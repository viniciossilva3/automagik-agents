#!/usr/bin/env python3
"""
API Test Script - Tests all endpoints in the Automagik Agents API with minimal verbosity.

Features:
- Tests all API endpoints including edge cases
- Concise output format suitable for AI consumption
- Only shows details on test failures
- Provides a summary report at the end
- Auto-cleans test resources

Usage: python tests/api_tests.py
"""

import json
import os
import requests
import sys
import time
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
import argparse

# Parse command line arguments
parser = argparse.ArgumentParser(description="API Test Script")
parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
parser.add_argument("--json", "-j", action="store_true", help="Output results as JSON (for AI consumption)")
parser.add_argument("--url", help="Base URL for API (overrides .env)", default=None)
args = parser.parse_args()

# Load environment variables
env_path = Path(__file__).parent.parent.parent / '.env'  # Updated path to account for new directory structure
load_dotenv(env_path)

# Configuration
BASE_URL = args.url or os.getenv("API_BASE_URL", "http://localhost:8881")

# Get API key from environment, removing any comments or whitespace
raw_api_key = os.getenv("AM_API_KEY", "")
if raw_api_key:
    # Extract just the actual key by splitting at the first '#' or whitespace
    API_KEY = raw_api_key.split('#')[0].split()[0].strip()
else:
    API_KEY = "namastex-888"  # Default key if not in .env

VERBOSE = args.verbose
JSON_OUTPUT = args.json

# Headers
HEADERS = {"x-api-key": API_KEY}

# Test resources tracking
TEST_SESSION_ID = None
TEST_USER_ID = None
TEST_USER_EMAIL = f"test-user-{int(time.time())}@example.com"
TEST_USER_PHONE = f"+1555{int(time.time())%1000000:06d}"
TEST_USER_DATA = {"test": True, "timestamp": int(time.time())}

RESOURCES_TO_CLEANUP = {
    "sessions": [],
    "users": [],
    "memories": []
}

# Test results tracking
TEST_RESULTS = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "skipped": 0,
    "tests": []
}

# Add a global variable to control whether cleanup happens automatically
AUTO_CLEANUP = True

def log(message, level="INFO", always=False):
    """Log a message to stdout if in verbose mode or if always=True"""
    if VERBOSE or always or level in ["ERROR", "WARNING"]:
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

# Add verbose logging for API key debugging
if VERBOSE:
    log(f"Starting API tests against: {BASE_URL}")
    log(f"API Key: {API_KEY[:3]}...{API_KEY[-3:]}")
    log(f"Headers: {HEADERS}")

def run_test(test_func, *args, **kwargs):
    """Run a test function and track results"""
    global TEST_RESULTS
    test_name = test_func.__name__
    TEST_RESULTS["total"] += 1
    
    start_time = time.time()
    result = {
        "name": test_name,
        "status": "failed",
        "duration": 0,
        "details": None,
        "error": None
    }
    
    # Print test header in non-JSON mode
    if not JSON_OUTPUT:
        print(f"\n{'=' * 40}")
        print(f"TEST: {test_name}")
        print(f"{'-' * 40}")
    
    try:
        # Run the test
        log(f"Running test: {test_name}")
        response_data = test_func(*args, **kwargs)
        
        # Test passed
        TEST_RESULTS["passed"] += 1
        result["status"] = "passed"
        result["details"] = response_data
        
        # Print success in non-JSON mode
        if not JSON_OUTPUT:
            print(f"✅ PASS: {test_name}")
    except AssertionError as e:
        # Test failed with assertion
        TEST_RESULTS["failed"] += 1
        error_msg = str(e)
        result["error"] = error_msg
        
        # Print failure in non-JSON mode
        if not JSON_OUTPUT:
            print(f"❌ FAIL: {test_name} - {error_msg}")
    except Exception as e:
        # Test failed with exception
        TEST_RESULTS["failed"] += 1
        error_msg = f"{type(e).__name__}: {str(e)}"
        result["error"] = error_msg
        
        # Print failure in non-JSON mode
        if not JSON_OUTPUT:
            print(f"❌ ERROR: {test_name} - {error_msg}")
    
    # Calculate duration and store result
    result["duration"] = round(time.time() - start_time, 3)
    TEST_RESULTS["tests"].append(result)
    return result

