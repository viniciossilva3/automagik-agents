"""Test script for Notion API integration."""
from notion_client import Client
from config import NOTION_SECRET

def test_notion_connection():
    """Test the connection to Notion API."""
    try:
        notion = Client(auth=NOTION_SECRET)
        # Try to list users to verify the connection
        users = notion.users.list()
        print("Successfully connected to Notion!")
        print("\nUsers in the workspace:")
        for user in users.get('results', []):
            print(f"- {user.get('name')} ({user.get('type')})")
    except Exception as e:
        print(f"Error connecting to Notion: {e}")

if __name__ == "__main__":
    test_notion_connection()
