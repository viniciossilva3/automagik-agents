"""Pydantic models for Notion API requests and responses."""
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime

class DatabaseListItem(BaseModel):
    """A database item in the list response."""
    id: str = Field(description="Database ID")
    title: str = Field(description="Database title")
    created_time: datetime = Field(description="When the database was created")
    last_edited_time: datetime = Field(description="When the database was last edited")

class DatabaseSchema(BaseModel):
    """Database schema response."""
    title: str = Field(description="Schema title")
    properties: Dict[str, Any] = Field(description="Schema properties")

class PeopleFilter(BaseModel):
    """Filter for querying people in a database."""
    name: str = Field(description="Name of the person to filter by")
    property_name: str = Field(description="Name of the people property in the database", default="Assignee")

class QueryFilter(BaseModel):
    """Query filter for database queries."""
    filter_type: str = Field(description="Type of filter (e.g., 'person', 'text', 'date')")
    value: Any = Field(description="Filter value")
    property_name: Optional[str] = Field(description="Property name to filter on", default=None)

class DatabaseQuery(BaseModel):
    """Database query parameters."""
    database_id: str = Field(description="ID of the database to query")
    filter: Optional[Union[Dict[str, Any], QueryFilter]] = Field(description="Filter conditions", default=None)
    sort_by: Optional[List[Dict[str, Any]]] = Field(description="Sort conditions", default=None)
    page_size: Optional[int] = Field(description="Number of items per page", default=100)

class PageProperties(BaseModel):
    """Properties for creating or updating a page."""
    database_id: str = Field(description="ID of the database this page belongs to")
    properties: Dict[str, Any] = Field(description="Page properties")

class PageResponse(BaseModel):
    """Response when creating or updating a page."""
    id: str = Field(description="Page ID")
    properties: Dict[str, Any] = Field(description="Page properties")
    created_time: datetime = Field(description="When the page was created")
    last_edited_time: datetime = Field(description="When the page was last edited")
