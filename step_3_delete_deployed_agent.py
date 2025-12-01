import os
import json
from pathlib import Path
import vertexai
from vertexai import agent_engines
from dotenv import load_dotenv

# ----------------------------
# Paths and env
# ----------------------------
ROOT_DIR = Path(__file__).parent
PROJECT_DIR = ROOT_DIR / "creative_analytics" / "creative_analytics_agents"
ENV_FILE = PROJECT_DIR / ".env"
DEPLOYED_JSON = ROOT_DIR / "deployed_agent.json"

if not ENV_FILE.exists():
    raise FileNotFoundError(f".env file not found at {ENV_FILE}")

load_dotenv(dotenv_path=ENV_FILE)

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")

if not PROJECT_ID or not LOCATION:
    raise ValueError("Missing GOOGLE_CLOUD_PROJECT_ID or GOOGLE_CLOUD_LOCATION in .env")

if not DEPLOYED_JSON.exists():
    raise FileNotFoundError(f"Deployed agent JSON not found at {DEPLOYED_JSON}")

# Read deployed agent resource ID
with open(DEPLOYED_JSON, "r", encoding="utf-8") as f:
    data = json.load(f)
AGENT_RESOURCE_ID = data.get("resource_id")

if not AGENT_RESOURCE_ID:
    raise ValueError("Resource ID not found in deployed_agent.json")


def main():
    vertexai.init(project=PROJECT_ID, location=LOCATION)

    # Delete agent engine
    agent = agent_engines.get(AGENT_RESOURCE_ID)
    agent_engines.delete(resource_name=agent.resource_name, force=True)

    print(f"Deleted agent engine: {AGENT_RESOURCE_ID}")


if __name__ == "__main__":
    main()
