import pandas as pd
import numpy as np
import uuid
from pathlib import Path
import logging

# --- CONFIGURATION ---
NUM_ROWS = 500
OUTPUT_DIR = Path(__file__).parent.parent / "data"
OUTPUT_FILENAME = "creative_tags_performance_data.csv"

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def generate_mock_data() -> pd.DataFrame:
    """
    Generates a DataFrame with realistic, skewed, and correlated mock data.
    """
    logging.info(f"Generating {NUM_ROWS} rows of mock data...")

    boolean_cols = ["animal", "human", "logo", "product", "cta"]
    data = {
        "media_id": [str(uuid.uuid4()) for _ in range(NUM_ROWS)],
        "animal": np.random.choice([True, False], size=NUM_ROWS, p=[0.35, 0.65]),
        "human": np.random.choice([True, False], size=NUM_ROWS, p=[0.60, 0.40]),
        "logo": np.random.choice([True, False], size=NUM_ROWS, p=[0.80, 0.20]),
        "product": np.random.choice([True, False], size=NUM_ROWS, p=[0.55, 0.45]),
        "cta": np.random.choice([True, False], size=NUM_ROWS, p=[0.70, 0.30]),
    }
    df = pd.DataFrame(data)

    # Generate skewed video_views using a log-normal distribution
    base_views = np.random.lognormal(mean=8, sigma=2.0, size=NUM_ROWS)
    df["video_views"] = (100 + base_views).astype(int)

    # Introduce correlations by adjusting views based on tags
    animal_boost_multiplier = 1.8
    df.loc[df["animal"], "video_views"] = (df.loc[df["animal"], "video_views"] * animal_boost_multiplier).astype(int)

    cta_boost_multiplier = 1.3
    df.loc[df["cta"], "video_views"] = (df.loc[df["cta"], "video_views"] * cta_boost_multiplier).astype(int)

    no_logo_penalty_multiplier = 0.8
    df.loc[~df["logo"], "video_views"] = (df.loc[~df["logo"], "video_views"] * no_logo_penalty_multiplier).astype(int)

    # Convert boolean columns to 1s and 0s for the CSV output ***
    for col in boolean_cols:
        df[col] = df[col].astype(int)

    # Ensure the column order matches the desired BigQuery schema
    schema_order = [
        "media_id", "animal", "human", "logo",
        "product", "cta", "video_views"
    ]
    df = df[schema_order]
    logging.info("Mock data generation completed...")

    return df


def main():
    """Main function to generate data and save it to a CSV file."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / OUTPUT_FILENAME

    mock_data_df = generate_mock_data()

    mock_data_df.to_csv(output_path, index=False)
    logging.info(f"Successfully saved mock data to: {output_path}")


if __name__ == "__main__":
    main()