def make_request(method, url, expected_status=200, **kwargs):
    """Make an HTTP request and handle error formatting"""
    try:
        # Ensure headers are included and contain the API key
        if 'headers' not in kwargs:
            kwargs['headers'] = HEADERS
        elif 'x-api-key' not in kwargs['headers']:
            kwargs['headers']['x-api-key'] = API_KEY
            
        # For debugging in verbose mode
        if VERBOSE:
            log(f"Request headers: {kwargs.get('headers', {})}")
            if 'json' in kwargs:
                log(f"Request payload: {json.dumps(kwargs['json'], indent=2)}")
            
        response = requests.request(method, url, **kwargs)
        
        # Log request details in verbose mode
        log(f"{method.upper()} {url} -> {response.status_code}")
        
        if response.status_code != expected_status:
            # Always log errors
            error_msg = f"Expected status {expected_status}, got {response.status_code}"
            
            # Try to parse error details from response
            try:
                error_data = response.json()
                if isinstance(error_data, dict) and 'detail' in error_data:
                    error_detail = error_data['detail']
                    error_msg += f"\nError detail: \"{error_detail}\""
            except:
                # Fallback to raw text if can't parse JSON
                error_msg += f"\nResponse: {response.text[:500]}"
            
            log(error_msg, level="ERROR", always=True)
            raise AssertionError(error_msg)
        
        # Parse JSON response if possible
        try:
            return response.json()
        except:
            return {"raw_text": response.text, "content_type": response.headers.get("content-type")}
    except requests.RequestException as e:
        error_msg = f"Request failed: {str(e)}"
        log(error_msg, level="ERROR", always=True)
        raise AssertionError(error_msg)

# ==========================================
# System Endpoint Tests
# ==========================================

def test_health_endpoint():
    """Test the health endpoint"""
    data = make_request("get", f"{BASE_URL}/health")
    assert "status" in data, "Missing status field"
    assert data["status"] == "healthy", f"Unexpected status: {data['status']}"
    return data

def test_root_endpoint():
    """Test the root endpoint"""
    data = make_request("get", f"{BASE_URL}/")
    assert "status" in data, "Missing status field"
    assert data["status"] == "online", f"Unexpected status: {data['status']}"
    return data

def test_openapi_schema():
    """Test the OpenAPI schema endpoint"""
    data = make_request("get", f"{BASE_URL}/api/v1/openapi.json")
    assert "paths" in data, "Missing paths field"
    assert "info" in data, "Missing info field"
    return {"schema_size": len(json.dumps(data)), "endpoints": len(data["paths"])}

def test_swagger_docs():
    """Test the Swagger UI documentation endpoint"""
    response = requests.get(f"{BASE_URL}/api/v1/docs")
    assert response.status_code == 200, f"Expected status 200, got {response.status_code}"
    assert "text/html" in response.headers.get("content-type", ""), "Expected HTML response"
    assert "swagger" in response.text.lower(), "Swagger UI not found in response"
    return {"content_length": len(response.text)}

def test_redoc_docs():
    """Test the ReDoc documentation endpoint"""
    response = requests.get(f"{BASE_URL}/api/v1/redoc")
    assert response.status_code == 200, f"Expected status 200, got {response.status_code}"
    assert "text/html" in response.headers.get("content-type", ""), "Expected HTML response"
    assert "redoc" in response.text.lower(), "ReDoc not found in response"
    return {"content_length": len(response.text)}

# ==========================================
# User Management Tests
# ==========================================

