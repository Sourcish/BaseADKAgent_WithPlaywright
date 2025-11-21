from google.adk.agents import Agent
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioConnectionParams, StdioServerParameters
from google.adk.tools.function_tool import FunctionTool
import random
from typing import Optional, List, Dict, Any
from datetime import datetime
from .serp_tool import search_urls_tool
import requests
import httpx
import asyncio
import time
 

PLAYWRIGHT_SERVICE_URL = "your_playwright_service_URL"


# ============ Playwright Cloud Run crawler functions ============

def playwright_crawl(
	url: str,
	selector: Optional[str] = None,
	add_delays: bool = True,
	session_id: Optional[str] = None,
	max_retries: int = 3,
) -> Dict[str, Any]:
	"""
	Crawl a single URL using the Cloud Run Playwright service.
	Returns the JSON response from the cloud service or an error object.
	"""
	payload = {
		"url": url,
		"add_delays": add_delays,
		"session_id": session_id or f"session_{random.randint(10000, 99999)}",
	}
	if selector:
		payload["selector"] = selector

	for attempt in range(1, max_retries + 1):
		try:
			print(f"[Playwright Crawl] Attempt {attempt}/{max_retries} -> {url}")
			resp = httpx.post(
				f"{PLAYWRIGHT_SERVICE_URL}/crawl",
				json=payload,
				headers={"Content-Type": "application/json"},
				timeout=300,
			)
			resp.raise_for_status()
			return resp.json()

		except httpx.TimeoutException:
			print(f"[Playwright Timeout] {url} (attempt {attempt})")
			if attempt == max_retries:
				return {"status": "error", "error": "timeout", "url": url}
			time.sleep(min(5 * attempt, 30))

		except httpx.HTTPStatusError as e:
			status = e.response.status_code
			print(f"[Playwright HTTP Error] {status} for {url}")
			# Retry 5xx
			if status >= 500 and attempt < max_retries:
				time.sleep(min(5 * attempt, 30))
				continue
			return {"status": "error", "error": f"HTTP {status}", "http_status": status, "url": url}

		except httpx.RequestError as e:
			print(f"[Playwright Request Error] {e} for {url}")
			if attempt == max_retries:
				return {"status": "error", "error": str(e), "url": url}
			time.sleep(1 + attempt)


def crawl_multiple_urls(
	urls: List[str],
	selector: Optional[str] = None,
	delay_between_urls: float = 2.0,
) -> Dict[str, Any]:
	"""
	Crawl multiple URLs sequentially using the Playwright Cloud Run service.
	Returns aggregated results and simple statistics.
	"""
	if not urls:
		return {"status": "error", "error": "No URLs provided"}

	results = []
	successful = 0
	failed = 0
	start = datetime.now()

	for idx, u in enumerate(urls, start=1):
		url = u if isinstance(u, str) else u.get("url")
		if not url:
			results.append({"status": "error", "error": "invalid_url", "input": u})
			failed += 1
			continue

		res = playwright_crawl(url, selector)
		results.append(res)
		if res.get("status") == "success":
			successful += 1
		else:
			failed += 1

		if idx < len(urls):
			time.sleep(delay_between_urls + random.uniform(-0.5, 0.5))

	elapsed = (datetime.now() - start).total_seconds()
	return {
		"status": "completed",
		"total_urls": len(urls),
		"successful": successful,
		"failed": failed,
		"elapsed_seconds": elapsed,
		"results": results,
	}


# FunctionTool wrappers
playwright_crawl_tool = FunctionTool(playwright_crawl)
crawl_multiple_urls_tool = FunctionTool(crawl_multiple_urls)


# Playwright agent
playwright_agent = LlmAgent(
	name="playwright_crawler_agent",
	model="gemini-2.5-flash",
	tools=[playwright_crawl_tool, crawl_multiple_urls_tool],
	instruction="""
	You are a Playwright Crawler Agent.
	Your task is to deep crawl web pages using the Playwright Cloud Run service.
	- Use 'playwright_crawl' to fetch a single page (returns JSON from the service).
	- Use 'crawl_multiple_urls' to process lists of URLs sequentially.
	- Do not assume JavaScript execution beyond what the cloud service provides.
	""",
)


# URL provider agent: uses google search to produce URLs for the Playwright agent
url_provider_agent = Agent(
    name="playwright_url_provider",
    model="gemini-2.5-flash",
    tools=[google_search],
    instruction="""
    You are a URL Provider Agent. Your job is to find and return relevant URLs for the Playwright crawler.
    - Use the 'google_search' tool to run focused searches based on the user's query.
    - Return a concise JSON-friendly list of URLs (either a plain list of strings or list of objects with a 'url' key).
    - Prefer official/authoritative pages and pages that directly contain the content the user asked for.
    - Keep summaries short; the Playwright agent will handle crawling and deeper extraction.
    """,
)

