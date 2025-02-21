"""Notion tools using Pydantic-AI and dynamic models."""
from typing import Dict, List, Optional, Type, Any, Union
from datetime import datetime
import logging
from pydantic import BaseModel
from pydantic_ai.tools import Tool
import logfire
from notion_client import Client
from notion_schema import NotionSchemaGenerator
from notion_models import (
    DatabaseListItem, DatabaseSchema, PeopleFilter,
    QueryFilter, DatabaseQuery, PageProperties, PageResponse
)
from config import NOTION_SECRET, LOGFIRE_TOKEN

# Set up standard logging for console output
console_logger = logging.getLogger(__name__)
console_logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_logger.addHandler(console_handler)

class NotionTools:
    def __init__(self):
        self.client = Client(auth=NOTION_SECRET)
        self.schema_generator = NotionSchemaGenerator()
        self.database_models: Dict[str, Type[BaseModel]] = {}
        self.tools: List[Tool] = []
        self._initialize_tools()

    def _initialize_tools(self):
        """Initialize the basic tools."""
        # Tools are now registered using decorators on the agent
        pass

    def _get_or_create_model(self, database_id: str) -> Type[BaseModel]:
        """Get an existing model or create a new one for a database."""
        if database_id not in self.database_models:
            self.database_models[database_id] = self.schema_generator.generate_database_model(database_id)
        return self.database_models[database_id]

    async def list_databases(self) -> List[DatabaseListItem]:
        """List all databases the integration has access to."""
        response = self.client.search(filter={"property": "object", "value": "database"})
        databases = []
        for db in response['results']:
            title = ''
            if db.get('title'):
                for text_block in db['title']:
                    if text_block.get('text', {}).get('content'):
                        title += text_block['text']['content']
            databases.append(DatabaseListItem(
                id=db['id'],
                title=title or 'Untitled',
                created_time=datetime.fromisoformat(db['created_time'].replace('Z', '+00:00')),
                last_edited_time=datetime.fromisoformat(db['last_edited_time'].replace('Z', '+00:00'))
            ))
        return databases

    async def get_database_schema(self, database_id: str) -> DatabaseSchema:
        """Get the schema for a specific database."""
        model = self._get_or_create_model(database_id)
        schema = model.model_json_schema()
        return DatabaseSchema(
            title=schema.get('title', ''),
            properties=schema.get('properties', {})
        )

    async def _find_user_id(self, name: str) -> Optional[str]:
        """Find a user's ID by their name."""
        try:
            users = self.client.users.list()["results"]
            for user in users:
                if name.lower() in user["name"].lower():
                    return user["id"]
            return None
        except Exception as e:
            print(f"Error finding user: {e}")
            return None

    async def query_database(
        self,
        database_id: str,
        filter_by: Optional[Union[Dict[str, Any], QueryFilter]] = None,
        sort_by: Optional[List[Dict[str, Any]]] = None,
        page_size: int = 100
    ) -> List[Dict[str, Any]]:
        """Query items from a database with optional filters."""
        logfire.debug(
            "Querying database",
            database_id=database_id,
            filter=filter_by,
            component="NotionTools",
            action="query_database"
        )
        
        model = self._get_or_create_model(database_id)
        logfire.debug(
            "Using model",
            model=model.__name__,
            component="NotionTools",
            action="query_database"
        )
        
        query_params = {
            "database_id": database_id,
            "page_size": page_size
        }
        
        # Handle filter conditions
        if isinstance(filter_by, QueryFilter):
            logfire.debug(
                "Processing QueryFilter",
                filter=filter_by.model_dump(),
                component="NotionTools",
                action="process_query_filter"
            )
            if filter_by.filter_type == 'person':
                user_id = await self._find_user_id(filter_by.value)
                logfire.debug(
                    "Found user ID",
                    user_id=user_id,
                    name=filter_by.value,
                    component="NotionTools",
                    action="find_user_id"
                )
                if user_id:
                    query_params["filter"] = {
                        "property": filter_by.property_name or "Assignee",
                        "people": {
                            "contains": user_id
                        }
                    }
                else:
                    raise ValueError(f"Could not find user with name '{filter_by.value}'")
            elif filter_by.filter_type == 'text':
                query_params["filter"] = {
                    "property": filter_by.property_name,
                    "rich_text": {
                        "contains": filter_by.value
                    }
                }
            elif filter_by.filter_type == 'select':
                query_params["filter"] = {
                    "property": filter_by.property_name,
                    "select": {
                        "equals": filter_by.value
                    }
                }
            elif filter_by.filter_type == 'status':
                query_params["filter"] = {
                    "property": filter_by.property_name,
                    "status": {
                        "equals": filter_by.value
                    }
                }
            else:
                # For other filter types, pass through as is
                query_params["filter"] = {
                    "property": filter_by.property_name,
                    filter_by.filter_type: filter_by.value
                }
        elif isinstance(filter_by, dict):
            logfire.debug(
                "Processing dict filter",
                filter=filter_by,
                component="NotionTools",
                action="process_dict_filter"
            )
            # Handle natural language filter
            if 'text' in filter_by and filter_by['text'] == 'person':
                user_id = await self._find_user_id(filter_by['value'])
                logfire.debug(
                    "Found user ID",
                    user_id=user_id,
                    name=filter_by['value'],
                    component="NotionTools",
                    action="find_user_id"
                )
                if user_id:
                    query_params["filter"] = {
                        "property": filter_by.get('property', 'Assignee'),
                        "people": {
                            "contains": user_id
                        }
                    }
                else:
                    raise ValueError(f"Could not find user with name '{filter_by['value']}'")
            else:
                query_params["filter"] = filter_by
        
        logfire.debug(
            "Query parameters prepared",
            query_params=query_params,
            component="NotionTools",
            action="prepare_query_params"
        )
        
        if sort_by:
            query_params["sorts"] = sort_by

        logfire.debug(
            "Executing Notion API query",
            component="NotionTools",
            action="execute_query"
        )
        response = self.client.databases.query(**query_params)
        logfire.debug(
            "Query results received",
            result_count=len(response['results']),
            component="NotionTools",
            action="process_results"
        )
        
        # Convert results to our model format
        results = []
        for page in response['results']:
            try:
                model_instance = model.from_notion_page(page)
                logfire.debug(
                    "Page converted to model",
                    page_id=page['id'],
                    model_type=model.__name__,
                    component="NotionTools",
                    action="convert_page"
                )
                results.append(model_instance.model_dump())
            except Exception as e:
                logfire.error(
                    "Error converting page",
                    page_id=page['id'],
                    error=str(e),
                    error_type=type(e).__name__,
                    page_data=page,
                    component="NotionTools",
                    action="convert_page_error",
                    exc_info=True
                )
                raise
        
        return results

    async def create_page(
        self,
        database_id: str,
        properties: Dict[str, Any]
    ) -> PageResponse:
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
        
        # Return the created page
        return PageResponse(
            id=response['id'],
            properties=response['properties'],
            created_time=datetime.fromisoformat(response['created_time'].replace('Z', '+00:00')),
            last_edited_time=datetime.fromisoformat(response['last_edited_time'].replace('Z', '+00:00'))
        )

    async def update_page(
        self,
        page_id: str,
        properties: Dict[str, Any]
    ) -> PageResponse:
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
        
        # Return the updated page
        return PageResponse(
            id=response['id'],
            properties=response['properties'],
            created_time=datetime.fromisoformat(response['created_time'].replace('Z', '+00:00')),
            last_edited_time=datetime.fromisoformat(response['last_edited_time'].replace('Z', '+00:00'))
        )

    async def delete_page(self, page_id: str) -> PageResponse:
        """Archive/delete a page."""
        response = self.client.pages.update(
            page_id=page_id,
            archived=True
        )
        return PageResponse(
            id=response['id'],
            properties=response['properties'],
            created_time=datetime.fromisoformat(response['created_time'].replace('Z', '+00:00')),
            last_edited_time=datetime.fromisoformat(response['last_edited_time'].replace('Z', '+00:00'))
        )

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
