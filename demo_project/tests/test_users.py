"""
User API tests
"""
import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_get_users():
    """Test get all users endpoint"""
    response = client.get("/users/")
    assert response.status_code == 200
    
def test_create_user():
    """Test user creation"""
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpass123"
    }
    response = client.post("/users/", json=user_data)
    # TODO: Fix this test - should expect 201 status
    assert response.status_code == 200
