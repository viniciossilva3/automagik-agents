"""Dynamic Pydantic model generation for Notion databases."""
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel, create_model, Field
from datetime import datetime
from notion_client import Client
from config import NOTION_SECRET

class NotionSchemaGenerator:
    def __init__(self):
        self.client = Client(auth=NOTION_SECRET)
        self._type_mapping = {
            'title': str,
            'rich_text': str,
            'number': float,
            'select': str,
            'multi_select': List[str],
            'date': datetime,
            'people': List[Dict[str, Any]],  # People are complex objects with id, name, etc.
            'files': List[str],
            'checkbox': bool,
            'url': str,
            'email': str,
            'phone_number': str,
            'formula': Any,
            'relation': List[str],
            'rollup': Any,
            'created_time': datetime,
            'created_by': str,
            'last_edited_time': datetime,
            'last_edited_by': str,
            'status': str,
        }

    def _get_field_type(self, prop_type: str, prop_config: Dict[str, Any]) -> Type:
        """Get the appropriate Python/Pydantic type for a Notion property type."""
        base_type = self._type_mapping.get(prop_type, Any)
        
        # Make all fields optional since Notion properties might not always be present
        return Optional[base_type]

    def _process_property_schema(self, property_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single property schema and return field info for Pydantic."""
        prop_type = property_schema['type']
        field_type = self._get_field_type(prop_type, property_schema.get(prop_type, {}))
        
        field_info = {}
        
        # Add description if available
        if prop_type == 'select':
            options = [opt['name'] for opt in property_schema.get('select', {}).get('options', [])]
            field_info['description'] = f"Allowed values: {', '.join(options)}"
        elif prop_type == 'status':
            options = [opt['name'] for opt in property_schema.get('status', {}).get('options', [])]
            field_info['description'] = f"Status options: {', '.join(options)}"
        
        return (field_type, Field(**field_info))

    def generate_database_model(self, database_id: str, model_name: str = None) -> Type[BaseModel]:
        """Generate a Pydantic model for a Notion database schema."""
        database = self.client.databases.retrieve(database_id=database_id)
        properties = database['properties']
        
        if not model_name:
            model_name = database.get('title')[0].get('plain_text', 'NotionDatabase').replace(' ', '')
        
        fields = {}
        for prop_name, prop_schema in properties.items():
            fields[prop_name] = self._process_property_schema(prop_schema)
        
        # Create the model
        model = create_model(
            model_name,
            **fields,
            __base__=BaseModel
        )
        
        # Add some helper methods to the model
        def to_notion_properties(self) -> Dict[str, Any]:
            """Convert model data to Notion properties format."""
            props = {}
            for field_name, field_value in self:
                if field_value is None:
                    continue
                
                field_type = properties[field_name]['type']
                if field_type == 'title':
                    props[field_name] = {'title': [{'text': {'content': field_value}}]}
                elif field_type == 'rich_text':
                    props[field_name] = {'rich_text': [{'text': {'content': field_value}}]}
                elif field_type == 'select':
                    props[field_name] = {'select': {'name': field_value}}
                elif field_type == 'multi_select':
                    props[field_name] = {'multi_select': [{'name': name} for name in field_value]}
                elif field_type == 'status':
                    props[field_name] = {'status': {'name': field_value}}
                elif field_type == 'date':
                    props[field_name] = {'date': {'start': field_value.isoformat()}}
                else:
                    # For other types, pass the value as is
                    props[field_name] = {field_type: field_value}
            return props
        
        @classmethod
        def from_notion_page(cls, page: Dict[str, Any]):
            """Create model instance from Notion page data."""
            data = {}
            for prop_name, prop_data in page['properties'].items():
                prop_type = prop_data['type']
                if prop_type == 'title':
                    data[prop_name] = prop_data['title'][0]['text']['content'] if prop_data['title'] else None
                elif prop_type == 'rich_text':
                    data[prop_name] = prop_data['rich_text'][0]['text']['content'] if prop_data['rich_text'] else None
                elif prop_type == 'select':
                    data[prop_name] = prop_data['select']['name'] if prop_data['select'] else None
                elif prop_type == 'multi_select':
                    data[prop_name] = [item['name'] for item in prop_data['multi_select']]
                elif prop_type == 'status':
                    data[prop_name] = prop_data['status']['name'] if prop_data['status'] else None
                elif prop_type == 'date':
                    if prop_data['date'] and prop_data['date'].get('start'):
                        data[prop_name] = datetime.fromisoformat(prop_data['date']['start'].replace('Z', '+00:00'))
                    else:
                        data[prop_name] = None
                elif prop_type == 'relation':
                    data[prop_name] = [item['id'] for item in prop_data['relation']]
                else:
                    # For other types, get the value directly
                    data[prop_name] = prop_data.get(prop_type)
            return cls(**data)
        
        # Add the methods to the model
        setattr(model, 'to_notion_properties', to_notion_properties)
        setattr(model, 'from_notion_page', from_notion_page)
        
        return model

# Example usage:
if __name__ == "__main__":
    generator = NotionSchemaGenerator()
    
    # Example: Generate models for our existing databases
    databases = {
        "Projects": "d2823ae0-1711-4bb5-be20-5613fa668b9c",
        "Tasks": "f1dd94b7-37d8-4d1a-a6a4-7ea461b2062e",
        "Meetings": "12e2c8ca-935e-8011-8c7a-f1683b7e3565"
    }
    
    for name, db_id in databases.items():
        try:
            model = generator.generate_database_model(db_id, f"{name}Model")
            print(f"\nGenerated model for {name}:")
            print(model.model_json_schema())
        except Exception as e:
            print(f"Error generating model for {name}: {e}")
