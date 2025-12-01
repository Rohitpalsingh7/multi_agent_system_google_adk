import logging

import vertexai
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.agents.callback_context import CallbackContext

# CRITICAL: This validates the entire environment on startup.
from .utils.settings import settings

from .prompts import get_orchestrator_instructions_template
from .sub_agents import performance_predictor_agent, statistical_analyst_agent
from .utils.database_context import init_database_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

vertexai.init(
    project=settings.GOOGLE_CLOUD_PROJECT_ID,
    location=settings.GOOGLE_CLOUD_LOCATION
)


def load_database_settings_in_context(callback_context: CallbackContext):
    """Load database settings into the callback context on first use."""
    if "database_settings" not in callback_context.state:
        callback_context.state["database_settings"] = _shared_context['database_settings']


def create_orchestrator_agent() -> LlmAgent:
    agent = LlmAgent(
        name="AdInsightsOrchestrator",
        model=Gemini(model=settings.ROOT_AGENT_MODEL),
        description="A top-level agent that delegates user questions about ad performance.",
        instruction=_full_instructions,
        before_agent_callback=load_database_settings_in_context,
        sub_agents=[statistical_analyst_agent, performance_predictor_agent]
    )
    return agent


# Database context
_shared_context = init_database_settings()

# Instructions for orchestrator
_instructions_template = get_orchestrator_instructions_template()
_full_instructions = (
    _instructions_template + "\n" + _shared_context["database_definitions_prompt"]
)

print(_shared_context)

# Define the root agent
root_agent = create_orchestrator_agent()
