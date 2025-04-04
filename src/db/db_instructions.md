# Database Layer Documentation


# Database Module

This directory contains the database access layer for Automagik Agents, implementing a clean repository pattern.

## Structure

- `__init__.py`: Exports all models and functions for easier imports
- `connection.py`: Database connection management and query execution
- `models.py`: Pydantic models representing database tables
- `repository/`: Directory containing repository modules for each entity type:
  - `__init__.py`: Aggregates and exports all repository functions
  - `agent.py`: Agent-related database operations
  - `user.py`: User-related database operations
  - `session.py`: Session-related database operations
  - `message.py`: Message-related database operations
  - `memory.py`: Memory-related database operations
- `db_instructions.md`: Detailed documentation and examples

## Quick Start

```python
from src.db import (
    # Models
    Agent, User, Session, Memory,
    
    # Repository functions
    create_agent, get_user, list_sessions,
    
    # Connection utilities
    execute_query
)

# Create a new agent
agent = Agent(
    name="my_agent",
    type="simple",
    model="gpt-4o-mini",
    description="A simple test agent"
)

# Save agent to database
agent_id = create_agent(agent)
```

## Design Principles

1. **Clean Architecture**: Separation of concerns between models, repositories, and connection management
2. **Type Safety**: Pydantic models ensure type-checked database operations
3. **Consistent API**: Repository functions follow a consistent pattern
4. **Error Handling**: All functions include error handling and logging 
5. **Modularity**: Each entity type has its own repository module for better organization


This document provides a comprehensive guide to using the database components in the Automagik Agents system. It's designed to be useful for both new developers and AI assistants like Claude.

## Directory Structure

The `src/db` directory contains the following components:

- `__init__.py`: Exports all important models and functions for easier imports
- `connection.py`: Handles database connection management and query execution
- `models.py`: Contains Pydantic models representing database tables
- `repository/`: Directory containing specialized repository modules:
  - `__init__.py`: Aggregates all repository functions for backward compatibility
  - `agent.py`: Functions for agent operations
  - `user.py`: Functions for user operations
  - `session.py`: Functions for session operations
  - `message.py`: Functions for message operations
  - `memory.py`: Functions for memory operations

## Overview

We use a clean repository pattern to abstract database operations:

1. **Models** represent the database tables as Pydantic classes
2. **Repository functions** handle CRUD operations for each entity type
3. **Connection utilities** manage the database pool and query execution

## Repository Pattern

Each entity type (Agent, User, Session, etc.) has its own repository module that contains all database operations related to that entity. This provides several benefits:

1. **Better organization**: Related functions are grouped together
2. **Easier maintenance**: Changes to one entity don't affect others
3. **Improved readability**: Smaller files are easier to understand
4. **Enhanced testability**: Each module can be tested independently

All repository functions are re-exported from the main `src.db` module, so you can import them directly:

```python
from src.db import create_agent, get_user, list_sessions
```

## Models

Models are Pydantic classes that represent database tables. They provide type safety, validation, and easy serialization/deserialization.

Example models:

```python
from src.db import Agent, User, Session

# Create a new user
user = User(
    email="user@example.com",
    phone_number="1234567890",
    user_data={"name": "Example User"}
)

# Create a new agent
agent = Agent(
    name="my_agent",
    type="simple",
    model="gpt-4",
    description="A simple agent",
    config={"temperature": 0.7},
    version="1.0.0"
)

# Create a new session
session = Session(
    id=uuid.uuid4(),
    user_id=1,
    agent_id=2,
    name="Example Session",
    platform="web"
)
```

## Repository Functions

Repository functions provide a clean interface for database operations. They handle all SQL construction, parameter binding, and error handling.

### Agents

```python
from src.db import create_agent, get_agent, get_agent_by_name, list_agents, update_agent, delete_agent, link_session_to_agent, increment_agent_run_id

# Create or update an agent
agent_id = create_agent(agent)

# Get an agent by ID
agent = get_agent(agent_id)

# Get an agent by name
agent = get_agent_by_name("my_agent")

# List all agents
agents = list_agents()

# List only active agents
active_agents = list_agents(active_only=True)

# Update an agent
agent.description = "Updated description"
updated_id = update_agent(agent)

# Delete an agent
success = delete_agent(agent_id)

# Increment an agent's run ID
success = increment_agent_run_id(agent_id)

# Link a session to an agent
success = link_session_to_agent(session_id, agent_id)

# Link a session to an agent with error handling
try:
    import uuid
    session_id_uuid = uuid.UUID(session_id) if isinstance(session_id, str) else session_id
    success = link_session_to_agent(session_id_uuid, agent_id)
    if success:
        print(f"Successfully linked session {session_id} to agent {agent_id}")
    else:
        print(f"Failed to link session {session_id} to agent {agent_id}")
except Exception as e:
    print(f"Error linking session to agent: {str(e)}")
```

