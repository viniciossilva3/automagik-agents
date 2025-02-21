"""Notion tools using Pydantic-AI and dynamic models."""
from typing import Dict, List, Optional, Type, Any
from pydantic import BaseModel
from pydantic_ai.tools import Tool
from notion_client import Client
from notion_schema import NotionSchemaGenerator
from config import NOTION_SECRET

class NotionTools:
    def __init__(self):
        self.client = Client(auth=NOTION_SECRET)
        self.schema_generator = NotionSchemaGenerator()
        self.database_models: Dict[str, Type[BaseModel]] = {}
        self.tools: List[Tool] = []
        self._initialize_tools()

    def _initialize_tools(self):
        """Initialize the basic tools."""
        self.tools = [
            Tool(
                name="list_databases",
                function=self.list_databases,
                description="List all available Notion databases"
            ),
            Tool(
                name="get_database_schema",
                function=self.get_database_schema,
                description="Get the schema for a specific database"
            ),
            Tool(
                name="query_database",
                function=self.query_database,
                description="Query items from a database with optional filters"
            ),
            Tool(
                name="create_page",
                function=self.create_page,
                description="Create a new page in a database"
            ),
            Tool(
                name="update_page",
                function=self.update_page,
                description="Update an existing page in a database"
            ),
            Tool(
                name="delete_page",
                function=self.delete_page,
                description="Archive/delete a page from a database"
            )
        ]

    def _get_or_create_model(self, database_id: str) -> Type[BaseModel]:
        """Get an existing model or create a new one for a database."""
        if database_id not in self.database_models:
            self.database_models[database_id] = self.schema_generator.generate_database_model(database_id)
        return self.database_models[database_id]

    async def list_databases(self) -> List[Dict[str, str]]:
        """List all databases the integration has access to."""
        response = self.client.search(filter={"property": "object", "value": "database"})
        return [{
            'id': db['id'],
            'title': db['title'][0]['text']['content'] if db['title'] else 'Untitled',
            'created_time': db['created_time'],
            'last_edited_time': db['last_edited_time']
        } for db in response['results']]

    async def get_database_schema(self, database_id: str) -> Dict[str, Any]:
        """Get the schema for a specific database."""
        model = self._get_or_create_model(database_id)
        return model.model_json_schema()

    async def query_database(
        self,
        database_id: str,
        filter_by: Optional[Dict[str, Any]] = None,
        sort_by: Optional[List[Dict[str, Any]]] = None,
        page_size: int = 100
    ) -> List[Dict[str, Any]]:
        """Query items from a database with optional filters."""
        model = self._get_or_create_model(database_id)
        
        query_params = {
            "database_id": database_id,
            "page_size": page_size
        }
        if filter_by:
            query_params["filter"] = filter_by
        if sort_by:
            query_params["sorts"] = sort_by

        response = self.client.databases.query(**query_params)
        
        # Convert results to our model format
        return [
            model.from_notion_page(page).model_dump()
            for page in response['results']
        ]

    async def create_page(
        self,
        database_id: str,
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new page in a database."""
        model = self._get_or_create_model(database_id)
        
        # Validate the properties using our model
        page_data = model(**properties)
        
        # Convert to Notion format
        notion_properties = page_data.to_notion_properties()
        
        # Create the page
        response = self.client.pages.create(
            parent={"database_id": database_id},
            properties=notion_properties
        )
        
        # Return the created page in our model format
        return model.from_notion_page(response).model_dump()

    async def update_page(
        self,
        page_id: str,
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update an existing page."""
        # Get the database_id from the page
        page = self.client.pages.retrieve(page_id=page_id)
        database_id = page['parent']['database_id']
        
        # Get the appropriate model
        model = self._get_or_create_model(database_id)
        
        # Merge existing data with updates
        current_data = model.from_notion_page(page).model_dump()
        current_data.update(properties)
        
        # Validate the merged data
        page_data = model(**current_data)
        
        # Convert to Notion format
        notion_properties = page_data.to_notion_properties()
        
        # Update the page
        response = self.client.pages.update(
            page_id=page_id,
            properties=notion_properties
        )
        
        # Return the updated page in our model format
        return model.from_notion_page(response).model_dump()

    async def delete_page(self, page_id: str) -> Dict[str, str]:
        """Archive/delete a page."""
        self.client.pages.update(
            page_id=page_id,
            archived=True
        )
        return {"status": "success", "message": f"Page {page_id} has been archived"}

# Example usage:
if __name__ == "__main__":
    import asyncio
    
    async def main():
        tools = NotionTools()
        
        # List databases
        databases = await tools.list_databases()
        print("\nAvailable databases:")
        for db in databases:
            print(f"- {db['title']} (ID: {db['id']})")
            
            # Get schema for each database
            schema = await tools.get_database_schema(db['id'])
            print(f"\nSchema for {db['title']}:")
            print(schema)
            
            # Query some items
            items = await tools.query_database(db['id'], page_size=3)
            print(f"\nSample items from {db['title']}:")
            for item in items:
                print(f"- {item}")
    
    asyncio.run(main())
