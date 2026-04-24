#!/usr/bin/env python3
"""Simple test for Node-RED connection"""

import requests
import json

def test_connection():
    """Test basic connection to Node-RED"""
    base_url = "http://localhost:1880"
    
    print("=== Testing Node-RED Connection ===\n")
    
    # Test 1: Check if server is up
    print("Test 1: Checking if Node-RED is running...")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"  Status: {response.status_code}")
        print(f"  Server is responding: {response.status_code == 200}")
    except Exception as e:
        print(f"  Error: {e}")
        return False
    
    # Test 2: Try to get flows
    print("\nTest 2: Getting flows...")
    try:
        response = requests.get(f"{base_url}/flows", timeout=5)
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            flows = response.json()
            print(f"  Flows count: {len(flows)}")
        else:
            print(f"  Response: {response.text[:200]}")
    except Exception as e:
        print(f"  Error: {e}")
    
    # Test 3: Try to get info
    print("\nTest 3: Getting info...")
    try:
        response = requests.get(f"{base_url}/info", timeout=5)
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            info = response.json()
            print(f"  Info: {json.dumps(info, indent=2)[:500]}")
        else:
            print(f"  Response: {response.text[:200]}")
    except Exception as e:
        print(f"  Error: {e}")
    
    # Test 4: Try to get nodes
    print("\nTest 4: Getting nodes...")
    try:
        response = requests.get(f"{base_url}/nodes", timeout=5)
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            nodes = response.json()
            print(f"  Nodes count: {len(nodes)}")
        else:
            print(f"  Response: {response.text[:200]}")
    except Exception as e:
        print(f"  Error: {e}")
    
    print("\n=== Test Complete ===")
    return True

if __name__ == '__main__':
    test_connection()
