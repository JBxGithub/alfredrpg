#!/usr/bin/env python3
"""Test Node-RED API paths"""

import requests

base_url = "http://localhost:1880"

# Common API paths to test
paths = [
    "/",
    "/flows",
    "/flow",
    "/nodes",
    "/settings",
    "/info",
    "/status",
    "/debug",
    "/auth/me",
    "/library/flows",
]

print("=== Testing Node-RED API Paths ===\n")

for path in paths:
    try:
        response = requests.get(f"{base_url}{path}", timeout=5)
        status = "✓" if response.status_code == 200 else "✗"
        print(f"{status} {path}: {response.status_code}")
    except Exception as e:
        print(f"✗ {path}: Error - {e}")

print("\n=== Done ===")
