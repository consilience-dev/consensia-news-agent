#!/usr/bin/env python3
"""
Test script to debug GNews API issues
"""
import os
import sys
import requests
from datetime import datetime, timedelta
from pathlib import Path

# Add support for loading environment variables from .env file
try:
    from dotenv import load_dotenv
    # Try to load from the .env file in the same directory as this script
    env_path = Path(__file__).parent / '.env'
    load_dotenv(dotenv_path=env_path)
    print(f"Loaded environment from {env_path}")
except ImportError:
    print("Warning: python-dotenv not installed. Will use manual .env loading.")
    # Try manual loading as fallback
    try:
        env_path = Path(__file__).parent / '.env'
        if env_path.exists():
            print(f"Manually loading from {env_path}")
            with open(env_path, 'r') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        try:
                            key, value = line.strip().split('=', 1)
                            os.environ[key] = value
                            print(f"Set environment variable: {key}")
                        except ValueError:
                            print(f"Skipping malformed line: {line.strip()}")
    except Exception as e:
        print(f"Error loading .env file manually: {e}")

def test_gnews_api():
    """Test the GNews API directly to identify 400 error issues"""
    print("\n==== GNews API Test ====\n")
    # Get API key from environment
    api_key = os.environ.get('GNEWS_API_KEY')
    if not api_key:
        print("ERROR: GNEWS_API_KEY not found in environment variables")
        print("Please make sure the GNEWS_API_KEY is defined in the .env file")
        return
    
    print(f"Found GNEWS_API_KEY in environment variables: {api_key[:4]}...{api_key[-4:]}")
    
    # Set up API endpoint
    base_url = "https://gnews.io/api/v4/search"
    
    # Simple test parameters
    params = {
        "q": "technology",  # Simple keyword search
        "token": api_key,   # API key parameter
        "lang": "en",       # English language
        "max": 10           # Maximum number of results
    }
    
    # Add date range
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=1)
    
    params["from"] = yesterday.strftime("%Y-%m-%dT00:00:00Z")
    params["to"] = tomorrow.strftime("%Y-%m-%dT23:59:59Z")
    
    # Print request details
    # Create a masked URL and params for logging to avoid exposing the API key
    safe_params = params.copy()
    safe_params['token'] = f"{api_key[:4]}...{api_key[-4:]}"
    
    full_url = requests.Request('GET', base_url, params=params).prepare().url
    safe_url = full_url.replace(api_key, f"{api_key[:4]}...{api_key[-4:]}")
    
    print(f"Making request to: {safe_url}")
    print(f"Request parameters: {safe_params}")
    
    # Make the request
    response = requests.get(base_url, params=params, timeout=10)  # Add timeout to prevent hanging
    
    # Print response details
    print(f"Response status code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        article_count = len(data.get('articles', []))
        print(f"Received {article_count} articles")
        if article_count > 0:
            print(f"First article title: {data['articles'][0]['title']}")
    else:
        print(f"Error response: {response.text}")
    
    # Test without date parameters
    print("\n--- Testing without date parameters ---")
    params_no_date = params.copy()
    if "from" in params_no_date:
        del params_no_date["from"]
    if "to" in params_no_date:
        del params_no_date["to"]
    
    full_url = requests.Request('GET', base_url, params=params_no_date).prepare().url
    safe_url = full_url.replace(api_key, f"{api_key[:4]}...{api_key[-4:]}")
    print(f"Making request to: {safe_url}")
    
    response = requests.get(base_url, params=params_no_date, timeout=10)  # Add timeout to prevent hanging
    print(f"Response status code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        article_count = len(data.get('articles', []))
        print(f"Received {article_count} articles")
    else:
        print(f"Error response: {response.text}")

def main():
    """Main entry point for the script"""
    # Test if we can import python-dotenv and install if needed
    try:
        import dotenv
    except ImportError:
        print("python-dotenv package not found. Attempting to install...")
        try:
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "python-dotenv"])
            print("Successfully installed python-dotenv")
            # Re-import after installation
            import dotenv
        except Exception as e:
            print(f"Failed to install python-dotenv: {e}")
    
    test_gnews_api()

if __name__ == "__main__":
    main()
