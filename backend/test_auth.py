#!/usr/bin/env python3
"""
Test script for JWT authentication functionality
Run this script to test the authentication endpoints
"""

import requests
import json

# Base URL for the API
BASE_URL = "http://localhost:8000"

def test_signup():
    """Test user signup"""
    print("=== Testing User Signup ===")
    
    signup_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/signup", json=signup_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Signup successful!")
            print(f"Username: {data['username']}")
            print(f"Token Type: {data['token_type']}")
            print(f"Access Token: {data['access_token'][:50]}...")
            return data['access_token']
        else:
            print(f"❌ Signup failed: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error. Make sure the server is running on localhost:8000")
        return None

def test_login():
    """Test user login"""
    print("\n=== Testing User Login ===")
    
    login_data = {
        "username": "testuser",
        "password": "testpassword123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/login", json=login_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Login successful!")
            print(f"Username: {data['username']}")
            print(f"Token Type: {data['token_type']}")
            print(f"Access Token: {data['access_token'][:50]}...")
            return data['access_token']
        else:
            print(f"❌ Login failed: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error. Make sure the server is running on localhost:8000")
        return None

def test_protected_endpoint(token):
    """Test accessing a protected endpoint with JWT token"""
    print("\n=== Testing Protected Endpoint ===")
    
    if not token:
        print("❌ No token provided")
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test chat endpoint
    chat_data = {"message": "Hello, this is a test message!"}
    
    try:
        response = requests.post(f"{BASE_URL}/chat", json=chat_data, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Chat endpoint accessible!")
            print(f"Bot Response: {data['response']}")
        else:
            print(f"❌ Chat endpoint failed: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error. Make sure the server is running on localhost:8000")

def test_user_info(token):
    """Test getting current user information"""
    print("\n=== Testing User Info Endpoint ===")
    
    if not token:
        print("❌ No token provided")
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/me", headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ User info retrieved!")
            print(f"Username: {data['username']}")
            print(f"Email: {data['email']}")
        else:
            print(f"❌ User info failed: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error. Make sure the server is running on localhost:8000")

def test_invalid_token():
    """Test accessing protected endpoint with invalid token"""
    print("\n=== Testing Invalid Token ===")
    
    headers = {
        "Authorization": "Bearer invalid_token_here",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/chat", json={"message": "test"}, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ Invalid token correctly rejected!")
        else:
            print(f"❌ Unexpected response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error. Make sure the server is running on localhost:8000")

def main():
    """Run all authentication tests"""
    print("🚀 Starting JWT Authentication Tests")
    print("=" * 50)
    
    # Test signup
    token = test_signup()
    
    # Test login
    login_token = test_login()
    
    # Use the login token for protected endpoints
    if login_token:
        test_protected_endpoint(login_token)
        test_user_info(login_token)
    
    # Test invalid token
    test_invalid_token()
    
    print("\n" + "=" * 50)
    print("🏁 Authentication tests completed!")

if __name__ == "__main__":
    main() 