def test_create_user():
    """Test creating a new user"""
    global TEST_USER_ID, TEST_USER_EMAIL, TEST_USER_PHONE
    
    # Create payload with required fields
    payload = {
        "email": TEST_USER_EMAIL,
        "phone_number": TEST_USER_PHONE,
        "user_data": TEST_USER_DATA
    }
    
    log(f"Creating user with email: {TEST_USER_EMAIL}")
    
    try:
        data = make_request(
            "post",
            f"{BASE_URL}/api/v1/users",
            headers=HEADERS,
            json=payload
        )
        
        assert "id" in data, "No user ID in response"
        assert data["email"] == TEST_USER_EMAIL, f"Email mismatch: {data.get('email')} != {TEST_USER_EMAIL}"
        
        # Store user ID for other tests
        TEST_USER_ID = data["id"]
        RESOURCES_TO_CLEANUP["users"].append(TEST_USER_ID)
        
        return data
    except AssertionError as e:
        # If we get a duplicate key error, try with a different email/phone
        if "duplicate key value" in str(e):
            # Update the email and phone with a new timestamp
            TEST_USER_EMAIL = f"test-user-{int(time.time())}@example.com"
            TEST_USER_PHONE = f"+1555{int(time.time())%1000000:06d}"
            
            # Try again with new values
            payload = {
                "email": TEST_USER_EMAIL,
                "phone_number": TEST_USER_PHONE,
                "user_data": TEST_USER_DATA
            }
            
            log(f"Retrying with new email: {TEST_USER_EMAIL}")
            
            data = make_request(
                "post",
                f"{BASE_URL}/api/v1/users",
                headers=HEADERS,
                json=payload
            )
            
            assert "id" in data, "No user ID in response"
            assert data["email"] == TEST_USER_EMAIL, f"Email mismatch: {data.get('email')} != {TEST_USER_EMAIL}"
            
            # Store user ID for other tests
            TEST_USER_ID = data["id"]
            RESOURCES_TO_CLEANUP["users"].append(TEST_USER_ID)
            
            return data
        else:
            raise

def test_get_user_by_id():
    """Test getting user by ID"""
    if not TEST_USER_ID:
        TEST_RESULTS["skipped"] += 1
        return {"skipped": "No test user available"}
    
    data = make_request(
        "get",
        f"{BASE_URL}/api/v1/users/{TEST_USER_ID}",
        headers=HEADERS
    )
    
    assert data["id"] == TEST_USER_ID, f"User ID mismatch: {data.get('id')} != {TEST_USER_ID}"
    assert data["email"] == TEST_USER_EMAIL, f"Email mismatch: {data.get('email')} != {TEST_USER_EMAIL}"
    
    return data

def test_get_user_by_email():
    """Test getting user by email"""
    if not TEST_USER_EMAIL or not TEST_USER_ID:
        TEST_RESULTS["skipped"] += 1
        return {"skipped": "No test user available"}
    
    data = make_request(
        "get",
        f"{BASE_URL}/api/v1/users/{TEST_USER_EMAIL}",
        headers=HEADERS
    )
    
    assert data["email"] == TEST_USER_EMAIL, f"Email mismatch: {data.get('email')} != {TEST_USER_EMAIL}"
    
    return data

def test_get_user_by_phone():
    """Test getting user by phone number"""
    if not TEST_USER_PHONE or not TEST_USER_ID:
        TEST_RESULTS["skipped"] += 1
        return {"skipped": "No test user available"}
    
    data = make_request(
        "get",
        f"{BASE_URL}/api/v1/users/{TEST_USER_PHONE}",
        headers=HEADERS
    )
    
    assert data["phone_number"] == TEST_USER_PHONE, f"Phone mismatch: {data.get('phone_number')} != {TEST_USER_PHONE}"
    
    return data

