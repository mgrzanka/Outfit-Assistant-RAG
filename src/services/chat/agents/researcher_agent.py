from typing import Optional

from google.adk.agents.base_agent import BaseAgent
from google.adk.agents.llm_agent import LlmAgent
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from src.models.filter_models import Filters
from src.services.chat.agents import AZURE_AI_FOUNDRY_MODEL, products_service


class SearchCriteria(BaseModel):
    """Output from criteria extractor agent."""

    model_config = ConfigDict(extra="forbid")

    search_query: str = Field(
        description="Natural language query for semantic search (e.g., 'white party dress')"
    )
    filters: Filters = Field()


class ResearcherAgent(BaseAgent):
    """
    Custom agent that combines search criteria generation (natural language query and filters) with product search.

    Workflow:
    1. Uses internal LlmAgent to search query from item description
    2  Calls products_service.product_search()
    3. Returns structured search results
    """

    item_description: str
    item_type: str
    output_key: str = "search_results"

    _criteria_extractor: Optional[LlmAgent] = PrivateAttr(default=None)

    def __init__(self, item_description: str, item_type: str, **kwargs):
        super().__init__(
            name="researcher",
            description="Generates search query and searches for clothing items",
            item_description=item_description,
            item_type=item_type,
            **kwargs,
        )

        self._criteria_extractor = LlmAgent(
            model=AZURE_AI_FOUNDRY_MODEL,
            name="criteria_extractor",
            description="Analyzes item descriptions and extracts structured search filters",
            instruction="""You are a clothing search analyst.

You receive descriptions of **single clothing items** (e.g., "white party top", "formal men's shoes").

Your job:
1. Extract a natural language search query optimized for semantic search
2. Generate structured filters for product attributes (price, size, material, construction, sex, color)

Guidelines:
- Convert price terms to PLN filters:
  - "cheap" → price < 150 PLN
  - "affordable" → price < 200 PLN
  - "expensive" → price > 500 PLN
  - Non-PLN currencies: convert using approximate rates
  
- For materials:
  - Use 'exists' operator unless specific percentage mentioned
  - E.g., "cotton shirt" → materials: [{operator: "exists", key: "cotton"}]
  
- For sizes:
  - Extract all mentioned sizes: "M or L" → sizes: ["M", "L"]
  
- For construction (fabric type):
  - Only map if explicit fabric construction is mentioned (e.g., "knitted", "woven", "jersey")
  
- For sex/gender:
  - Extract if mentioned: "women's blouse" → sex: "Women"
  - Leave null if not specified

Examples:

Input: "cheap cotton t-shirt size M"
→ search_query: "cotton t-shirt size M"
  filters: {price: {operator: "lt", value: 150}, materials: [{operator: "exists", key: "cotton"}], sizes: ["M"]}

Input: "formal men's shoes under €50"
→ search_query: "formal men's shoes"
  filters: {price: {operator: "lt", value: 215}, sex: "Men"}

Input: "white knitted party top"
→ search_query: "white party top"
  filters: {color: "white", construction: "knitted"}
""",
            output_schema=SearchCriteria,
            output_key="search_criteria",
            disallow_transfer_to_parent=True,
            disallow_transfer_to_peers=True,
        )

    async def _run_sub_agent(self, agent, context):
        """Helper to run a sub-agent to completion and return its last yielded result."""
        final_result = None
        async for result in agent.run_async(context):
            final_result = result
        return final_result.actions.state_delta["search_criteria"]

    async def _run_async_impl(self, context, **kwargs):
        """
        Execute research and search workflow.

        Args:
            context: Agent execution context

        Yields:
            dict with search results and metadata
        """
        raw_criteria = await self._run_sub_agent(self._criteria_extractor, context)
        criteria = SearchCriteria.model_validate(raw_criteria, strict=False)

        search_results = products_service.product_search(
            query=criteria.search_query, filters=criteria.filters
        )

        top_matches = []
        for product in search_results.get("search_results", [])[:5]:
            top_matches.append(
                {
                    "name": product.get("name"),
                    "description": product.get("description"),
                    "color": product.get("color"),
                    "price": product.get("price_pln"),
                    "image_url": product.get("image_url"),
                }
            )

        yield {
            "item_type": self.item_type,
            "description": self.item_description,
            "message": search_results["message"],
            "products": top_matches,
        }


def create_researcher_agent(item_description: str, item_type: str, index: int):
    """
    Factory for a researcher agent for a specific item.

    Args:
        item_description: What to search for (e.g., "white party top")
        item_type: Type of clothing (e.g., "top", "bottom")
        index: Unique index for output_key

    Returns:
        ResearcherAgent configured for this specific search
    """
    return ResearcherAgent(
        item_description=item_description,
        item_type=item_type,
        output_key=f"search_results_{index}",
    )
