import logging

from google.adk.agents import LlmAgent
from google.adk.tools import AgentTool
from google.adk.models.google_llm import Gemini
from google.adk.agents.callback_context import CallbackContext
from google.genai.types import HttpRetryOptions

from .tools import (
    generate_prediction_sql,
    validate_features_json
)
from ..statistical_analysis.tools import bq_executor_tool

from .prompts import (
    get_instructions_features_extractor_agent,
    get_instructions_sql_prediction_agent,
    get_instructions_performance_predictor_agent
)
from ...utils.database_context import init_database_settings
from ...utils.settings import settings

logger = logging.getLogger(__name__)


def setup_before_agent_call(callback_context: CallbackContext):
    """Ensures the shared database settings are loaded into the agent's state."""
    if "database_settings" not in callback_context.state:
        shared_context = init_database_settings()
        callback_context.state["database_settings"] = shared_context['database_settings']


retry_config = HttpRetryOptions(
    attempts=3,
    initial_delay=1,
    exp_base=5,
    http_status_codes=[429, 500, 503, 504]
)

features_extraction_agent = LlmAgent(
    name="FeaturesExtractionAgent",
    model=Gemini(model=settings.PREDICTOR_AGENT_MODEL, retry_options=retry_config),
    description="An agent tool to extract visual features from the input image or video",
    instruction=get_instructions_features_extractor_agent(),
    tools=[validate_features_json],
    output_key="features"
)

sql_prediction_agent = LlmAgent(
    name="SQLPredictionAgent",
    model=Gemini(model=settings.PREDICTOR_AGENT_MODEL, retry_options=retry_config),
    description="A agent tool to get prediction of visual features via BigQuery ML model",
    instruction=get_instructions_sql_prediction_agent(),
    tools=[generate_prediction_sql, bq_executor_tool],
    output_key='predictions'
)

performance_predictor_agent = LlmAgent(
    name="PerformancePredictorCoordinator",
    model=Gemini(model=settings.PREDICTOR_AGENT_MODEL, retry_options=retry_config),
    description="Orchestrates a workflow to predict creative performance.",
    instruction=get_instructions_performance_predictor_agent(),
    tools=[
        AgentTool(features_extraction_agent),
        AgentTool(sql_prediction_agent)
    ],
    before_agent_callback=setup_before_agent_call,
)
