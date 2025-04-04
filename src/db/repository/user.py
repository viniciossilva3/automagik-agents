"""User repository functions for database operations."""

import json
import logging
from typing import List, Optional, Dict, Any, Tuple
import copy

from src.db.connection import execute_query
from src.db.models import User

# Configure logger
logger = logging.getLogger(__name__)


def get_user(user_id: int) -> Optional[User]:
    """Get a user by ID.
    
    Args:
        user_id: The user ID
        
    Returns:
        User object if found, None otherwise
    """
    try:
        result = execute_query(
            "SELECT * FROM users WHERE id = %s",
            (user_id,)
        )
        return User.from_db_row(result[0]) if result else None
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {str(e)}")
        return None


def get_user_by_email(email: str) -> Optional[User]:
    """Get a user by email.
    
    Args:
        email: The user email
        
    Returns:
        User object if found, None otherwise
    """
    try:
        result = execute_query(
            "SELECT * FROM users WHERE email = %s",
            (email,)
        )
        return User.from_db_row(result[0]) if result else None
    except Exception as e:
        logger.error(f"Error getting user by email {email}: {str(e)}")
        return None


def get_user_by_identifier(identifier: str) -> Optional[User]:
    """Get a user by ID, email, or phone number.
    
    Args:
        identifier: The user ID, email, or phone number
        
    Returns:
        User object if found, None otherwise
    """
    try:
        # First check if it's an ID
        if identifier.isdigit():
            return get_user(int(identifier))
        
        # Try email
        user = get_user_by_email(identifier)
        if user:
            return user
        
        # Try phone number
        result = execute_query(
            "SELECT * FROM users WHERE phone_number = %s",
            (identifier,)
        )
        return User.from_db_row(result[0]) if result else None
    except Exception as e:
        logger.error(f"Error getting user by identifier {identifier}: {str(e)}")
        return None


def list_users(page: int = 1, page_size: int = 100) -> Tuple[List[User], int]:
    """List users with pagination.
    
    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        
    Returns:
        Tuple of (list of User objects, total count)
    """
    try:
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Get total count
        count_result = execute_query("SELECT COUNT(*) as count FROM users")
        total_count = count_result[0]["count"]
        
        # Get paginated results
        result = execute_query(
            "SELECT * FROM users ORDER BY id LIMIT %s OFFSET %s",
            (page_size, offset)
        )
        
        users = [User.from_db_row(row) for row in result]
        return users, total_count
    except Exception as e:
        logger.error(f"Error listing users: {str(e)}")
        return [], 0


def create_user(user: User) -> Optional[int]:
    """Create a new user.
    
    Args:
        user: The user to create
        
    Returns:
        The created user ID if successful, None otherwise
    """
    try:
        # Check if user with this email already exists
        if user.email:
            existing = get_user_by_email(user.email)
            if existing:
                # Update existing user
                user.id = existing.id
                return update_user(user)
        
        # Prepare user data
        user_data_json = json.dumps(user.user_data) if user.user_data else None
        
        # Insert the user
        result = execute_query(
            """
            INSERT INTO users (
                email, phone_number, user_data, created_at, updated_at
            ) VALUES (
                %s, %s, %s, NOW(), NOW()
            ) RETURNING id
            """,
            (
                user.email,
                user.phone_number,
                user_data_json
            )
        )
        
        user_id = result[0]["id"] if result else None
        logger.info(f"Created user with ID {user_id}")
        return user_id
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        return None


def update_user(user: User) -> Optional[int]:
    """Update an existing user.
    
    Args:
        user: The user to update
        
    Returns:
        The updated user ID if successful, None otherwise
    """
    try:
        if not user.id:
            if user.email:
                existing = get_user_by_email(user.email)
                if existing:
                    user.id = existing.id
                else:
                    return create_user(user)
            else:
                return create_user(user)
        
        user_data_json = json.dumps(user.user_data) if user.user_data else None
        
        execute_query(
            """
            UPDATE users SET 
                email = %s,
                phone_number = %s,
                user_data = %s,
                updated_at = NOW()
            WHERE id = %s
            """,
            (
                user.email,
                user.phone_number,
                user_data_json,
                user.id
            ),
            fetch=False
        )
        
        logger.info(f"Updated user with ID {user.id}")
        return user.id
    except Exception as e:
        logger.error(f"Error updating user {user.id}: {str(e)}")
        return None