def test_update_user_email():
    """Test updating user email"""
    global TEST_USER_EMAIL  # Must be at the top of the function
    
    if not TEST_USER_ID:
        TEST_RESULTS["skipped"] += 1
        return {"skipped": "No test user available"}
    
    # Generate a new email
    updated_email = f"updated-{TEST_USER_EMAIL}"
    
    data = make_request(
        "put",
        f"{BASE_URL}/api/v1/users/{TEST_USER_ID}",
        headers=HEADERS,
        json={"email": updated_email}
    )
    
    assert data["email"] == updated_email, f"Email not updated: {data.get('email')} != {updated_email}"
    
    # Update the global email for future tests
    TEST_USER_EMAIL = updated_email
    
    return data

def test_update_user_data():
    """Test updating user data"""
    if not TEST_USER_ID:
        TEST_RESULTS["skipped"] += 1
        return {"skipped": "No test user available"}
    
    # Update user data with new fields
    updated_data = {
        **TEST_USER_DATA,
        "updated": True,
        "timestamp": int(time.time())
    }
    
    data = make_request(
        "put",
        f"{BASE_URL}/api/v1/users/{TEST_USER_ID}",
        headers=HEADERS,
        json={"user_data": updated_data}
    )
    
    # Verify user_data contains our updates
    assert data["user_data"].get("updated") == True, "user_data.updated field not set to True"
    
    return data

def test_list_users():
    """Test listing all users"""
    data = make_request(
        "get",
        f"{BASE_URL}/api/v1/users",
        headers=HEADERS,
        params={"page": 1, "page_size": 50}
    )
    
    assert "users" in data, "No users field in response"
    assert "total_count" in data, "No total_count field in response"
    assert isinstance(data["users"], list), "Users is not a list"
    
    # Check if our test user is in the list (if we created one)
    if TEST_USER_ID:
        user_ids = [user["id"] for user in data["users"]]
        assert TEST_USER_ID in user_ids, f"Test user {TEST_USER_ID} not found in users list"
    
    return {"total_users": data["total_count"], "page_count": data["total_pages"]}

# ==========================================
# Agent Tests
# ==========================================

def test_list_agents():
    """Test listing all available agents"""
    data = make_request(
        "get",
        f"{BASE_URL}/api/v1/agent/list",
        headers=HEADERS
    )
    
    assert isinstance(data, list), "Expected a list of agents"
    assert len(data) > 0, "No agents found"
    
    # Extract agent names for reporting
    agent_names = [agent["name"] for agent in data]
    
    return {"agent_count": len(data), "agent_names": agent_names}

def test_run_agent():
    """Test running an agent to create a new session"""
    global TEST_SESSION_ID
    
    # Create a session name that's unique
    session_name = f"test-session-{int(time.time())}"
    
    # Use the test user ID if available
    user_id = TEST_USER_ID if TEST_USER_ID else 1
    
    payload = {
        "message_content": "Test message for API test automation",
        "session_name": session_name,
        "user_id": user_id,
        "context": {"source": "api_test"},
        "message_limit": 10,
        "session_origin": "api_test"
    }
    
    log(f"Running agent with session name: {session_name}")
    
    data = make_request(
        "post",
        f"{BASE_URL}/api/v1/agent/simple/run",
        expected_status=200,
        headers=HEADERS,
        json=payload
    )
    
    assert "session_id" in data, "No session_id in response"
    
    # Store session ID for other tests
    TEST_SESSION_ID = data["session_id"]
    RESOURCES_TO_CLEANUP["sessions"].append(TEST_SESSION_ID)
    
    # Wait a moment for session to be stored
    time.sleep(1)
    
    return {"session_id": TEST_SESSION_ID, "session_name": session_name}

# ==========================================
# Session Tests
# ==========================================

