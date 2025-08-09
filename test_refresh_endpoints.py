#!/usr/bin/env python3
"""
Quick test script to verify the refresh endpoints work
"""
import requests
import json

def test_endpoints():
    base_url = "http://127.0.0.1:5000"
    
    print("Testing refresh endpoints...")
    
    # Test ingest endpoint
    try:
        print("\n1. Testing ingest endpoint...")
        response = requests.post(f"{base_url}/api/jobs/ingest", timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        
    except requests.exceptions.RequestException as e:
        print(f"Ingest endpoint error: {e}")
    
    # Test cleanup endpoint
    try:
        print("\n2. Testing cleanup endpoint...")
        response = requests.post(f"{base_url}/api/jobs/cleanup", timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        
    except requests.exceptions.RequestException as e:
        print(f"Cleanup endpoint error: {e}")

if __name__ == "__main__":
    test_endpoints()
