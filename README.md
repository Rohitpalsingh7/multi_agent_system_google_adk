# Overview

Brands constantly ask questions like:  

- **Did ads with logos perform better?**  
- **Which creative elements historically gave us the biggest lift?**  
- **Can you predict how this new image or video will perform before publishing it?**

Answering these questions across dozens of brands and thousands of ads is slow, repetitive, and resource-intensive. Data analysts must manually write SQL, run statistical analysis, validate creative tags, clean results, and prepare insights. Meanwhile, clients wait days for answers—delaying decisions and increasing marketing costs.

## Solution: Multi-Agent Creative Analytics System

To solve this real-world problem, I built a **Multi-Agent Creative Analytics System** using **Google ADK**, designed to let brands get **accurate insights instantly** without depending on analysts.

### Key Agents:

- **Orchestrator Agent**: Understands user intent and routes tasks to the right specialist agent.  
- **Statistical Analysis Agent**: Examines historical performance using SQL to answer *“What worked before?”*  
- **Performance Prediction Agent**: Analyzes new creatives using multi-modal LLMs and BigQuery ML to predict *“whether their ads will succeed or not”*  

Together, they automate **end-to-end creative intelligence**, empowering brands to act quickly and confidently.

## Why This Matters

This system gives brands a **front-row seat** to their creative performance:

- Analyze creative performance **anytime**  
- Predict outcomes **before running ads**  
- Make **strategic decisions in seconds**  
- Save **time, effort, and significant marketing spend**  

For analytics teams, it removes repetitive SQL tasks and frees them to focus on **high-value insights**.

## Real-World Impact

- Faster answers to creative questions  
- No more manual SQL or long turnaround times  
- Scalable intelligence across many brands  
- Improved marketing efficiency and reduced ad-spend waste  

In short, this **multi-agent system transforms how brands understand and optimize their creative performance.**

# Architecture

The diagram below illustrates the flow and interaction between agents in the Multi-Agent Creative Analytics System:

![Multi-Agent System Architecture](architecture.png)

**Key Features:**

1. **Orchestrator Agent**  
   - Receives user queries and delegates tasks to the right specialist agent.
2. **Statistical Analysis Agent**  
   - Handles historical performance queries via SQL and BigQuery database.
3. **Performance Prediction Agent**  
   - Processes new creative assets (images/videos) using multimodal LLM and hosted BigQuery ML model to forecast performance.
4. **Workflow**  
   - The orchestrator ensures the right agent handles each query.
   - Outputs are collected and returned to the user in a simplified format.

# Installation 

## Project Directory Structure (for reference)

```
multi_agent_system_google_adk/
│
├── creative_analytics/
│   ├── creative_analytics_agents/
│   │   ├── .env                  # Environment variables
│   │   ├── requirements.txt      # Python packages
│   │   ├── .agent_engine_config.json
│   │   ├── agent.py
│   │   ├── utils
│   │   └── sub_agents
│   ├── data/
│   ├── scripts/
│   └── README.md
│
└── 
```

## Prerequisites

- **Google Cloud Account**: Ensure you have a Google Cloud account with BigQuery enabled.
- **Python Version**: Python 3.11.6+ recommended.
- **APIs to Enable in Your Google Cloud Project** (required for Vertex AI agent deployment):
  - Vertex AI API
  - Cloud Storage API
  - Cloud Logging API
  - Cloud Monitoring API
  - Cloud Trace API
  - Telemetry API
  - BigQuery API

## 1. Install Python Packages

Install all dependencies from the `requirements.txt` file located in **`creative_analytics/creative_analytics_agents/`** directory.

## 2. Setup Google Cloud CLI

Initialize Google Cloud CLI and authenticate your account:

```
gcloud init
gcloud auth application-default login
```

## 3. Create the .env file 

Create a .env file under **`creative_analytics/creative_analytics_agents/`** directory. Include the following environment variables:

```
# Google cloud variables
GOOGLE_CLOUD_PROJECT_ID=your_google_project
GOOGLE_CLOUD_LOCATION=google_cloud_location

# BigQuery variables
BQ_DATASET_NAME=creative_analytics # Keep same as it is
BQ_TABLE_NAME=creative_tags_performance # Keep same as it is
BQ_MODEL_NAME=video_views_classifier # Keep same as it is

# Dataset configurations
DATASET_CONFIG_FILE=dataset_config.json # Keep same as it is

# Gemini model for agents
ROOT_AGENT_MODEL=gemini-2.5-flash # Keep same as it is
STATS_AGENT_MODEL=gemini-2.5-flash # Keep same as it is
PREDICTOR_AGENT_MODEL=gemini-2.5-flash # Keep same as it is

# Use Vertex AI
GOOGLE_GENAI_USE_VERTEXAI=1
```



