#!/usr/bin/env python3
"""
Test the get_related_news_gnews function directly
"""
import os
import sys
from pathlib import Path

# Add support for loading environment variables from .env file
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    load_dotenv(dotenv_path=env_path)
    print(f"Loaded environment from {env_path}")
except ImportError:
    print("Warning: python-dotenv not installed. Using manual .env loading.")
    try:
        env_path = Path(__file__).parent / '.env'
        if env_path.exists():
            with open(env_path, 'r') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        try:
                            key, value = line.strip().split('=', 1)
                            os.environ[key] = value
                        except ValueError:
                            pass
    except Exception as e:
        print(f"Error loading .env file manually: {e}")

# Import the function we want to test
from tools import get_related_news_gnews

def main():
    """Test the get_related_news_gnews function"""
    print("\n===== Testing get_related_news_gnews function =====\n")
    
    # Test with current date and a simple topic
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Test case 1: with date and topic
    print("\nTest Case 1: With date and topic")
    result = get_related_news_gnews(date=today, topic="artificial intelligence")
    
    if result["status"] == "success":
        print(f"SUCCESS! Found {len(result['stories'])} stories")
        if len(result['stories']) > 0:
            first_story = result['stories'][0]
            print(f"First headline: {first_story['headline']}")
            print(f"Source: {first_story['source']}")
    else:
        print(f"ERROR: {result['error_message']}")
    
    # Test case 2: without date
    print("\nTest Case 2: Without date")
    result = get_related_news_gnews(date="", topic="climate change")
    
    if result["status"] == "success":
        print(f"SUCCESS! Found {len(result['stories'])} stories")
        if len(result['stories']) > 0:
            first_story = result['stories'][0]
            print(f"First headline: {first_story['headline']}")
            print(f"Source: {first_story['source']}")
    else:
        print(f"ERROR: {result['error_message']}")

if __name__ == "__main__":
    main()
