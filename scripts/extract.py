import requests
import json
import os
from datetime import datetime

# --- Configuration ---
BASE_URL = "https://dummyjson.com"
RAW_DIR = "data/raw"

# Endpoints we want to pull
ENDPOINTS = {
    "products": "/products?limit=100",
    "users": "/users?limit=100",
    "carts": "/carts?limit=100"
}

def fetch_data(endpoint_name, endpoint_path):
    """
    Sends a GET request to the API and returns JSON data.
    In DE terms: this is your extraction / ingestion function.
    """
    url = BASE_URL + endpoint_path
    print(f"Fetching {endpoint_name} from {url}...")
    
    response = requests.get(url)
    
    # Check if the request succeeded (200 = OK)
    if response.status_code == 200:
        # data = response.json()
        response_json = response.json()
# DummyJSON wraps data in a key matching the endpoint name
# e.g. products are in response["products"], users in response["users"]
        data = response_json.get(endpoint_name, response_json)
        print(f"  ✓ Got {len(data)} records for {endpoint_name}")
        return data
    else:
        print(f"  ✗ Failed to fetch {endpoint_name}. Status: {response.status_code}")
        return None

def save_raw(endpoint_name, data):
    """
    Saves raw JSON to data/raw/ with a timestamp in the filename.
    Timestamping is a real DE practice — it lets you track when each pull happened.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{RAW_DIR}/{endpoint_name}_{timestamp}.json"
    
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"  ✓ Saved to {filename}")
    return filename

def run_extraction():
    """
    Master function — loops through all endpoints, fetches and saves each.
    """
    print("=" * 50)
    print("EXTRACTION LAYER — Dummy JSON")
    print("=" * 50)
    
    saved_files = {}
    
    for name, path in ENDPOINTS.items():
        data = fetch_data(name, path)
        if data:
            filepath = save_raw(name, data)
            saved_files[name] = filepath
    
    print("\n✓ Extraction complete. Files saved:")
    for name, path in saved_files.items():
        print(f"   {name}: {path}")
    
    return saved_files

# Run when script is executed directly
if __name__ == "__main__":
    run_extraction()
