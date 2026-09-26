from typing import Any

from google.adk.agents.llm_agent import LlmAgent
from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.services.chat.agents import AZURE_AI_FOUNDRY_MODEL


class ClothingSearchRequest(BaseModel):
    """A single clothing item search request."""

    model_config = ConfigDict(extra="forbid")

    item_description: str = Field(
        description="Natural language description of the item to search for (e.g., 'white party top', 'black formal shoes')"
    )
    item_type: str = Field(
        description="Type of clothing item (e.g., 'top', 'bottom', 'shoes', 'outerwear', 'accessory')"
    )


class OutfitSearchPlan(BaseModel):
    """Plan for searching clothing items to compose an outfit or fulfill a request."""

    model_config = ConfigDict(extra="forbid")

    search_requests: list[ClothingSearchRequest] = Field(
        description="List of individual clothing items to search for"
    )
    occasion: str | None = Field(
        description="Occasion or context for the outfit (e.g., 'party', 'formal', 'casual')",
    )
    user_intent: str = Field(description="Summary of what the user is looking for")

    @model_validator(mode="before")
    @classmethod
    def set_null_for_missing_keys(cls, data: Any) -> Any:
        if isinstance(data, dict):
            optional_fields = ["occasion"]
            for field in optional_fields:
                if field not in data:
                    data[field] = None
        return data


def create_outfit_planner_agent():
    return LlmAgent(
        model=AZURE_AI_FOUNDRY_MODEL,
        name="outfit_planner",
        description="Analyzes user queries and creates search plans for clothing items.",
        instruction="""You are an outfit planning assistant for a clothing store.

Analyze the user's request and determine what clothing items they need.

For outfit requests:
- Typical outfit = top + bottom + shoes
- Formal outfit = top + bottom + shoes + outerwear
- Party outfit = top + bottom + shoes
- Casual outfit = top + bottom

For single-item requests
- Create one search request

Preserve user preferences (color, style, price) across all items.
If the user specifies a gender (e.g., "men's", "women's"), include it in the description of every item.
Return ocassion only if it can be inferred from user's request.

Examples:

User: "white outfit for a party"
→ search_requests: [
    {item_description: "white party top", item_type: "top"},
    {item_description: "white party pants or skirt", item_type: "bottom"},
    {item_description: "white party shoes", item_type: "shoes"}
  ]
  ocassion: "party"
  user_intent: "Complete white party outfit"

User: "cheap cotton t-shirt size M"
→ search_requests: [
    {item_description: "cheap cotton t-shirt size M", item_type: "top"}
  ]
  user_intent: "Affordable cotton t-shirt"

User: "formal interview outfit for women"
→ search_requests: [
    {item_description: "formal women's blouse or shirt", item_type: "top"},
    {item_description: "formal women's pants or skirt", item_type: "bottom"},
    {item_description: "formal women's shoes", item_type: "shoes"},
    {item_description: "formal women's blazer", item_type: "outerwear"}
  ]
  occasion: "job interview"
  user_intent: "Professional formal outfit for women"
""",
        output_schema=OutfitSearchPlan,
        output_key="outfit_search_plan",
        disallow_transfer_to_parent=True,
        disallow_transfer_to_peers=True,
    )