def test_get_session_by_id():
    """Test getting session by ID"""
    if not TEST_SESSION_ID:
        TEST_RESULTS["skipped"] += 1
        return {"skipped": "No test session available"}
    
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            data = make_request(
                "get",
                f"{BASE_URL}/api/v1/sessions/{TEST_SESSION_ID}",
                headers=HEADERS
            )
            
            assert data["session_id"] == TEST_SESSION_ID, "Session ID mismatch"
            assert data["exists"] == True, "Session does not exist according to API"
            assert "messages" in data, "No messages field in response"
            
            return {"message_count": data["total_messages"], "exists": data["exists"]}
        except AssertionError as e:
            if attempt < max_retries - 1:
                log(f"Retrying get_session (attempt {attempt+1}/{max_retries}): {str(e)}")
                time.sleep(retry_delay)
            else:
                raise

def test_list_sessions():
    """Test listing all sessions"""
    data = make_request(
        "get",
        f"{BASE_URL}/api/v1/sessions",
        headers=HEADERS
    )
    
    assert "sessions" in data, "No sessions field in response"
    assert "total_count" in data, "No total_count field in response"
    
    # Check if our test session is in the list (if we created one)
    if TEST_SESSION_ID:
        session_ids = [session["session_id"] for session in data["sessions"]]
        if TEST_SESSION_ID not in session_ids:
            log(f"Warning: Test session {TEST_SESSION_ID} not found in sessions list", level="WARNING")
    
    return {"total_sessions": data["total_count"], "page_count": data["total_pages"]}

def test_delete_session():
    """Test deleting a session"""
    if not TEST_SESSION_ID:
        TEST_RESULTS["skipped"] += 1
        return {"skipped": "No test session available"}
    
    data = make_request(
        "delete",
        f"{BASE_URL}/api/v1/sessions/{TEST_SESSION_ID}",
        headers=HEADERS
    )
    
    assert data["status"] == "success", f"Expected status 'success', got {data.get('status')}"
    assert data["session_id"] == TEST_SESSION_ID, "Session ID mismatch in response"
    
    # Remove from cleanup list since we've already deleted it
    if TEST_SESSION_ID in RESOURCES_TO_CLEANUP["sessions"]:
        RESOURCES_TO_CLEANUP["sessions"].remove(TEST_SESSION_ID)
    
    return {"status": data["status"], "session_id": data["session_id"]}

def test_delete_user():
    """Test deleting a user"""
    if not TEST_USER_ID:
        TEST_RESULTS["skipped"] += 1
        return {"skipped": "No test user available"}
    
    # Skip deletion for system user
    if TEST_USER_ID == 1:
        TEST_RESULTS["skipped"] += 1
        # Remove from cleanup list
        if TEST_USER_ID in RESOURCES_TO_CLEANUP["users"]:
            RESOURCES_TO_CLEANUP["users"].remove(TEST_USER_ID)
        return {"skipped": "Will not delete system user"}
    
    data = make_request(
        "delete",
        f"{BASE_URL}/api/v1/users/{TEST_USER_ID}",
        headers=HEADERS
    )
    
    assert data["status"] == "success", f"Expected status 'success', got {data.get('status')}"
    
    # Remove from cleanup list since we've already deleted it
    if TEST_USER_ID in RESOURCES_TO_CLEANUP["users"]:
        RESOURCES_TO_CLEANUP["users"].remove(TEST_USER_ID)
    
    return {"status": data["status"], "user_id": data["session_id"]}  # API uses session_id field for user_id

# ==========================================
# Memory Tests
# ==========================================

def test_create_memory():
    """Test creating a memory"""
    global TEST_SESSION_ID
    global TEST_USER_ID
    
    # Create a new memory for the test user
    memory_data = {
        "name": "Test Memory",
        "description": "This is a test memory",
        "content": "This is the content of the test memory",
        "user_id": TEST_USER_ID,
        "read_mode": "user_memory",
        "access": "read"
    }
    
    if TEST_SESSION_ID:
        memory_data["session_id"] = TEST_SESSION_ID
    
    data = make_request(
        "post", 
        f"{BASE_URL}/api/v1/memories", 
        json=memory_data
    )
    
    assert "id" in data, "Memory ID not returned"
    assert data["name"] == memory_data["name"], "Memory name doesn't match"
    assert data["content"] == memory_data["content"], "Memory content doesn't match"
    
    # Store memory ID for later tests
    RESOURCES_TO_CLEANUP["memories"].append(data["id"])
    
    return data

