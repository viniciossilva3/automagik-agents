import logging
import json
from fastapi import HTTPException
from src.db import execute_query, get_db_connection, get_user_by_identifier, list_users, update_user
from src.db.connection import generate_uuid, safe_uuid
from src.api.models import UserCreate, UserUpdate, UserInfo, UserListResponse
from src.db.models import User
from typing import Optional, List

# Get our module's logger
logger = logging.getLogger(__name__)

async def get_users(page: int, page_size: int) -> UserListResponse:
    """
    Get a paginated list of users
    """
    try:
        users, total_count = list_users(page=page, page_size=page_size)
        
        # Convert User objects to UserInfo objects
        user_infos = []
        for user in users:
            user_infos.append(UserInfo(
                id=user.id,
                email=user.email,
                phone_number=user.phone_number,
                user_data=user.user_data,
                created_at=user.created_at,
                updated_at=user.updated_at
            ))
        
        # Calculate pagination info
        total_pages = max(1, (total_count + page_size - 1) // page_size)
        has_next = page < total_pages
        has_prev = page > 1
        
        return UserListResponse(
            users=user_infos,
            total=total_count,  # Use 'total' instead of 'total_count' to match the test
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev
        )
        
    except Exception as e:
        logger.error(f"Error listing users: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list users: {str(e)}")

async def create_user(user_create: UserCreate) -> UserInfo:
    """
    Create a new user
    """
    try:
        # Check if user already exists with the provided email or phone
        if user_create.email:
            existing_user = get_user_by_identifier(user_create.email)
            if existing_user:
                raise HTTPException(status_code=400, detail=f"User with email {user_create.email} already exists")
                
        if user_create.phone_number:
            existing_user = get_user_by_identifier(user_create.phone_number)
            if existing_user:
                raise HTTPException(status_code=400, detail=f"User with phone number {user_create.phone_number} already exists")
        
        # Convert user_data dict to JSON string if it's not None
        user_data_json = json.dumps(user_create.user_data) if user_create.user_data else None
        
        with get_db_connection() as conn:
            # Note: We're not providing an ID here - let the database auto-increment it
            result = execute_query(
                """
                INSERT INTO users (email, phone_number, user_data, created_at, updated_at) 
                VALUES (%s, %s, %s, NOW(), NOW())
                RETURNING id, created_at, updated_at
                """,
                (user_create.email, user_create.phone_number, user_data_json)
            )
            
            if not result or len(result) == 0:
                raise Exception("Failed to create user - no result returned")
                
            user_id = result[0]["id"]
            created_at = result[0]["created_at"]
            updated_at = result[0]["updated_at"]
        
        return UserInfo(
            id=user_id,
            email=user_create.email,
            phone_number=user_create.phone_number,
            user_data=user_create.user_data,
            created_at=created_at,
            updated_at=updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")

async def get_user(user_identifier: str) -> UserInfo:
    """
    Get a user by ID, email, or phone number
    """
    try:
        user = get_user_by_identifier(user_identifier)
        if not user:
            raise HTTPException(status_code=404, detail=f"User not found with identifier: {user_identifier}")
        
        return UserInfo(
            id=user.id,
            email=user.email,
            phone_number=user.phone_number,
            user_data=user.user_data,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get user: {str(e)}")

async def update_user_data(user_identifier: str, user_update: UserUpdate) -> UserInfo:
    """
    Update a user by ID, email, or phone number
    """
    try:
        # Check if user exists
        existing_user = get_user_by_identifier(user_identifier)
        if not existing_user:
            raise HTTPException(status_code=404, detail=f"User not found with identifier: {user_identifier}")
        
        # Convert user_data dict to JSON string if it's not None
        user_data_json = json.dumps(user_update.user_data) if user_update.user_data else None
        
        # Create a User object with the updated fields
        updated_user_obj = User(
            id=existing_user.id,
            email=user_update.email if user_update.email is not None else existing_user.email,
            phone_number=user_update.phone_number if user_update.phone_number is not None else existing_user.phone_number,
            user_data=user_update.user_data if user_update.user_data is not None else existing_user.user_data,
            created_at=existing_user.created_at
        )
        
        # Update the user using the repository function
        user_id = update_user(updated_user_obj)
        
        if not user_id:
            raise HTTPException(status_code=500, detail=f"Failed to update user: {user_identifier}")
        
        # Fetch the updated user to return
        updated_user = get_user_by_identifier(str(user_id))
        
        return UserInfo(
            id=updated_user.id,
            email=updated_user.email,
            phone_number=updated_user.phone_number,
            user_data=updated_user.user_data,
            created_at=updated_user.created_at,
            updated_at=updated_user.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update user: {str(e)}")

async def delete_user(user_identifier: str) -> bool:
    """
    Delete a user by ID, email, or phone number
    """
    try:
        # Check if user exists
        existing_user = get_user_by_identifier(user_identifier)
        if not existing_user:
            raise HTTPException(status_code=404, detail=f"User not found with identifier: {user_identifier}")
        
        # Delete the user
        with get_db_connection() as conn:
            execute_query(
                "DELETE FROM users WHERE id = %s",
                (existing_user.id,)
            )
        
        return True
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}") 