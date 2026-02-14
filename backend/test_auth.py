"""
Test Authentication System
Run this script to verify the authentication endpoints are working
"""
import requests
import json

# API Base URL
BASE_URL = "http://localhost:8000/api"

def test_register():
    """Test user registration"""
    print("\n=== Testing User Registration ===")
    
    # Test data
    data = {
        "username": "testuser123",
        "email": "testuser123@example.com",
        "password": "SecurePassword123!",
        "password_confirm": "SecurePassword123!"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/authentication/register/", json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 201:
            print("✅ Registration successful!")
            return True
        else:
            print("❌ Registration failed!")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_login():
    """Test user login"""
    print("\n=== Testing User Login ===")
    
    data = {
        "username": "testuser123",
        "password": "SecurePassword123!"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login/", json=data)
        print(f"Status Code: {response.status_code}")
        response_data = response.json()
        print(f"Response: {json.dumps(response_data, indent=2)}")
        
        if response.status_code == 200:
            print("✅ Login successful!")
            return response_data.get('access'), response_data.get('refresh')
        else:
            print("❌ Login failed!")
            return None, None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None, None


def test_get_current_user(token):
    """Test get current user"""
    print("\n=== Testing Get Current User ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/authentication/me/", headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Get current user successful!")
            return True
        else:
            print("❌ Get current user failed!")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_validation():
    """Test validation errors"""
    print("\n=== Testing Validation ===")
    
    # Test password mismatch
    print("\nTest 1: Password mismatch")
    data = {
        "username": "validation_test",
        "email": "validation@example.com",
        "password": "password123",
        "password_confirm": "password456"
    }
    
    response = requests.post(f"{BASE_URL}/authentication/register/", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Test duplicate username
    print("\nTest 2: Duplicate username (if previous registration worked)")
    data = {
        "username": "testuser123",
        "email": "newemail@example.com",
        "password": "SecurePassword123!",
        "password_confirm": "SecurePassword123!"
    }
    
    response = requests.post(f"{BASE_URL}/authentication/register/", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


if __name__ == "__main__":
    print("=" * 60)
    print("Authentication System Test Suite")
    print("=" * 60)
    
    # Make sure Django server is running
    try:
        requests.get(f"{BASE_URL}/")
    except Exception as e:
        print(f"\n❌ Cannot connect to Django server at {BASE_URL}")
        print("Please make sure the Django server is running (python manage.py runserver)")
        exit(1)
    
    # Run tests
    test_register()
    access_token, refresh_token = test_login()
    
    if access_token:
        test_get_current_user(access_token)
    
    test_validation()
    
    print("\n" + "=" * 60)
    print("Test suite completed!")
    print("=" * 60)
