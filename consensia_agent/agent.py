from zoneinfo import ZoneInfo
from google.adk.agents import Agent
from .prompt import NEWS_SEARCH_AGENT_PROMPT_v1
from .prompt import COMPARE_STORIES_AGENT_PROMPT_v1
from google.adk.agents import SequentialAgent, ParallelAgent, LlmAgent
from google.adk.tools.agent_tool import AgentTool
from .tools import get_related_news_gnews
from .tools import get_related_news

compare_stories_agent = Agent(
    name="compare_stories_agent",
    model="gemini-2.5-flash-preview-05-20", # Can be a string for Gemini or a LiteLlm object
    description="Compares a list of related news stories based on topic and date.",
    instruction=COMPARE_STORIES_AGENT_PROMPT_v1,
)

root_agent = Agent(
    name="news_search_agent_v1",
    model="gemini-2.0-flash", # Can be a string for Gemini or a LiteLlm object
    description="Looks up related news stories based on topic and date.",
    instruction=NEWS_SEARCH_AGENT_PROMPT_v1,
    tools=[get_related_news_gnews, AgentTool(compare_stories_agent)], # Pass the function directly
)
