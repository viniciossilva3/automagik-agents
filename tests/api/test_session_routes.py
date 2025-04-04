import pytest
import uuid
from src.db import get_db_connection

# Test data
test_session = {
    "id": str(uuid.uuid4()),
    "name": f"test_session_{uuid.uuid4().hex[:8]}"
}

# Global variable to store created session ID
created_session_id = None

def setup_module():
    """Setup test data before running tests"""
    global created_session_id
    
    # Create a test session directly in the database
    with get_db_connection() as conn:
        # Insert directly into the database
        conn.cursor().execute(
            """
            INSERT INTO sessions (id, name, created_at, updated_at) 
            VALUES (%s, %s, NOW(), NOW())
            """,
            (test_session["id"], test_session["name"])
        )
        conn.commit()
    
    created_session_id = test_session["id"]

def test_list_sessions(client):
    """Test listing sessions endpoint"""
    response = client.get("/api/v1/sessions")
    
    # For debugging - the issue might be auth related
    if response.status_code != 200:
        print(f"Failed with status {response.status_code}: {response.text}")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check response structure
    assert "sessions" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert "total_pages" in data
    
    # Check data types
    assert isinstance(data["sessions"], list)
    assert isinstance(data["total"], int)
    assert isinstance(data["page"], int)
    assert isinstance(data["page_size"], int)
    assert isinstance(data["total_pages"], int)
    
    # Verify the test session is in the list - ID might be formatted differently
    session_ids = [session["session_id"] for session in data["sessions"]]
    if created_session_id not in session_ids:
        print(f"Expected session ID {created_session_id} not in results: {session_ids}")
        # Try without hyphens (some systems store UUIDs differently)
        created_id_nohyphens = created_session_id.replace('-', '')
        found = False
        for sid in session_ids:
            if sid.replace('-', '') == created_id_nohyphens:
                found = True
                break
        assert found, f"Session ID {created_session_id} not found in results: {session_ids}"
    else:
        assert created_session_id in session_ids

def test_get_session_by_id(client):
    """Test getting a session by ID"""
    global created_session_id
    assert created_session_id is not None, "Session creation must succeed before this test"
    
    response = client.get(f"/api/v1/sessions/{created_session_id}")
    
    # For debugging
    if response.status_code != 200:
        print(f"Failed with status {response.status_code}: {response.text}")
        
    assert response.status_code == 200
    
    # Check response data
    data = response.json()
    assert "session_id" in data
    assert data["session_id"] == created_session_id
    assert "exists" in data
    assert data["exists"] == True
    assert "messages" in data
    assert "total_messages" in data
    assert "current_page" in data
    assert "total_pages" in data

def test_get_session_by_name(client):
    """Test getting a session by name"""
    response = client.get(f"/api/v1/sessions/{test_session['name']}")
    
    # For debugging
    if response.status_code != 200:
        print(f"Failed with status {response.status_code}: {response.text}")
        
    assert response.status_code == 200
    
    # Check response data
    data = response.json()
    assert "session_id" in data
    
    # Now we expect the session_id to match the name we used to look it up 
    assert data["session_id"] == test_session['name']
    
    assert "exists" in data
    assert data["exists"] == True

def test_get_session_with_pagination(client):
    """Test getting a session with pagination parameters"""
    response = client.get(
        f"/api/v1/sessions/{created_session_id}",
        params={"page": 1, "page_size": 10, "sort_desc": False, "hide_tools": True}
    )
    
    # For debugging
    if response.status_code != 200:
        print(f"Failed with status {response.status_code}: {response.text}")
        
    assert response.status_code == 200
    
    # Check response data
    data = response.json()
    assert data["current_page"] == 1
    assert "session_id" in data
    assert "messages" in data

def test_get_nonexistent_session(client):
    """Test getting a session that doesn't exist"""
    nonexistent_id = str(uuid.uuid4())
    response = client.get(f"/api/v1/sessions/{nonexistent_id}")
    
    # We now expect a 404 status code for nonexistent sessions
    assert response.status_code == 404

def test_delete_session(client):
    """Test deleting a session"""
    global created_session_id
    assert created_session_id is not None, "Session creation must succeed before this test"
    
    response = client.delete(f"/api/v1/sessions/{created_session_id}")
    
    # For debugging
    if response.status_code != 200:
        print(f"Failed with status {response.status_code}: {response.text}")
        
    assert response.status_code == 200
    assert response.json() == {"status": "success", "session_id": created_session_id, "message": f"Session {created_session_id} deleted successfully"}
    
    # Verify session is actually deleted - now expect 404
    response = client.get(f"/api/v1/sessions/{created_session_id}")
    assert response.status_code == 404
    
    # Also try with name
    response = client.get(f"/api/v1/sessions/{test_session['name']}")
    assert response.status_code == 404

def test_delete_nonexistent_session(client):
    """Test deleting a session that doesn't exist"""
    nonexistent_id = str(uuid.uuid4())
    response = client.delete(f"/api/v1/sessions/{nonexistent_id}")
    
    # For debugging
    if response.status_code != 404:
        print(f"Failed with status {response.status_code}: {response.text}")
        
    assert response.status_code == 404

if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 