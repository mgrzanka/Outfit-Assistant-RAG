import json
import os
import random
from pathlib import Path
from typing import Dict, List

import pandas as pd
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()


class TestDatasetGenerator:
    def __init__(
        self,
        deployment_name: str = "gpt-4o",
        products_file: str = "../../data/products_raw.csv",
    ):
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_API_KEY"),
            api_version=os.getenv("AZURE_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_API_BASE"),
        )
        self.deployment_name = deployment_name
        self.products_df = pd.read_csv(products_file)

    def _get_product_context(self, row) -> str:
        materials = (
            eval(row["materials"])
            if isinstance(row["materials"], str)
            else row["materials"]
        )
        material_str = ", ".join([f"{m['name']} {m['percentage']}%" for m in materials])

        price_info = (
            eval(row["price"]) if isinstance(row["price"], str) else row["price"]
        )
        price_str = f"{row['price_pln']:.2f} PLN"

        sizes = eval(row["sizes"]) if isinstance(row["sizes"], str) else row["sizes"]
        sizes_str = ", ".join(sizes)

        context = f"{row['name']} - {row['description']} Color: {row['color']}. Construction: {row['construction']}. Materials: {material_str}. Price: {price_str}. Available sizes: {sizes_str}. Gender: {row['sex']}. Image URL: {row['image_url']}."

        return context

    def _sample_products(self, n: int = 4) -> List[str]:
        sampled = self.products_df.sample(n=min(n, len(self.products_df)))
        contexts = [self._get_product_context(row) for _, row in sampled.iterrows()]
        return contexts

    def generate_test_cases(self, num_cases: int = 20) -> List[Dict]:
        test_cases = []

        print(f"Generating {num_cases} test cases.")

        for i in range(num_cases):
            contexts = self._sample_products(n=random.randint(3, 5))
            contexts_str = "\n\n".join(
                [f"Product {j+1}: {ctx}" for j, ctx in enumerate(contexts)]
            )

            prompt = f"""You are creating a test case for an outfit assistant chatbot.

Here are REAL products from the database:
{contexts_str}

Based on these actual products, create:
1. A realistic user question that would lead to retrieving these products
2. An ideal ground_truth answer that presents these products as a friendly clothing store assistant would

The question should be natural and diverse. Cover scenarios like:
- Casual outfit recommendations
- Formal/business attire
- Seasonal clothing
- Specific events (weddings, parties, dates)
- Color coordination
- Style preferences
- Budget considerations
- Specific item searches

The ground_truth answer should:
- Be conversational and friendly (like a helpful store assistant)
- Reference the actual products provided with their key details
- Include product names in **bold** and mention prices
- Show product images using HTML format: <img src="URL" width="200" alt="Product Name">
- For outfits, explain how items work together
- Use natural paragraphs with varied structure
- Highlight relevant features (material, color, style, price)

Return ONLY a JSON object with this structure:
{{
  "question": "user question here",
  "ground_truth": "friendly conversational response with product recommendations and HTML images"
}}

Make each ground_truth answer unique in structure and tone while being helpful and specific."""

            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that generates high-quality test data.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.9,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            parsed = json.loads(content)

            test_cases.append(
                {
                    "question": parsed["question"],
                    "ground_truth": parsed["ground_truth"],
                    "contexts": contexts,
                }
            )

            print(f"  [{i+1}/{num_cases}] Generated test case")

        return test_cases

    def save_dataset(self, test_cases: List[Dict], output_path: str):
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(test_cases, f, indent=2, ensure_ascii=False)

        print(f"Saved {len(test_cases)} test cases to {output_path}")


def main():
    generator = TestDatasetGenerator()

    test_cases = generator.generate_test_cases(num_cases=100)

    output_path = "tests/data/test_dataset.json"
    generator.save_dataset(test_cases, output_path)

    print(f"\nGenerated {len(test_cases)} test cases")


if __name__ == "__main__":
    main()