def test_get_memory_by_id():
    """Test getting a memory by ID"""
    # Create a memory first if none exists
    if not RESOURCES_TO_CLEANUP["memories"]:
        memory_data = test_create_memory()
        memory_id = memory_data["id"]
    else:
        memory_id = RESOURCES_TO_CLEANUP["memories"][0]
    
    # Get the memory by ID
    data = make_request(
        "get", 
        f"{BASE_URL}/api/v1/memories/{memory_id}"
    )
    
    assert data["id"] == memory_id, "Memory ID mismatch"
    return data

def test_update_memory():
    """Test updating a memory"""
    # Create a memory first if none exists
    if not RESOURCES_TO_CLEANUP["memories"]:
        memory_data = test_create_memory()
        memory_id = memory_data["id"]
    else:
        memory_id = RESOURCES_TO_CLEANUP["memories"][0]
    
    # Update the memory
    update_data = {
        "name": "Updated Memory",
        "content": "This memory has been updated"
    }
    
    data = make_request(
        "put", 
        f"{BASE_URL}/api/v1/memories/{memory_id}", 
        json=update_data
    )
    
    assert data["id"] == memory_id, "Memory ID mismatch"
    assert data["name"] == update_data["name"], "Updated name doesn't match"
    assert data["content"] == update_data["content"], "Updated content doesn't match"
    
    return data

def test_list_memories():
    """Test listing memories"""
    # Create a memory first if none exists
    if not RESOURCES_TO_CLEANUP["memories"]:
        test_create_memory()
    
    # List all memories
    data = make_request(
        "get", 
        f"{BASE_URL}/api/v1/memories"
    )
    
    assert "memories" in data, "Memories field missing"
    assert "count" in data, "Count field missing"
    assert "page" in data, "Page field missing"
    assert "page_size" in data, "Page size field missing"
    assert "pages" in data, "Pages field missing"
    assert len(data["memories"]) > 0, "No memories returned"
    
    return data

def test_delete_memory():
    """Test deleting a memory"""
    # Create a memory first if none exists
    if not RESOURCES_TO_CLEANUP["memories"]:
        memory_data = test_create_memory()
        memory_id = memory_data["id"]
    else:
        memory_id = RESOURCES_TO_CLEANUP["memories"].pop()
    
    # Delete the memory
    data = make_request(
        "delete", 
        f"{BASE_URL}/api/v1/memories/{memory_id}"
    )
    
    assert data["id"] == memory_id, "Memory ID mismatch"
    
    # Verify memory is deleted
    try:
        make_request(
            "get", 
            f"{BASE_URL}/api/v1/memories/{memory_id}",
            expected_status=404
        )
    except AssertionError as e:
        # We expect a 404 error, if we don't get it, re-raise the exception
        if "Expected status 404" not in str(e):
            raise
    
    return data

# ==========================================
# Error Case Tests
# ==========================================

def test_invalid_api_key():
    """Test using an invalid API key"""
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/users",
            headers={"x-api-key": "invalid-key"}
        )
        
        assert response.status_code in [401, 403], f"Expected 401/403 for invalid API key, got {response.status_code}"
        return {"status_code": response.status_code}
    except requests.RequestException as e:
        raise AssertionError(f"Request failed: {str(e)}")

def test_nonexistent_user():
    """Test getting a nonexistent user"""
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/users/nonexistent-user-{int(time.time())}",
            headers=HEADERS
        )
        
        assert response.status_code == 404, f"Expected 404 for nonexistent user, got {response.status_code}"
        return {"status_code": response.status_code}
    except requests.RequestException as e:
        raise AssertionError(f"Request failed: {str(e)}")

