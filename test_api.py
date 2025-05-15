import requests
import json
import sys

def test_chat_api(environment='local'):
    # Choose URL based on environment
    base_urls = {
        'local': "http://127.0.0.1:8000",
        'production': "https://your-app-name.onrender.com"  # Replace with your Render URL
    }
    
    url = f"{base_urls[environment]}/api/chat/"
    headers = {"Content-Type": "application/json"}
    data = {"message": "Hello, chatbot!"}
    
    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"Environment: {environment}")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Use 'production' as argument to test production environment
    env = sys.argv[1] if len(sys.argv) > 1 else 'local'
    test_chat_api(env) 