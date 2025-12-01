import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Literal, Tuple

import pandas as pd
from google.api_core.exceptions import GoogleAPICallError, NotFound
from google.cloud import bigquery
from pydantic import BaseModel, Field, ValidationError

from .settings import settings

logger = logging.getLogger(__name__)


class DatasetConfig(BaseModel):
    """Schema for a single data source entry in the JSON config."""
    type: Literal["bigquery"] = Field(..., description="Must be 'bigquery'")
    name: str = Field(..., description="The BigQuery Dataset ID")
    tables: List[str] = Field(..., description="List of table names in the dataset")
    description: str = Field(..., description="A description for the LLM")


class RootConfig(BaseModel):
    """Root structure of the JSON configuration file."""
    datasets: List[DatasetConfig]


def _load_and_validate_dataset_config(config_path: Path) -> RootConfig:
    """Loads and validates the dataset configuration file."""
    if not config_path.is_file():
        raise FileNotFoundError(f"Dataset config file not found at: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return RootConfig.model_validate(data)


def _format_schema_for_prompt(
    project_id: str,
    dataset_id: str,
    table_name: str,
    schema: List[Tuple[str, str]],
    sample_df: pd.DataFrame
) -> str:
    """Formats schema and sample rows into a single, clean text block for the LLM."""
    full_table_id = f"`{project_id}.{dataset_id}.{table_name}`"
    schema_str = ", ".join(f"{col} ({dtype})" for col, dtype in schema)

    samples_str = "This table is empty."
    if not sample_df.empty:
        samples_str = sample_df.to_string(index=False)

    return (
        f"Table {full_table_id}:\n"
        f"  - Schema: {schema_str}\n"
        f"  - Sample Rows:\n{samples_str}"
    )


def _get_table_details(
    client: bigquery.Client,
    project_id: str,
    dataset_id: str,
    table_name: str
) -> Dict[str, Any]:
    """
    Fetch schema and sample rows for a single BigQuery table.
    """
    full_table_id = f"{project_id}.{dataset_id}.{table_name}"

    try:
        table_obj = client.get_table(full_table_id)
        schema = [(col.name, col.field_type) for col in table_obj.schema]

        query = f"SELECT * FROM `{full_table_id}` LIMIT 3"
        sample_df = client.query(query).to_dataframe()
        formatted_schema = _format_schema_for_prompt(
            project_id, dataset_id, table_name, schema, sample_df
        )

        return {
            "error": None,
            "schema_list": schema,
            "schema_prompt": formatted_schema
        }

    except (NotFound, GoogleAPICallError) as e:
        logger.warning(f"Could not inspect table '{full_table_id}'. Error: {e}")
        formatted_schema = f"Table `{full_table_id}` could not be inspected."
        return {
            "error": str(e),
            "schema_list": [],
            "schema_prompt": formatted_schema
        }


def _build_dataset_definitions_prompt(db_settings: Dict[str, Dict[str, Any]]) -> str:
    """Builds the complete <DATASETS> block for the LLM prompt."""
    prompt_parts = ["<DATASETS>"]
    for dataset_name, dataset_info in db_settings.items():
        prompt_parts.append("<DATA_SOURCE>")
        prompt_parts.append(f"<NAME>{dataset_name}</NAME>")
        prompt_parts.append(f"<DESCRIPTION>{dataset_info['description']}</DESCRIPTION>")
        prompt_parts.append("<SCHEMAS>")
        for table_name, table_info in dataset_info.get("tables", {}).items():
            if "schema_prompt" in table_info:
                prompt_parts.append(table_info["schema_prompt"])
        prompt_parts.append("</SCHEMAS>")
        prompt_parts.append("</DATA_SOURCE>")
    prompt_parts.append("</DATASETS>")

    return "\n".join(prompt_parts)


@lru_cache(maxsize=1)
def init_database_settings() -> Dict[str, Any]:
    """Initializes the database settings for the configured datasets"""
    try:
        project_id = settings.GOOGLE_CLOUD_PROJECT_ID
        config_path_str = Path(__file__).parent.parent / "config" / settings.DATASET_CONFIG_FILE

        dataset_config = _load_and_validate_dataset_config(Path(config_path_str))

        client = bigquery.Client(project=project_id)

        db_settings: Dict[str, Dict[str, Any]] = {}
        for dataset in dataset_config.datasets:
            if dataset.type == "bigquery":
                table_details = {
                    name: _get_table_details(client, project_id, dataset.name, name)
                    for name in dataset.tables
                }
                db_settings[dataset.name] = {
                    "project_id": project_id,
                    "dataset_id": dataset.name,
                    "description": dataset.description,
                    "tables": table_details,
                }

        db_definitions_prompt = _build_dataset_definitions_prompt(db_settings)
        logger.info("Shared agent context initialization complete...")

        return {
            "database_settings": db_settings,
            "database_definitions_prompt": db_definitions_prompt,
        }

    except (ValueError, FileNotFoundError, json.JSONDecodeError, ValidationError) as e:
        logger.critical(f"Configuration failed. Application cannot start. Reason: {e}...")
        raise
    except Exception as e:
        logger.critical(f"An unexpected error occurred during initialization. Reason: {e}...")
        raise