### Users

```python
from src.db import create_user, get_user, get_user_by_email, get_user_by_identifier, list_users, update_user, delete_user

# Create a user
user_id = create_user(user)

# Get a user by ID
user = get_user(user_id)

# Get a user by email
user = get_user_by_email("user@example.com")

# Get a user by ID, email, or phone number
user = get_user_by_identifier("user@example.com")  # Using email
user = get_user_by_identifier("123456789")         # Using phone number
user = get_user_by_identifier("42")                # Using ID

# List all users
users = list_users()

# List users with pagination
users, total_count = list_users(page=1, page_size=20)

# Update a user
user.email = "updated@example.com"
updated_id = update_user(user)

# Delete a user
success = delete_user(user_id)
```

### Sessions

```python
from src.db import create_session, get_session, list_sessions, update_session, delete_session, finish_session

# Create a session
session_id = create_session(session)

# Get a session by ID
session = get_session(session_id)

# List sessions for a user
user_sessions = list_sessions(user_id=user_id)

# List sessions for an agent
agent_sessions = list_sessions(agent_id=agent_id)

# List sessions with pagination
sessions, total_count = list_sessions(page=1, page_size=20)

# List sessions with custom sorting
sessions, total_count = list_sessions(page=1, page_size=20, sort_desc=False)

# List sessions with filtering and pagination
sessions, total_count = list_sessions(
    user_id=user_id,
    agent_id=agent_id,
    page=1, 
    page_size=20
)

# Update a session
session.name = "Updated Session Name"
updated_id = update_session(session)

# Mark a session as finished
success = finish_session(session_id)

# Delete a session
success = delete_session(session_id)
```

### Memories

```python
from src.db import create_memory, get_memory, get_memory_by_name, list_memories, update_memory, delete_memory

# Create a memory
memory = Memory(
    name="important_info",
    content="This is important information",
    agent_id=agent_id,
    user_id=user_id
)
memory_id = create_memory(memory)

# Get a memory by ID
memory = get_memory(memory_id)

# Get a memory by name
memory = get_memory_by_name("important_info", agent_id=agent_id, user_id=user_id)

# List memories with filters
agent_memories = list_memories(agent_id=agent_id)
user_memories = list_memories(agent_id=agent_id, user_id=user_id)
tool_memories = list_memories(agent_id=agent_id, read_mode="tool")

# Update a memory
memory.content = "Updated content"
updated_id = update_memory(memory)

# Delete a memory
success = delete_memory(memory_id)
```

## Direct Connection Usage

For advanced use cases, you can use the connection utilities directly:

```python
from src.db import execute_query, execute_batch, get_db_connection, get_db_cursor

# Execute a simple query
results = execute_query("SELECT * FROM users WHERE email = %s", ["user@example.com"])

# Execute a batch of queries
execute_batch(
    "INSERT INTO log_entries (user_id, message) VALUES (%s, %s)",
    [(1, "Log message 1"), (1, "Log message 2")]
)

# Use a connection context manager
with get_db_connection() as conn:
    # Connection is automatically returned to the pool when done
    pass

# Use a cursor context manager
with get_db_cursor() as cursor:
    # Cursor is automatically closed when done
    cursor.execute("SELECT NOW()")
    result = cursor.fetchone()
```

## Best Practices

1. **Always use models and repository functions** instead of direct SQL when possible
2. **Handle errors** that might be raised by repository functions
3. **Use type hints** to get better IDE support
4. **Don't bypass the repository layer** by writing direct SQL in application code
5. **Keep repository functions focused** on one entity type

## Common Patterns

### Creating or Updating an Entity

Many repository functions like `create_agent` or `create_user` will automatically update the entity if it already exists with the same name/email.

```python
# This will create a new agent or update an existing one with the same name
agent_id = create_agent(agent)
```

### Working with UUIDs

Session IDs and Memory IDs are UUIDs. Always convert string UUIDs to UUID objects:

```python
import uuid

# Convert string to UUID
session_id_str = "550e8400-e29b-41d4-a716-446655440000"
session_id = uuid.UUID(session_id_str)

# Get a session using the UUID
session = get_session(session_id)
```

### Converting Between Models and Dictionaries

Pydantic models can be easily converted to dictionaries:

```python
# Convert model to dict
user_dict = user.model_dump()

# Convert dict to model
user = User(**user_dict)
```

## For LLMs/AI Assistants

When working with this codebase, here are some tips:

1. Always import from `src.db` rather than directly from sub-modules
2. Use the repository pattern for database operations
3. Use Pydantic models for all database entities
4. Handle errors appropriately in try/except blocks
5. Be aware of the difference between `None`, `[]`, and empty result sets
6. Look at the model definitions in `models.py` to understand the data structure

## Advanced Development

If you need to extend or modify the database layer:

