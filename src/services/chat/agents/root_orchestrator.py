from google.adk.agents.sequential_agent import SequentialAgent

from src.services.chat.agents.outfit_planner_agent import create_outfit_planner_agent
from src.services.chat.agents.research_orchestrator import create_research_orchestrator
from src.services.chat.agents.summarization_agent import create_summarization_agent


def create_root_orchestrator():
    """Main workflow orchestrator using SequentialAgent."""
    return SequentialAgent(
        name="outfit_search_workflow",
        description="Orchestrates outfit search from query to recommendation",
        sub_agents=[
            create_outfit_planner_agent(),
            create_research_orchestrator(),
            create_summarization_agent(),
        ],
    )
