import json
import os
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# ----------------------------
# Paths
# ----------------------------
ROOT_DIR = Path(__file__).parent
PROJECT_DIR = ROOT_DIR / "creative_analytics"
AGENT_FOLDER = "creative_analytics_agents"
ENV_FILE = PROJECT_DIR / AGENT_FOLDER / ".env"
AGENT_CONFIG = PROJECT_DIR / AGENT_FOLDER / ".agent_engine_config.json"
OUTPUT_JSON = ROOT_DIR / "deployed_agent.json"

# ----------------------------
# Load .env
# ----------------------------
if not ENV_FILE.exists():
    raise FileNotFoundError(f".env file not found at {ENV_FILE}")

load_dotenv(dotenv_path=ENV_FILE)

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")

if not PROJECT_ID or not LOCATION:
    raise ValueError("Missing GOOGLE_CLOUD_PROJECT_ID or GOOGLE_CLOUD_LOCATION in .env")

# ----------------------------
# Change working directory to project dir
# ----------------------------
os.chdir(PROJECT_DIR)
print(f"Changed working directory to project dir: {PROJECT_DIR}")

# ----------------------------
# Deploy agent using ADK CLI
# ----------------------------
deploy_cmd = [
    "adk",
    "deploy",
    "agent_engine",
    AGENT_FOLDER,
    "--project", PROJECT_ID,
    "--region", LOCATION,
    "--agent_engine_config_file", str(AGENT_CONFIG)
]

print(f"Deploying agent from folder: {PROJECT_DIR / AGENT_FOLDER} ...")
result = subprocess.run(deploy_cmd, capture_output=True, text=True)

if result.returncode != 0:
    print("Deployment failed:")
    print(result.stderr)
    exit(1)

# ----------------------------
# Extract resource ID
# ----------------------------
resource_id = None
for line in result.stdout.splitlines():
    line = line.strip()
    if line.startswith("✅ Created agent engine:"):
        resource_id = line.split("✅ Created agent engine:")[1].strip()
        break

if not resource_id:
    print("Could not find resource ID in ADK output:")
    print(result.stdout)
    exit(1)

print(f"Agent deployed successfully: {resource_id}")

# ----------------------------
# Save resource ID to JSON
# ----------------------------
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump({"resource_id": resource_id}, f, indent=4)

print(f"Saved deployed agent info to {OUTPUT_JSON}")