1. **Adding a new entity type**: Create a new file in `src/db/repository/` and update `src/db/repository/__init__.py`
2. **Adding new functions to an entity**: Add the function to the appropriate file in `src/db/repository/`
3. **Fixing a bug**: Update the function in its repository file

By following these guidelines, you'll help maintain a clean and consistent codebase.

## Migrating from Direct SQL to Repository Pattern

If you're refactoring existing code that uses direct SQL queries via `execute_query`, follow these steps to convert to the repository pattern:

### Before: Direct SQL Query

```python
from src.db import execute_query

# Get agent by ID with direct SQL
def get_agent_by_id(agent_id):
    query = "SELECT * FROM agents WHERE id = %s"
    result = execute_query(query, [agent_id])
    if isinstance(result, list) and len(result) > 0:
        return result[0]
    elif 'rows' in result and len(result['rows']) > 0:
        return result['rows'][0]
    return None

# Update agent with direct SQL
def update_agent_status(agent_id, active):
    query = "UPDATE agents SET active = %s WHERE id = %s"
    result = execute_query(query, [active, agent_id])
    return result
```

### After: Repository Pattern

```python
from src.db import get_agent, update_agent

# Get agent by ID using repository function
def get_agent_by_id(agent_id):
    return get_agent(agent_id)

# Update agent using repository function
def update_agent_status(agent_id, active):
    agent = get_agent(agent_id)
    if agent:
        agent.active = active
        return update_agent(agent_id, {"active": active})
    return False
```

### Example: Converting Scripts

When updating scripts, focus on these patterns:

1. Replace `SELECT` queries with appropriate `get_*` or `list_*` functions
2. Replace `INSERT` queries with `create_*` functions
3. Replace `UPDATE` queries with `update_*` functions
4. Replace `DELETE` queries with `delete_*` functions

For complex queries that don't have a direct repository function equivalent, you may still need to use `execute_query`, but try to encapsulate these in a repository function for future use.

## UUID Handling in Database Operations

When working with UUIDs in database operations, ensure proper type adaptation:

1. **Repository Functions**: These handle UUID conversion automatically
2. **Direct SQL Queries**: Use one of the following:
   - Convert UUID to string explicitly: `str(uuid_value)`
   - Use the `safe_uuid()` utility function from `src.db.connection`
   - Rely on the registered UUID adapter (added in connection.py)

### Example:

```python
# Using safe_uuid utility for direct SQL
from src.db.connection import safe_uuid, execute_query
result = execute_query("SELECT * FROM sessions WHERE id = %s", (safe_uuid(session_id),))
```

The `safe_uuid()` function converts UUID objects to strings to prevent adaptation errors while maintaining compatibility with string values:

```python
def safe_uuid(value):
    """Convert UUID objects to strings for safe database use."""
    if isinstance(value, uuid.UUID):
        return str(value)
    return value
```

Using repository functions is always preferred as they handle UUID conversion automatically.

## Comprehensive UUID Best Practices

PostgreSQL natively supports UUIDs, and our database schema uses UUID columns for identifiers. Here are best practices for working with UUIDs:

### Database Schema
- Use the `uuid` data type for identifier columns that need to be unique across systems
- Example schema: `id UUID PRIMARY KEY DEFAULT gen_random_uuid()`

### Generating UUIDs
- Always use the utility function: `from src.db.connection import generate_uuid; new_id = generate_uuid()`
- This prevents variable shadowing issues and ensures consistent UUID generation
- Avoid direct calls to uuid.uuid4() which can be problematic in nested scopes

### Working with UUIDs in Repository Functions
```python
# Creating a new record with UUID
from src.db import create_session, Session
from src.db.connection import generate_uuid

new_session = Session(
    id=generate_uuid(),  # Safe UUID generation
    name="Example Session",
    # Other fields...
)
session_id = create_session(new_session)
```

### Direct SQL Queries with UUIDs
When using direct SQL queries (which should be avoided when possible):

1. **Use the registered adapter**: Our system has a registered adapter for UUID objects
   ```python
   from src.db import execute_query
   from src.db.connection import generate_uuid
   
   session_id = generate_uuid()
   execute_query("INSERT INTO sessions (id, name) VALUES (%s, %s)", (session_id, "Test"))
   ```

2. **Use the safe_uuid utility**:
   ```python
   from src.db.connection import safe_uuid, execute_query
   
   execute_query("SELECT * FROM sessions WHERE id = %s", (safe_uuid(session_id),))
   ```

### Variables Naming
- NEVER use `uuid` as a variable name - it shadows the module
- Use descriptive names like `session_id`, `message_uuid`, or `uuid_value` instead

### Troubleshooting UUID Issues
If you encounter issues with UUIDs:

1. **Adaptation errors**: Use `safe_uuid()` when passing UUIDs to SQL queries
2. **Variable shadowing**: Make sure no local variables are named `uuid`
3. **Import issues**: Always use `generate_uuid()` instead of direct `uuid.uuid4()` calls