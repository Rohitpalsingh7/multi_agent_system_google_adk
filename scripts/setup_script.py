import os
import logging
from pathlib import Path

from dotenv import load_dotenv, find_dotenv
from google.cloud import bigquery
from google.api_core.exceptions import NotFound, GoogleAPICallError

# --- CONFIGURE LOGGING ---
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- LOAD ENV VARIABLES ---
env_path = Path(__file__).parent.parent / "creative_analytics" / "creative_analytics_agents" / ".env"
load_dotenv(dotenv_path=env_path)

# --- INITIALIZATION OF VARIABLES ---
try:
    # Google Cloud settings
    PROJECT_ID = os.environ["GOOGLE_CLOUD_PROJECT_ID"]
    REGION = os.environ["GOOGLE_CLOUD_LOCATION"]

    # BigQuery variables
    BQ_DATASET_NAME = os.environ["BQ_DATASET_NAME"]
    BQ_TABLE_NAME = os.environ["BQ_TABLE_NAME"]
    BQ_MODEL_NAME = os.environ["BQ_MODEL_NAME"]

    # Derived BQ table name for training data
    BQ_TRAINING_TABLE_NAME = f"{BQ_TABLE_NAME}_training"

    # Source data file settings
    DATA_DIR = Path(__file__).parent.parent / "data"
    CSV_FILENAME = "creative_tags_performance_data.csv"
    DATA_FILEPATH = DATA_DIR / CSV_FILENAME

except KeyError as e:
    logging.error(f"Missing required environment variable in .env file: {e}")
    exit(1)

# -- BIGQUERY TABLE SCHEMA ---
TABLE_SCHEMA = [
    bigquery.SchemaField("media_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("animal", "BOOLEAN"),
    bigquery.SchemaField("human", "BOOLEAN"),
    bigquery.SchemaField("logo", "BOOLEAN"),
    bigquery.SchemaField("product", "BOOLEAN"),
    bigquery.SchemaField("cta", "BOOLEAN"),
    bigquery.SchemaField("video_views", "INTEGER"),
]


def execute_bq_query(client: bigquery.Client, query: str) -> None:
    """Executes a BigQuery query and waits for it to complete."""
    job = client.query(query)
    try:
        job.result()
    except GoogleAPICallError as e:
        logging.error(f"BigQuery job failed: {e.errors}")
        raise


def load_data_to_bq(client: bigquery.Client) -> None:
    """
    Ensures dataset exists and loads CSV data into the BigQuery table.
    """
    logging.info("Starting data loading process...")

    dataset_id = f"{PROJECT_ID}.{BQ_DATASET_NAME}"
    table_id = f"{dataset_id}.{BQ_TABLE_NAME}"

    try:
        client.get_dataset(dataset_id)
        logging.info(f"Dataset '{dataset_id}' already exists...")
    except NotFound:
        logging.info(f"Dataset '{dataset_id}' not found, creating it...")
        dataset = bigquery.Dataset(dataset_id)
        dataset.location = REGION
        client.create_dataset(dataset, timeout=30)
        logging.info("Dataset created successfully...")

    try:
        client.get_table(table_id)
        logging.info(f"Table '{table_id}' already exists — skipping load...")
        return
    except NotFound:
        logging.info(f"Table '{table_id}' does NOT exist — creating & loading...")

    if not DATA_FILEPATH.exists():
        raise FileNotFoundError(f"Data file not found at: {DATA_FILEPATH}")

    logging.info(f"Loading data to BigQuery table '{table_id}'...")
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1, schema=TABLE_SCHEMA,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    with open(DATA_FILEPATH, "rb") as source_file:
        load_job = client.load_table_from_file(source_file, table_id, job_config=job_config)
    load_job.result()
    logging.info(f"Loaded {load_job.output_rows} rows into table...")


def create_training_table(client: bigquery.Client) -> None:
    """Creates a new table with a binary label based on the median of log-transformed views."""
    logging.info("Creating the training dataset in BigQuery...")

    query = f"""
    CREATE OR REPLACE TABLE `{BQ_DATASET_NAME}.{BQ_TRAINING_TABLE_NAME}` AS
    WITH
      SourceData AS (
        SELECT *, LOG(SAFE_CAST(video_views AS FLOAT64) + 1) AS log_video_views
        FROM `{BQ_DATASET_NAME}.{BQ_TABLE_NAME}`
      ),
      Thresholds AS (
        SELECT APPROX_QUANTILES(log_video_views, 2)[OFFSET(1)] AS median_log_views
        FROM SourceData
      )
    SELECT
      SourceData.*,
      IF(SourceData.log_video_views > Thresholds.median_log_views, 1, 0) AS is_high_performing
    FROM SourceData, Thresholds;
    """

    execute_bq_query(client, query)
    logging.info("Training dataset created successfully in BigQuery...")


def train_model(client: bigquery.Client) -> None:
    """Trains a BigQuery model to predict the 'is_high_performing' label."""
    logging.info("Training BigQueryML Logistic Regression model...")

    query = f"""
    CREATE OR REPLACE MODEL `{BQ_DATASET_NAME}.{BQ_MODEL_NAME}`
    OPTIONS(model_type='LOGISTIC_REG', input_label_cols=['is_high_performing']) AS
    SELECT
      animal,
      human,
      logo,
      product,
      cta,
      is_high_performing
    FROM
      `{BQ_DATASET_NAME}.{BQ_TRAINING_TABLE_NAME}`;
    """

    execute_bq_query(client, query)
    logging.info("BigQueryML Logistic Regression model successfully trained...")


def main():
    """Main function to orchestrate the entire setup process."""
    logging.info("=== Starting Quickstart Setup (Data + BigQueryML Model) ===")

    try:
        bq_client = bigquery.Client(project=PROJECT_ID)

        # Step 1: Load the dataset to BigQuery
        load_data_to_bq(bq_client)

        # Step 2: Create the training table in BQ
        create_training_table(bq_client)

        # Step 3: Train the BigQuery logistic regression model
        train_model(bq_client)

        logging.info("Quickstart setup completed successfully!")

    except Exception as e:
        logging.error(f"An error occurred during setup: {e}", exc_info=True)
        exit(1)


if __name__ == "__main__":
    main()
