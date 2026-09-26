import asyncio
import json
from typing import Any, Dict, List

from google.adk.agents import BaseAgent
from google.adk.events import Event
from pydantic import BaseModel

from src.services.chat.agents.outfit_planner_agent import OutfitSearchPlan
from src.services.chat.agents.researcher_agent import create_researcher_agent


class ResearchOrchestrator(BaseAgent):
    """Orchestrator that takes an OutfitSearchPlan, spawns ResearcherAgents in parallel and aggregates the results."""

    input_schema: type[BaseModel] = OutfitSearchPlan
    output_key: str = "research_findings"

    def __init__(self, **kwargs):
        super().__init__(
            name="research_orchestrator",
            description="Executes parallel product searches based on an outfit plan",
            **kwargs,
        )

    async def _run_sub_agent(self, agent, context):
        """Helper to run a sub-agent to completion and return its last yielded result."""
        final_result = None
        async for result in agent.run_async(context):
            final_result = result
        return final_result

    async def _run_async_impl(self, context, **kwargs) -> Any:
        """
        Execute the research workflow.

        Args:
            context: The agent context.
            input_override: The input from the previous agent (expected OutfitSearchPlan).

        Yields:
             A dictionary containing user intent, occasion, and a list of search results
             for the summarization agent.
        """
        plan = OutfitSearchPlan.model_validate(
            context.session.state.get("outfit_search_plan")
        )

        tasks = []
        for i, request in enumerate(plan.search_requests):
            agent = create_researcher_agent(
                item_description=request.item_description,
                item_type=request.item_type,
                index=i,
            )
            tasks.append(self._run_sub_agent(agent, context))

        results = await asyncio.gather(*tasks)

        final_output = {
            "user_intent": plan.user_intent,
            "occasion": plan.occasion,
            "search_results": results,
        }

        context.session.state[self.output_key] = final_output

        json_output = json.dumps(final_output, indent=2, default=str)

        yield Event(author=self.name, content={"parts": [{"text": json_output}]})


def create_research_orchestrator():
    return ResearchOrchestrator()
