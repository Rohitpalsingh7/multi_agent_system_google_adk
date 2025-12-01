import os
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv

import vertexai
from vertexai import agent_engines
from google.adk.sessions import VertexAiSessionService

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
USER_ID = "test_user_1"

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

# ----------------------------
# Async helper for agent query
# ----------------------------


async def query_agent(message: str):
    vertexai.init(project=PROJECT_ID, location=LOCATION)

    # Create session
    session_service = VertexAiSessionService(PROJECT_ID, LOCATION)
    session = await session_service.create_session(app_name=AGENT_RESOURCE_ID, user_id=USER_ID)

    # Load agent
    agent = agent_engines.get(AGENT_RESOURCE_ID)
    print(f"🔵 Sending message to agent: '{message}'\n")

    # Stream query
    async for event in agent.async_stream_query(
        message=message,
        user_id=USER_ID,
        session_id=session.id
    ):
        if "content" in event:
            for part in event["content"].get("parts", []):
                if "text" in part:
                    print("Agent:", part["text"])

    print("\n🟢 Query finished.")


def main():
    user_message = input("Enter message to send to agent: ")
    asyncio.run(query_agent(user_message))


if __name__ == "__main__":
    main()
