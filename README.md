# Outfit Assistant — Multi-Agent RAG

**A conversational shopping assistant that composes complete outfits from a real product catalogue.**
Multi-agent orchestration (Google ADK) over hybrid vector search (Weaviate), evaluated with RAGAS.

> *"formal interview outfit for women"* → the system decomposes the request into top / bottom / shoes / blazer, searches each in parallel with its own semantic query **and** structured filters, then presents 1–2 coherent looks with images, prices and styling rationale.

---

## Architecture

```
user query
    │
    ▼
┌─────────────────────┐   SequentialAgent (root orchestrator)
│ 1. outfit_planner   │   LLM → OutfitSearchPlan (Pydantic)
│                     │   "white party outfit" → [top, bottom, shoes] + occasion + intent
└─────────────────────┘
    │
    ▼
┌─────────────────────┐   custom BaseAgent — spawns one researcher per item,
│ 2. research_        │   runs them concurrently via asyncio.gather
│    orchestrator     │
│   ┌───────────────┐ │
│   │ researcher ×N │ │   per item:  LLM → SearchCriteria = semantic query + Filters
│   └───────────────┘ │             → Weaviate hybrid search (α = 0.75)
└─────────────────────┘             → top-5 products
    │
    ▼
┌─────────────────────┐   LLM → natural-language recommendation,
│ 3. outfit_presenter │   inline product images, total price, styling tips
└─────────────────────┘
```

**Why this shape:** a single LLM call with one retrieval pass cannot build an *outfit* — it needs N independent retrievals whose results must stay mutually coherent. Planning and presentation are therefore separated from retrieval, and the N retrievals run in parallel rather than sequentially.

## What makes the retrieval work

**Structured filters, not just embeddings.** A second LLM converts each item description into a validated `Filters` object — price, sizes, gender, colour, fabric construction, and *material composition with percentages*. `ProductsService` translates it into Weaviate predicates:

```
"cheap cotton t-shirt size M"
  → query:   "cotton t-shirt size M"
  → filters: price < 150 PLN ∧ cotton_percentage > 0 ∧ sizes contains "M"
```

Everything the LLM may emit is constrained by Pydantic + `Literal` enums generated from the actual catalogue values (`unique_values.json`), with an `OTHER` fallback — so the model cannot invent a material or size that does not exist in the index.

**Hybrid search.** Weaviate `hybrid(alpha=0.75)` — 75% vector similarity, 25% BM25 keyword — so brand/product names still match exactly while intent still matches semantically.

**Graceful degradation.** Over-constrained filters return nothing; the service retries unfiltered and tells the presenter agent that it did so, so the answer stays honest about it rather than silently returning off-target items.

## Evaluation (RAGAS)

100 test cases synthesised by GPT-4o from sampled catalogue products (`generate_test_dataset.py`), scored on five metrics (`evaluate_rag.py`), with resumable generation so a crash mid-run doesn't waste tokens.

| Metric | Score |
|---|---|
| Answer relevancy | **0.95** |
| Context precision | **0.78** |
| Context recall | **0.72** |
| Answer correctness | 0.31 |
| Faithfulness | 0.02 ⚠️ |

⚠️ **Read the last two with care.** The harness scores answers against the *reference* products used to synthesise each question, not against what the pipeline actually retrieved. With 888 products, a valid answer frequently recommends a different-but-equally-suitable garment — which RAGAS counts as unfaithful. The correct fix is to log real retrieved contexts and re-score; the numbers above are kept as measured rather than quietly dropped.

## Data pipeline

`01-data-load-and-proccess` — scrapes ~864 H&M products (men + women) from the public listing API, normalises material composition into per-material percentage columns, converts GBP → PLN, and extracts the catalogue's unique attribute values.
`02-data-indexing` — builds the Weaviate `Products` collection (`text2vec-openai` via Azure), generates one RAG string per product, and indexes it.

## Run it

```bash
cp .env.example .env    # Azure OpenAI keys: chat + embeddings
docker compose up
```

- Streamlit chat UI → `localhost:8000`
- FastAPI `/chat` → `localhost:5000`

```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"userId": "u1", "q": "Suggest an outfit for the office"}'
```

> The Weaviate index must exist first — run notebook `02-data-indexing`.

Conversation state is persisted per user through ADK's `DatabaseSessionService`, so the API and the Streamlit panel share the same sessions.

## Layout

```
src/services/chat/agents/   planner · research orchestrator · researcher · presenter
src/services/storage/       Weaviate client + filter translation
src/models/                 Pydantic filter schema, catalogue-derived enums
notebooks/                  data acquisition → indexing
tests/scripts/              RAGAS dataset generation + evaluation
```

**Stack:** Python · Google ADK · LiteLLM (Azure GPT-4o) · Weaviate · FastAPI · Streamlit · Pydantic · RAGAS · Docker Compose
