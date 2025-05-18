import datetime
import os
import requests
from zoneinfo import ZoneInfo
from google.adk.agents import Agent

def get_related_news(date: str, topic: str) -> dict:
    """Retrieves related news stories based on topic and date using the NewsAPI.
    
    This function connects to the NewsAPI to fetch relevant news stories.
    The topic parameter would typically be determined by an LLM from user input.

    Args:
        date (str): The date for which to find news articles (YYYY-MM-DD format).
        topic (str): The topic of interest, as determined by an LLM.

    Returns:
        dict: A dictionary containing the news information.
              Includes a 'status' key ('success' or 'error').
              If 'success', includes a 'stories' key with a list of related news headlines.
              If 'error', includes an 'error_message' key.
    """
    try:
        # Get API key from environment variables
        api_key = os.environ.get('NEWS_API_KEY')
        if not api_key:
            return {
                "status": "error",
                "error_message": "NewsAPI key not found in environment variables."
            }
        
        # Set up API endpoint - use everything endpoint for searching articles
        base_url = "https://newsapi.org/v2/everything"
        
        # Configure the search parameters based on NewsAPI docs
        params = {
            "q": topic,  # Keywords or phrases to search for
            "apiKey": api_key,
            "language": "en",
            "sortBy": "relevancy",  # Sort by relevance to the topic
            "pageSize": 5  # Limit results to 5 articles
        }
        
        # Format and validate date if provided
        # NewsAPI accepts dates in ISO 8601 format (e.g., 2025-05-18 or 2025-05-18T02:16:26)
        if date and len(date.strip()) > 0:
            # Try to parse and format the date correctly
            try:
                # If it's just YYYY-MM-DD format, use it directly
                if len(date) >= 10 and '-' in date:
                    date_str = date.split('T')[0]  # Remove time component if present
                    # Validate the date format
                    datetime.datetime.strptime(date_str, "%Y-%m-%d")
                    
                    # NewsAPI uses from/to for date ranges
                    # Setting both to the same date searches for articles on that specific day
                    params["from"] = date_str
                    params["to"] = date_str
            except (ValueError, IndexError):
                # If date parsing fails, log it but continue without date filtering
                print(f"Warning: Could not parse date '{date}'. Continuing without date filter.")
        
        # Make the request to the API
        response = requests.get(base_url, params=params)
        
        # Process the response
        if response.status_code == 200:
            data = response.json()
            
            # Check if we received articles
            if data.get('status') == 'ok' and data.get('totalResults', 0) > 0 and data.get('articles'):
                # Extract and format the headlines
                headlines = []
                for article in data['articles']:
                    # Include title and source in the headline
                    source_name = article.get('source', {}).get('name', 'Unknown source')
                    title = article.get('title', '')
                    if title:  # Only add non-empty titles
                        headlines.append(f"{title} - {source_name}")
                
                if headlines:
                    return {
                        "status": "success",
                        "stories": headlines
                    }
            
            # If we get here, no articles were found
            date_info = f" on or around {date}" if date and len(date.strip()) > 0 else ""
            return {
                "status": "error",
                "error_message": f"No news articles found for topic '{topic}'{date_info}."
            }
        
        else:
            # Handle API errors
            try:
                error_data = response.json()
                error_message = error_data.get('message', 'Unknown error')
            except Exception:
                error_message = f"HTTP error {response.status_code}"
            
            return {
                "status": "error",
                "error_message": f"NewsAPI error: {error_message}"
            }
    
    except Exception as e:
        # Catch and handle any other exceptions
        return {
            "status": "error",
            "error_message": f"Error fetching news: {str(e)}"
        }

root_agent = Agent(
    name="news_search_agent_v1",
    model="gemini-2.0-flash", # Can be a string for Gemini or a LiteLlm object
    description="Looks up related news stories based on topic and date.",
    instruction="You are a news searching assistant. "
                "When the user provides an article on a specific topic and on a specific date, "
                "use the 'get_related_news' tool to find the related stories. "
                "When using the get_related_news tool, please pass the date in the following format: YYYY-MM-DD. "
                "If the tool returns an error, inform the user politely. "
                "If the tool is successful, present the news stories clearly.",
    tools=[get_related_news], # Pass the function directly
)
