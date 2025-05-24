import os
from datetime import datetime, timedelta
from typing import List, Dict
import requests

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
              If 'success', includes a 'stories' key with a list of dictionaries containing:
                  - headline: The article title
                  - source: The source name
                  - description: A brief description of the article
                  - content: The article content or preview
                  - url: The URL to the full article
                  - published_at: The publication date
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
        
        # Extract keywords from the topic - try to parse out the most relevant search terms
        keywords = extract_keywords(topic)
        search_query = keywords if keywords else topic
        
        # Configure the search parameters based on NewsAPI docs
        params = {
            "q": search_query,  # Keywords or phrases to search for
            "apiKey": api_key,
            "language": "en",
            "sortBy": "relevancy",  # Start with relevancy sorting
            "pageSize": 10  # Increase page size to get more results initially
        }
        
        # Format and validate date if provided
        date_str = None
        date_range = 1  # Number of days to look before and after the target date
        
        if date and len(date.strip()) > 0:
            # Try to parse and format the date correctly
            try:
                # If it's just YYYY-MM-DD format, use it directly
                if len(date) >= 10 and '-' in date:
                    date_str = date.split('T')[0]  # Remove time component if present
                    # Validate the date format
                    target_date = datetime.strptime(date_str, "%Y-%m-%d")
                    
                    # Calculate from and to dates with a range
                    from_date = target_date - timedelta(days=date_range)
                    to_date = target_date + timedelta(days=date_range)
                    
                    # NewsAPI uses from/to for date ranges
                    params["from"] = from_date.strftime("%Y-%m-%d")
                    params["to"] = to_date.strftime("%Y-%m-%d")
            except (ValueError, IndexError):
                # If date parsing fails, log it but continue without date filtering
                print(f"Warning: Could not parse date '{date}'. Continuing without date filter.")
        
        # Make the request to the API
        response = requests.get(base_url, params=params, timeout=10)  # Add timeout to prevent hanging
        
        # Process the response
        if response.status_code == 200:
            data = response.json()
            
            # Check if we received articles
            if data.get('status') == 'ok' and data.get('totalResults', 0) > 0 and data.get('articles'):
                # Extract detailed article information
                stories = []
                for article in data['articles']:
                    # Get all relevant information from the article
                    source_name = article.get('source', {}).get('name', 'Unknown source')
                    title = article.get('title', '')
                    description = article.get('description', '')
                    content = article.get('content', '')
                    url = article.get('url', '')
                    published_at = article.get('publishedAt', '')
                    
                    if title:  # Only add articles with non-empty titles
                        story = {
                            "headline": title,
                            "source": source_name,
                            "description": description,
                            "content": content,
                            "url": url,
                            "published_at": published_at
                        }
                        stories.append(story)
                
                if stories:
                    return {
                        "status": "success",
                        "stories": stories
                    }
            
            # If no results were found with relevancy sorting, try popularity
            if data.get('status') == 'ok' and data.get('totalResults', 0) == 0:
                # Try with popularity sorting
                params["sortBy"] = "popularity"
                
                # If we had date filters, try removing them as a fallback
                if "from" in params and "to" in params:
                    fallback_params = params.copy()
                    del fallback_params["from"]
                    del fallback_params["to"]
                    fallback_response = requests.get(base_url, params=fallback_params, timeout=10)  # Add timeout
                    
                    if fallback_response.status_code == 200:
                        fallback_data = fallback_response.json()
                        if fallback_data.get('status') == 'ok' and fallback_data.get('totalResults', 0) > 0:
                            # Extract detailed article information
                            stories = []
                            for article in fallback_data['articles']:
                                source_name = article.get('source', {}).get('name', 'Unknown source')
                                title = article.get('title', '')
                                description = article.get('description', '')
                                content = article.get('content', '')
                                url = article.get('url', '')
                                published_at = article.get('publishedAt', '')
                                
                                if title:  # Only add articles with non-empty titles
                                    story = {
                                        "headline": title,
                                        "source": source_name,
                                        "description": description,
                                        "content": content,
                                        "url": url,
                                        "published_at": published_at
                                    }
                                    stories.append(story)
                            
                            if stories:
                                return {
                                    "status": "success",
                                    "stories": stories,
                                    "note": "Results found by expanding the search beyond the specified date."
                                }
            
            # If we get here, no articles were found
            date_info = f" on or around {date}" if date and len(date.strip()) > 0 else ""
            return {
                "status": "error",
                "error_message": f"No news articles found for topic '{topic}'{date_info}. Try using more specific keywords or a different date range."
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

def extract_keywords(topic: str) -> str:
    """Extract the most relevant keywords from a topic string.
    
    This function attempts to identify the main entities and keywords 
    in a topic string to create a more effective search query.
    
    Args:
        topic (str): The topic string, which may be a sentence or phrase.
        
    Returns:
        str: A string of keywords for searching.
    """
    # Simple keyword extraction logic - in a real application, you might use NLP
    # This version removes common words and keeps important nouns/entities
    
    # If the topic is already short (likely already keywords), return as is
    if len(topic.split()) <= 3:
        return topic
    
    # List of common words to filter out (could be expanded)
    stop_words = ["a", "an", "the", "and", "or", "but", "is", "are", "was", "were", 
                 "in", "on", "at", "to", "for", "with", "by", "about", "like", 
                 "from", "of", "gets", "got", "get"]
    
    # Simple tokenization (split by spaces)
    words = topic.lower().split()
    
    # Filter out common words and keep important ones
    keywords = [word for word in words if word not in stop_words]
    
    # Join the keywords with spaces to create the search query
    if keywords:
        return " ".join(keywords)
    else:
        # If all words were filtered out, return the original topic
        return topic

def get_related_news_gnews(date: str, topic: str) -> dict:
    """Retrieves related news stories based on topic and date using the GNews API.
    
    This function connects to the GNews API to fetch relevant news stories.
    The topic parameter would typically be determined by an LLM from user input.

    Args:
        date (str): The date for which to find news articles (YYYY-MM-DD format).
        topic (str): The topic of interest, as determined by an LLM.

    Returns:
        dict: A dictionary containing the news information.
              Includes a 'status' key ('success' or 'error').
              If 'success', includes a 'stories' key with a list of dictionaries containing:
                  - headline: The article title
                  - source: The source name
                  - description: A brief description of the article
                  - content: The article content or preview
                  - url: The URL to the full article
                  - published_at: The publication date
                  - image: URL to related image (if available)
              If 'error', includes an 'error_message' key.
    """
    print(f"DEBUG - Starting get_related_news_gnews with date={date}, topic={topic}")
    try:
        # Get API key from environment variables
        api_key = os.environ.get('GNEWS_API_KEY')
        print(f"DEBUG - GNEWS_API_KEY environment variable {'found' if api_key else 'NOT FOUND'}")
        
        if not api_key:
            return {
                "status": "error",
                "error_message": "GNews API key not found in environment variables. Please set the GNEWS_API_KEY environment variable."
            }
        
        # Set up API endpoint - use search endpoint for searching articles
        base_url = "https://gnews.io/api/v4/search"
        
        # Extract keywords from the topic - try to parse out the most relevant search terms
        keywords = extract_keywords(topic)
        search_query = keywords if keywords else topic
        
        # Configure the search parameters based on GNews API docs
        params = {
            "q": search_query,  # Keywords or phrases to search for
            "token": api_key,   # API key parameter (should be 'token' not 'apikey')
            "lang": "en",       # English language
            "max": 10,          # Maximum number of results
            "expand": "content" # Expand the content to get full articles instead of truncated versions
        }
        
        # Format and validate date if provided
        date_str = None
        date_range = 1  # Number of days to look before and after the target date
        
        if date and len(date.strip()) > 0:
            # Try to parse and format the date correctly
            try:
                # If it's just YYYY-MM-DD format, use it directly
                if len(date) >= 10 and '-' in date:
                    date_str = date.split('T')[0]  # Remove time component if present
                    # Validate the date format
                    target_date = datetime.strptime(date_str, "%Y-%m-%d")
                    
                    # Calculate from and to dates with a range
                    from_date = target_date - timedelta(days=date_range)
                    to_date = target_date + timedelta(days=date_range)
                    
                    # GNews API uses from/to for date ranges
                    # Use ISO 8601 format with time component as required by GNews
                    params["from"] = from_date.strftime("%Y-%m-%dT00:00:00Z")
                    params["to"] = to_date.strftime("%Y-%m-%dT23:59:59Z")
            except (ValueError, IndexError):
                # If date parsing fails, log it but continue without date filtering
                print(f"Warning: Could not parse date '{date}'. Continuing without date filter.")
        
        # Make the request to the API
        response = requests.get(base_url, params=params, timeout=10)  # Add timeout to prevent hanging
        
        # Process the response
        if response.status_code == 200:
            data = response.json()
            
            # Check if we received articles
            if data.get('articles') and len(data['articles']) > 0:
                # Extract detailed article information
                stories = []
                for article in data['articles']:
                    # Get all relevant information from the article
                    source_name = article.get('source', {}).get('name', 'Unknown source')
                    title = article.get('title', '')
                    description = article.get('description', '')
                    content = article.get('content', '')
                    url = article.get('url', '')
                    published_at = article.get('publishedAt', '')
                    image = article.get('image', '')
                    
                    if title:  # Only add articles with non-empty titles
                        story = {
                            "headline": title,
                            "source": source_name,
                            "description": description,
                            "content": content,
                            "url": url,
                            "published_at": published_at,
                            "image": image
                        }
                        stories.append(story)
                
                if stories:
                    return {
                        "status": "success",
                        "stories": stories
                    }
            
            # Try without date restrictions if no results found
            if not data.get('articles') or len(data['articles']) == 0:
                # If we had date filters, try removing them as a fallback
                if "from" in params and "to" in params:
                    fallback_params = params.copy()
                    del fallback_params["from"]
                    del fallback_params["to"]
                    
                    fallback_response = requests.get(base_url, params=fallback_params, timeout=10)  # Add timeout
                    
                    if fallback_response.status_code == 200:
                        fallback_data = fallback_response.json()
                        if fallback_data.get('articles') and len(fallback_data['articles']) > 0:
                            # Extract detailed article information
                            stories = []
                            for article in fallback_data['articles']:
                                source_name = article.get('source', {}).get('name', 'Unknown source')
                                title = article.get('title', '')
                                description = article.get('description', '')
                                content = article.get('content', '')
                                url = article.get('url', '')
                                published_at = article.get('publishedAt', '')
                                image = article.get('image', '')
                                
                                if title:  # Only add articles with non-empty titles
                                    story = {
                                        "headline": title,
                                        "source": source_name,
                                        "description": description,
                                        "content": content,
                                        "url": url,
                                        "published_at": published_at,
                                        "image": image
                                    }
                                    stories.append(story)
                            
                            if stories:
                                return {
                                    "status": "success",
                                    "stories": stories,
                                    "note": "Results found by expanding the search beyond the specified date."
                                }
            
            # If we get here, no articles were found
            date_info = f" on or around {date}" if date and len(date.strip()) > 0 else ""
            return {
                "status": "error",
                "error_message": f"No news articles found for topic '{topic}'{date_info}. Try using more specific keywords or a different date range."
            }
        
        else:
            # Handle API errors with more detailed information
            try:
                error_data = response.json()
                error_message = error_data.get('errors', ['Unknown error'])[0]
                # Print the complete error details for debugging
                print(f"GNews API error: Status {response.status_code}, Response: {error_data}")
                print(f"Request parameters (redacted): {str(params).replace(api_key, 'API_KEY_REDACTED')}")
                
                # Check for specific error conditions based on GNews documentation
                if "Daily limit" in str(error_data):
                    return {
                        "status": "error",
                        "error_message": "GNews API daily request limit exceeded. Please try again tomorrow."
                    }
                if "Invalid API key" in str(error_data) or "apiKey is not valid" in str(error_data):
                    return {
                        "status": "error",
                        "error_message": "Invalid GNews API key. Please check your API key configuration."
                    }
            except Exception as e:
                error_message = f"HTTP error {response.status_code}: {str(e)}"
                # Print the raw response content
                print(f"GNews API error: Status {response.status_code}, Raw response: {response.text}")
                print(f"Request parameters: {params}")
            
            return {
                "status": "error",
                "error_message": f"GNews API error: {error_message} (Status code: {response.status_code})"
            }
    
    except Exception as e:
        # Catch and handle any other exceptions
        return {
            "status": "error",
            "error_message": f"Error fetching news: {str(e)}"
        }
