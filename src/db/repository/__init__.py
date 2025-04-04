"""Repository modules for database operations.

This package contains the repository modules for each entity type in the database.
All repository functions are re-exported here for easier imports.
"""

# Agent repository functions
from src.db.repository.agent import (
    get_agent,
    get_agent_by_name,
    list_agents,
    create_agent,
    update_agent,
    delete_agent,
    increment_agent_run_id,
    link_session_to_agent,
    register_agent
)

# User repository functions
from src.db.repository.user import (
    get_user,
    get_user_by_email,
    get_user_by_identifier,
    list_users,
    create_user,
    update_user,
    delete_user,
    ensure_default_user_exists
)

# Session repository functions
from src.db.repository.session import (
    get_session,
    get_session_by_name,
    list_sessions,
    create_session,
    update_session,
    delete_session,
    finish_session,
    update_session_name_if_empty
)

# Message repository functions
from src.db.repository.message import (
    get_message,
    list_messages,
    count_messages,
    create_message,
    update_message,
    delete_message,
    delete_session_messages,
    list_session_messages,
    get_system_prompt
)

# Memory repository functions
from src.db.repository.memory import (
    get_memory,
    get_memory_by_name,
    list_memories,
    create_memory,
    update_memory,
    delete_memory
)
