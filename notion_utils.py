"""Utility functions for working with Notion API."""
from typing import Dict, List, Optional
from notion_client import Client
from config import NOTION_SECRET

class NotionUtils:
    def __init__(self):
        self.client = Client(auth=NOTION_SECRET)

    def list_databases(self) -> List[Dict]:
        """List all databases the integration has access to."""
        response = self.client.search(filter={"property": "object", "value": "database"})
        return response.get('results', [])

    def list_pages(self, database_id: str, filter_params: Optional[Dict] = None) -> List[Dict]:
        """List all pages in a specific database with optional filters."""
        params = {"database_id": database_id}
        if filter_params:
            params["filter"] = filter_params
        
        response = self.client.databases.query(**params)
        return response.get('results', [])

    def get_database_properties(self, database_id: str) -> Dict:
        """Get all properties of a specific database."""
        database = self.client.databases.retrieve(database_id=database_id)
        return database.get('properties', {})

    def create_page(self, database_id: str, properties: Dict) -> Dict:
        """Create a new page in a database."""
        return self.client.pages.create(
            parent={"database_id": database_id},
            properties=properties
        )

    def update_page(self, page_id: str, properties: Dict) -> Dict:
        """Update properties of an existing page."""
        return self.client.pages.update(
            page_id=page_id,
            properties=properties
        )

    def get_block_children(self, block_id: str) -> List[Dict]:
        """Get all children blocks of a specific block."""
        response = self.client.blocks.children.list(block_id=block_id)
        return response.get('results', [])


def test_utils():
    """Test the utility functions."""
    utils = NotionUtils()
    
    print("\n=== Available Databases ===")
    databases = utils.list_databases()
    for db in databases:
        print(f"- {db.get('title')[0].get('text', {}).get('content', 'Untitled')} (ID: {db.get('id')})")
        
        # Get and display database properties
        print("\n  Properties:")
        props = utils.get_database_properties(db['id'])
        for prop_name, prop_details in props.items():
            print(f"  - {prop_name} ({prop_details.get('type', 'unknown type')})")
        
        # List some pages from the database
        print("\n  Recent Pages:")
        pages = utils.list_pages(db['id'], filter_params=None)[:3]  # Get first 3 pages
        for page in pages:
            page_title = next(
                (
                    prop.get('title', [{}])[0].get('text', {}).get('content', 'Untitled')
                    for prop in page.get('properties', {}).values()
                    if prop.get('type') == 'title'
                ),
                'Untitled'
            )
            print(f"  - {page_title} (ID: {page.get('id')})")
        print("\n" + "="*50)

if __name__ == "__main__":
    test_utils()
