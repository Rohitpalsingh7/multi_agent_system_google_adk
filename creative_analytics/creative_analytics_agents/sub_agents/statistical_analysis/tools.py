import logging
from typing import Dict, Any

from google import genai
from google.adk.tools import ToolContext
from google.adk.tools.bigquery import BigQueryToolset

from ...utils.settings import settings

logger = logging.getLogger(__name__)


TOOL_PROMPT = """
    You are an expert-level BigQuery data analyst. Your sole purpose is to write a single, highly-optimized, and syntactically correct Google Standard SQL query to answer the user's analytical question. You must use the provided schema.

    **SQL Generation Guidelines:**

    -   **Table Referencing:** You have access to one table: {FULL_TABLE_ID}. ALWAYS use this full, backticked name in your queries.
    -   **Column Usage:** Use ONLY the column names mentioned in the provided Table Schema below. Do not invent or assume any other columns exist.
    -   **Aggregations:** To calculate "lift" or "boost," you MUST compare the `AVG(video_views)` of a specific segment against the overall `AVG(video_views)` for the entire table. Use Common Table Expressions (CTEs) to make this efficient.
    -   **Efficiency:** Write a single query to answer the entire question. If asked to compare multiple tags, use techniques like `UNION ALL` or conditional aggregation in a `GROUP BY` to get all results in one database call.
    -   **Output Format:** Your final output MUST be a raw SQL string only. Do not include any explanations, comments, or markdown formatting like ```sql.

    ---
    **Schema:**

    The database structure is defined by the following table schema. You MUST use this to write your queries.
    {SCHEMA}

    ---
    **Example Tasks:**

    **1. Comparative Analysis Question:**
    "Compare the performance lift from ads with 'animals' vs. ads with 'humans'."

    **Correct SQL Query:**
    ```sql
    WITH OverallAvg AS (SELECT AVG(video_views) as avg_all FROM {FULL_TABLE_ID})
    SELECT 'animal' as tag, (AVG(t.video_views) - o.avg_all) / o.avg_all * 100 as percentage_lift
    FROM {FULL_TABLE_ID} t, OverallAvg o WHERE t.animal = TRUE GROUP BY o.avg_all
    UNION ALL
    SELECT 'human' as tag, (AVG(t.video_views) - o.avg_all) / o.avg_all * 100 as percentage_lift
    FROM {FULL_TABLE_ID} t, OverallAvg o WHERE t.human = TRUE GROUP BY o.avg_all
    ```

    **2. Comprehensive Analysis Question:**
    "What creative elements are working best overall?"

    **Correct SQL Query:**
    ```sql
    WITH OverallAvg AS (SELECT AVG(video_views) as avg_all FROM {FULL_TABLE_ID})
    SELECT tag_name, (AVG(t.video_views) - o.avg_all) / o.avg_all * 100 as percentage_lift
    FROM {FULL_TABLE_ID} t, OverallAvg o
    CROSS JOIN UNNEST(['animal', 'human', 'logo', 'product', 'cta']) as tag_name
    WHERE
      (tag_name = 'animal' AND t.animal = TRUE) OR
      (tag_name = 'human' AND t.human = TRUE) OR
      (tag_name = 'logo' AND t.logo = TRUE) OR
      (tag_name = 'product' AND t.product = TRUE) OR
      (tag_name = 'cta' AND t.cta = TRUE)
    GROUP BY tag_name, o.avg_all
    ORDER BY percentage_lift DESC
    ```
    ---

    **User's Natural Language Question:**
    {QUESTION}

    **Your Generated SQL Query:**
    """


def generate_sql_for_analysis(question: str, tool_context: ToolContext) -> Dict[str, Any]:
    """
    Generates a Google Standard SQL query from a natural language question.

    This tool takes a user's question about ad performance and uses a powerful LLM
    to construct an optimized BigQuery SQL query based on the available schema.

    Args:
    question: The user's natural language question.
    tool_context: The context containing shared data like database schemas.

    Returns:
        Dict[str, Any]: A dictionary representing the outcome.
        - On success: `{"status": "success", "sql_query": "SELECT ..."}`
        - On failure: `{"status": "error", "error_message": "Details of the error."}`
    """

    try:
        database_settings = tool_context.state["database_settings"]
        project_id = settings.GOOGLE_CLOUD_PROJECT_ID
        dataset_name = settings.BQ_DATASET_NAME
        table_name = settings.BQ_TABLE_NAME

        schema_prompt = database_settings[dataset_name]["tables"][table_name]["schema_prompt"]
        full_table_id = f"`{project_id}.{dataset_name}.{table_name}`"
    except (KeyError, TypeError) as e:
        error_msg = f"Could not find required schema info to generate SQL. Error: {e}"
        logger.error(error_msg)
        return {"status": "error", "error_message": error_msg}

    prompt = TOOL_PROMPT.format(
        FULL_TABLE_ID=full_table_id,
        SCHEMA=schema_prompt,
        QUESTION=question
    )

    try:
        client = genai.Client(vertexai=True)
        response = client.models.generate_content(
            model=settings.STATS_AGENT_MODEL,
            contents=prompt,
        )

        sql_query = response.text.strip().replace("```sql", "").replace("```", "")
        return {"status": "success", "sql_query": sql_query}
    except Exception as e:
        error_msg = f"LLM failed to generate SQL. Error: {e}"
        logger.error(error_msg, exc_info=True)
        return {"status": "error", "error_message": error_msg}


# BigQuery built in tool
bq_executor_tool = BigQueryToolset(
    tool_filter=['execute_sql'],
)