def delete_user(user_id: int) -> bool:
    """Delete a user.
    
    Args:
        user_id: The user ID to delete
        
    Returns:
        True if successful, False otherwise
    """
    try:
        execute_query(
            "DELETE FROM users WHERE id = %s",
            (user_id,),
            fetch=False
        )
        logger.info(f"Deleted user with ID {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {str(e)}")
        return False


def ensure_default_user_exists(user_id: int = 1, email: str = "admin@automagik") -> bool:
    """Ensures a default user exists in the database, creating it if necessary.
    
    Args:
        user_id: The default user ID
        email: The default user email
    
    Returns:
        True if user already existed or was created successfully, False otherwise
    """
    try:
        # Check if user exists
        user = get_user(user_id)
        if user:
            logger.debug(f"Default user {user_id} already exists")
            return True
            
        # Create default user
        from datetime import datetime
        user = User(
            id=user_id,
            email=email,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        created_id = create_user(user)
        if created_id:
            logger.info(f"Created default user with ID {user_id} and email {email}")
            return True
        else:
            logger.warning(f"Failed to create default user with ID {user_id}")
            return False
    except Exception as e:
        logger.error(f"Error ensuring default user exists: {str(e)}")
        return False


def update_user_data(user_id: int, data_updates: Dict[str, Any], path: Optional[str] = None) -> bool:
    """Update specific fields in a user's user_data JSONB without affecting other existing fields.
    
    This function allows updating nested dictionary values while preserving the rest of the structure.
    For example, updating {'preferences': {'theme': 'dark'}} will only change the theme value
    without affecting other preference settings or other top-level keys.
    
    Args:
        user_id: The user ID to update
        data_updates: Dictionary containing the key-value pairs to update
        path: Optional JSON path for nested updates (e.g., 'preferences' to update within that object)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Get current user data
        user = get_user(user_id)
        if not user:
            logger.error(f"User {user_id} not found for data update")
            return False
            
        # Start with existing user_data or empty dict if None
        current_data = copy.deepcopy(user.user_data) if user.user_data else {}
        
        # Update strategy depends on whether we're updating a nested path or top-level
        if path:
            # Handle nested path update
            path_parts = path.split('.')
            target = current_data
            
            # Navigate to the nested location
            for i, part in enumerate(path_parts):
                # Create missing dictionary nodes
                if part not in target:
                    target[part] = {}
                    
                # Move to next level except for the last part
                if i < len(path_parts) - 1:
                    target = target[part]
                else:
                    # At the last level, we merge the dictionaries
                    if isinstance(target[part], dict) and isinstance(data_updates, dict):
                        # Deep merge for dictionaries
                        _deep_update(target[part], data_updates)
                    else:
                        # Direct assignment for non-dict values
                        target[part] = data_updates
        else:
            # Top-level update - merge with existing data
            _deep_update(current_data, data_updates)
        
        # Update the user record with the merged data
        execute_query(
            """
            UPDATE users 
            SET user_data = %s, updated_at = NOW()
            WHERE id = %s
            """,
            (json.dumps(current_data), user_id),
            fetch=False
        )
        
        logger.info(f"Updated user_data for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error updating user_data for user {user_id}: {str(e)}")
        return False


def _deep_update(target: Dict[str, Any], source: Dict[str, Any]) -> None:
    """Helper function to recursively update nested dictionaries.
    
    This performs a deep merge, preserving all keys in the target while updating
    values from the source. If both target and source have a dict at the same key,
    the dicts are merged recursively.
    
    Args:
        target: The target dictionary to update
        source: The source dictionary with updates
    """
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            # Recursively update nested dictionaries
            _deep_update(target[key], value)
        else:
            # Update or add the value
            target[key] = value
