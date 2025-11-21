**AI Agent Web Crawler with Google ADK**
A multi-agent system built with Google's Agent Development Kit (ADK) that combines intelligent web crawling, URL discovery, and email reporting capabilities.​

### Overview
This project implements a Multi-Agent System (MAS) that orchestrates specialized AI agents to discover, crawl, and extract content from web pages. The system uses a coordinator pattern where a root agent delegates tasks to specialized sub-agents.​

### Agent Architecture
Coordinator Agent - Manages task delegation and user interaction

URL Provider Agent - Discovers relevant URLs using Google Search

Playwright Crawler Agent - Deep crawls web pages using a Cloud Run service

Gmail Integration - Sends email reports with findings

### Features
 Intelligent URL discovery through Google Search

 Deep web crawling with Playwright (Cloud Run hosted)

 Automated email reporting via Gmail API

 Built-in security against prompt injections

 Retry logic and error handling

 Configurable delays to avoid rate limiting

### Prerequisites
Python 3.12+

### Google Cloud Project with billing enabled
Vertex AI API enabled

Gmail API credentials (stored in Secret Manager)

Access to a deployed Playwright Cloud Run service

### Installation
**1. Set Up Google Cloud**
Follow the setup instructions from the ADK Foundation Codelab:​

bash
### Set your project ID
gcloud config set project <your-project-id>

### Enable required APIs
gcloud services enable aiplatform.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable gmail.googleapis.com



**2. Create Python Environment**
bash
### Create project directory
mkdir ai-web-crawler
cd ai-web-crawler

# Create virtual environment
uv venv --python 3.12
source .venv/bin/activate

# Install ADK
uv pip install google-adk


**3. Install Additional Dependencies**
bash
pip install httpx google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client google-cloud-secret-manager
4. Configure Environment Variables
Create a .env file in your project root:

bash
GOOGLE_GENAI_USE_VERTEXAI=1
GOOGLE_CLOUD_PROJECT=<your-project-id>
GOOGLE_CLOUD_LOCATION=us-central1
5. Set Up Gmail OAuth
Store your Gmail OAuth credentials in Google Secret Manager as gmail-token. The secret should contain:

json
{
  "refresh_token": "your-refresh-token",
  "client_id": "your-client-id",
  "client_secret": "your-client-secret",
  "token_uri": "https://oauth2.googleapis.com/token",
  "scopes": ["https://www.googleapis.com/auth/gmail.send"]
}


**Project Structure**

ai-web-crawler/
├── __init__.py          # Package initialization
├── agent.py             # Root coordinator agent
├── tools.py             # Playwright crawler agents and tools
├── gmail_tool.py        # Gmail integration
├── .env                 # Environment configuration
└── README.md            # This file


**Running the Agent**

### Terminal Mode
bash
adk run . //Command

### Web UI Mode (Recommended)
bash
adk web
