from pydantic import Field
from pydantic_settings import BaseSettings
from pathlib import Path


class AppSettings(BaseSettings):
    """
    Centralized application settings loaded from environment variables.
    This ensures early failure and strict validation.
    """

    # ---- Google Cloud Variables ----
    GOOGLE_CLOUD_PROJECT_ID: str = Field(..., description="Google Cloud project ID")
    GOOGLE_CLOUD_LOCATION: str = Field(..., description="GCP region, e.g. us-central1")

    # ---- BigQuery Parameters ----
    BQ_DATASET_NAME: str = Field(..., description="BigQuery dataset name")
    BQ_TABLE_NAME: str = Field(..., description="BigQuery main table name")
    BQ_MODEL_NAME: str = Field(..., description="BigQuery ML model name")

    # ---- Dataset Config JSON File ----
    DATASET_CONFIG_FILE: str = Field(..., description="Path to dataset config JSON file")

    # ---- Vertex AI flag ----
    GOOGLE_GENAI_USE_VERTEXAI: int = Field(..., description="Enable vertex ai")

    # ---- Models for agents ----
    ROOT_AGENT_MODEL: str = Field(..., description="Model for the root agent")
    STATS_AGENT_MODEL: str = Field(..., description="Model for the stat agent")
    PREDICTOR_AGENT_MODEL: str = Field(..., description="Model for predictor agent")

    class Config:
        env_file = Path(__file__).parent.parent / ".env"
        env_file_encoding = "utf-8"


# Create a global instance that will be imported everywhere
settings = AppSettings()
