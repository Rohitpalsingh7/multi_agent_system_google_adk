import logging
from typing import Any, Dict, Optional

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools import BaseTool, ToolContext
from google.genai.types import HttpRetryOptions

from .tools import generate_sql_for_analysis, bq_executor_tool
from .prompts import get_instructions_statistical_analyst_agent
from ...utils.database_context import init_database_settings
from ...utils.settings import settings

logger = logging.getLogger(__name__)


def setup_before_agent_call(callback_context: CallbackContext):
    """Ensures the shared database settings are loaded into the agent's state."""
    if "database_settings" not in callback_context.state:
        shared_context = init_database_settings()
        callback_context.state["database_settings"] = shared_context['database_settings']


def store_results_in_context(
    tool: BaseTool,
    args: Dict[str, Any],
    tool_context: ToolContext,
    tool_response: Dict,
) -> Optional[Dict]:
    """Stores intermediate tool output into the agent's state."""
    if tool.name == 'execute_sql':
        if tool_response.get("status") == "SUCCESS":
            tool_context.state["last_query_result"] = tool_response.get("rows")
    elif tool.name == 'generate_sql_for_analysis':
        if tool_response.get("status") == "SUCCESS":
            tool_context.state["last_generated_sql"] = tool_response.get("sql_query")
    return None


retry_config = HttpRetryOptions(
    attempts=3,
    initial_delay=1,
    exp_base=5,
    http_status_codes=[429, 500, 503, 504]
)


statistical_analyst_agent = LlmAgent(
    name="StatisticalAnalystAgent",
    model=Gemini(model=settings.STATS_AGENT_MODEL, retry_options=retry_config),
    description="A specialist agent that analyzes historical ad data by generating and executing SQL.",
    instruction=get_instructions_statistical_analyst_agent(),
    tools=[generate_sql_for_analysis, bq_executor_tool],
    before_agent_callback=setup_before_agent_call,
    after_tool_callback=store_results_in_context,
)
