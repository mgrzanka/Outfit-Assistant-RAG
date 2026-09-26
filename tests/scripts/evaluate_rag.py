import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, List

import pandas as pd
from datasets import Dataset
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from ragas import evaluate
from ragas.metrics import (
    answer_correctness,
    answer_relevancy,
    context_precision,
    context_recall,
    faithfulness,
)

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.services.chat.chat_service import ChatService

load_dotenv()


class RAGEvaluator:
    def __init__(self, test_dataset_path: str):
        self.test_dataset_path = test_dataset_path
        self.test_cases = self._load_test_dataset()

    def _load_test_dataset(self) -> List[Dict]:
        with open(self.test_dataset_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def generate_responses(self) -> List[Dict]:
        results = []
        progress_file = Path("tests/data/results/generation_progress.json")
        progress_file.parent.mkdir(parents=True, exist_ok=True)

        if progress_file.exists():
            with open(progress_file, "r", encoding="utf-8") as f:
                results = json.load(f)

        print(f"Generating responses for {len(self.test_cases)} test cases.")

        chat_service = ChatService()

        for i, test_case in enumerate(self.test_cases, 1):
            if i <= len(results):
                continue

            question = test_case["question"]

            try:
                user_id = f"test_user_{i}"

                response = asyncio.run(chat_service.perform_prompt(user_id, question))

                result_entry = {
                    "question": question,
                    "answer": response,
                    "ground_truth": test_case["ground_truth"],
                    "contexts": test_case["contexts"],
                }
                results.append(result_entry)

            except Exception as e:
                print(f"    Error: {e}")
                result_entry = {
                    "question": question,
                    "answer": f"Error: {str(e)}",
                    "ground_truth": test_case["ground_truth"],
                    "contexts": test_case["contexts"],
                }
                results.append(result_entry)

            with open(progress_file, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

            print(f"[{i}/{len(self.test_cases)}] Generated response for test case")

        return results

    def evaluate_with_ragas(self, results: List[Dict]) -> pd.DataFrame:
        """Evaluate results using Ragas metrics."""

        dataset_dict = {
            "question": [r["question"] for r in results],
            "answer": [r["answer"] for r in results],
            "contexts": [r["contexts"] for r in results],
            "ground_truth": [r["ground_truth"] for r in results],
        }

        dataset = Dataset.from_dict(dataset_dict)

        print("\nEvaluating with Ragas metrics.")

        azure_llm = AzureChatOpenAI(
            azure_endpoint=os.getenv("AZURE_API_BASE"),
            api_key=os.getenv("AZURE_API_KEY"),
            api_version=os.getenv("AZURE_API_VERSION"),
            deployment_name="gpt-4o",
            temperature=0,
        )

        azure_embeddings = AzureOpenAIEmbeddings(
            azure_endpoint=os.getenv("AZURE_API_BASE_EMB"),
            api_key=os.getenv("AZURE_API_KEY_EMB"),
            api_version=os.getenv("AZURE_API_VERSION_EMB"),
            deployment="text-embedding-ada-002",
        )

        metrics = [
            answer_relevancy,
            faithfulness,
            context_recall,
            context_precision,
            answer_correctness,
        ]

        evaluation_result = evaluate(
            dataset=dataset, metrics=metrics, llm=azure_llm, embeddings=azure_embeddings
        )

        return evaluation_result.to_pandas()

    def save_results(
        self, results: List[Dict], metrics_df: pd.DataFrame, output_dir: str
    ):
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        results_file = output_path / "evaluation_results.json"
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\nSaved results to {results_file}")

        metrics_file = output_path / "ragas_metrics.csv"
        metrics_df.to_csv(metrics_file, index=False)
        print(f"Saved metrics to {metrics_file}")

        print("EVALUATION SUMMARY")
        print(f"\nTotal test cases: {len(results)}\n")
        print("Average Scores:")
        for col in metrics_df.columns:
            if pd.api.types.is_numeric_dtype(metrics_df[col]):
                mean_score = metrics_df[col].mean()
                print(f"{col:.<30} {mean_score:.4f}")


def main():
    test_dataset_path = "tests/data/test_dataset.json"
    output_dir = "tests/data/results"

    if not Path(test_dataset_path).exists():
        print(f"Error: Test dataset not found at {test_dataset_path}")
        return

    evaluator = RAGEvaluator(test_dataset_path)
    results = evaluator.generate_responses()
    metrics_df = evaluator.evaluate_with_ragas(results)
    evaluator.save_results(results, metrics_df, output_dir)
    return


if __name__ == "__main__":
    main()