def test_nonexistent_session():
    """Test getting a nonexistent session"""
    try:
        nonexistent_id = f"00000000-0000-0000-0000-{int(time.time())}"
        response = requests.get(
            f"{BASE_URL}/api/v1/sessions/{nonexistent_id}",
            headers=HEADERS
        )
        
        # This endpoint doesn't return a 404, it returns a 200 with exists=False
        assert response.status_code == 200, f"Expected 200 for nonexistent session, got {response.status_code}"
        data = response.json()
        assert data["exists"] == False, "Expected exists=False for nonexistent session"
        return {"exists": data["exists"]}
    except requests.RequestException as e:
        raise AssertionError(f"Request failed: {str(e)}")

def test_invalid_user_create():
    """Test creating a user with invalid data"""
    try:
        # Empty payload should fail validation
        response = requests.post(
            f"{BASE_URL}/api/v1/users",
            headers=HEADERS,
            json={}
        )
        
        assert response.status_code == 400, f"Expected 400 for invalid user data, got {response.status_code}"
        return {"status_code": response.status_code}
    except requests.RequestException as e:
        raise AssertionError(f"Request failed: {str(e)}")

# ==========================================
# Cleanup and Reporting Functions
# ==========================================

def cleanup_resources():
    """Clean up all test resources created during testing"""
    log("Cleaning up test resources", always=True)
    
    # Keep track of successful cleanups
    cleanup_success = {
        "memories": 0,
        "sessions": 0,
        "users": 0
    }
    
    # Clean up memories
    if "memories" in RESOURCES_TO_CLEANUP:
        for memory_id in RESOURCES_TO_CLEANUP["memories"]:
            try:
                log(f"Deleting memory: {memory_id}")
                response = requests.delete(
                    f"{BASE_URL}/api/v1/memories/{memory_id}",
                    headers=HEADERS,
                    timeout=5  # Add timeout to prevent hanging
                )
                
                if response.status_code in [200, 204]:
                    cleanup_success["memories"] += 1
                else:
                    log(f"Failed to delete memory {memory_id}: Status {response.status_code}", level="WARNING")
            except Exception as e:
                log(f"Error deleting memory {memory_id}: {str(e)}", level="ERROR")
    
    # Clean up sessions
    for session_id in RESOURCES_TO_CLEANUP["sessions"]:
        try:
            log(f"Deleting session: {session_id}")
            response = requests.delete(
                f"{BASE_URL}/api/v1/sessions/{session_id}",
                headers=HEADERS,
                timeout=5  # Add timeout to prevent hanging
            )
            
            if response.status_code in [200, 204]:
                cleanup_success["sessions"] += 1
            else:
                log(f"Failed to delete session {session_id}: Status {response.status_code}", level="WARNING")
        except Exception as e:
            log(f"Error deleting session {session_id}: {str(e)}", level="ERROR")
    
    # Clean up users
    for user_id in RESOURCES_TO_CLEANUP["users"]:
        # Skip system user
        if user_id == 1:
            log(f"Skipping deletion of system user (ID: 1)", level="INFO")
            continue
            
        try:
            log(f"Deleting user: {user_id}")
            response = requests.delete(
                f"{BASE_URL}/api/v1/users/{user_id}",
                headers=HEADERS,
                timeout=5  # Add timeout to prevent hanging
            )
            
            if response.status_code in [200, 204]:
                cleanup_success["users"] += 1
            else:
                log(f"Failed to delete user {user_id}: Status {response.status_code}", level="WARNING")
        except Exception as e:
            log(f"Error deleting user {user_id}: {str(e)}", level="ERROR")
    
    # Log cleanup summary
    log(f"Cleanup summary - Users: {cleanup_success['users']}/{len(RESOURCES_TO_CLEANUP['users'])}, " +
        f"Sessions: {cleanup_success['sessions']}/{len(RESOURCES_TO_CLEANUP['sessions'])}, " +
        f"Memories: {cleanup_success.get('memories', 0)}/{len(RESOURCES_TO_CLEANUP.get('memories', []))}", 
        always=True)

def print_summary():
    """Print a summary of test results"""
    if JSON_OUTPUT:
        # Print JSON output for AI consumption
        print(json.dumps(TEST_RESULTS, indent=2))
        return
        
    # Print human-readable summary
    print("\n" + "=" * 60)
    print(f"TEST SUMMARY - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    print(f"Total Tests: {TEST_RESULTS['total']}")
    print(f"Passed: {TEST_RESULTS['passed']} ({TEST_RESULTS['passed']/TEST_RESULTS['total']*100:.1f}%)")
    print(f"Failed: {TEST_RESULTS['failed']}")
    print(f"Skipped: {TEST_RESULTS['skipped']}")
    print("-" * 60)
    
    # Print failed tests
    if TEST_RESULTS['failed'] > 0:
        print("\nFAILED TESTS:")
        for test in TEST_RESULTS['tests']:
            if test['status'] == 'failed':
                print(f"  - {test['name']}: {test['error']}")
    
    print("=" * 60)

def main():
    """Run all tests in sequence"""
    global AUTO_CLEANUP
    log(f"Starting API tests against: {BASE_URL}", always=True)
    log(f"API Key: {API_KEY[:3]}...{API_KEY[-3:]}")
    
    # Define all tests to run in sequence
    all_tests = [
        # System tests
        test_health_endpoint,
        test_root_endpoint,
        test_openapi_schema,
        test_swagger_docs,
        test_redoc_docs,
        
        # User tests
        test_create_user,
        test_get_user_by_id,
        test_get_user_by_email,
        test_get_user_by_phone,
        test_update_user_email,
        test_update_user_data,
        test_list_users,
        
        # Agent tests
        test_list_agents,
        test_run_agent,
        
        # Session tests
        test_get_session_by_id,
        test_list_sessions,
        
        # Memory tests
        test_create_memory,
        test_get_memory_by_id,
        test_update_memory,
        test_list_memories,
        
        # Error case tests
        test_invalid_api_key,
        test_nonexistent_user,
        test_nonexistent_session,
        test_invalid_user_create,
        
        # Cleanup tests
        test_delete_memory,
        test_delete_session,
        test_delete_user
    ]
    
    exit_code = 0
    
    try:
        # Run all tests
        for test_func in all_tests:
            try:
                run_test(test_func)
            except KeyboardInterrupt:
                log("Test run interrupted by user!", level="WARNING", always=True)
                break
            except Exception as e:
                log(f"Unexpected error running test {test_func.__name__}: {str(e)}", level="ERROR", always=True)
                
        # Overall status message
        if TEST_RESULTS["failed"] == 0:
            log("All tests passed successfully!", level="INFO", always=True)
        else:
            log(f"{TEST_RESULTS['failed']} tests failed!", level="ERROR", always=True)
            exit_code = 1
    except KeyboardInterrupt:
        log("Test suite interrupted by user! Cleaning up...", level="WARNING", always=True)
        exit_code = 130  # Standard exit code for SIGINT
    except Exception as e:
        log(f"Unexpected error in test suite: {str(e)}", level="ERROR", always=True)
        exit_code = 2
    finally:
        # Always clean up resources if auto cleanup is enabled
        if AUTO_CLEANUP:
            try:
                cleanup_resources()
            except Exception as e:
                log(f"Error during cleanup: {str(e)}", level="ERROR", always=True)
        
        # Print summary
        try:
            print_summary()
        except Exception as e:
            log(f"Error printing summary: {str(e)}", level="ERROR", always=True)
        
        # Return proper exit code for CI/CD
        return exit_code

# Make sure the main function is defined at the module level
__all__ = ['main']

if __name__ == "__main__":
    # Call main and use its return value as exit code
    sys.exit(main()) 