import requests

API_URL = "http://127.0.0.1:8000/api/chat/"
user_id = "manual_test_user"
session = None

print("Welcome to the manual chatbot simulation! Type 'exit' to quit.\n")

while True:
    if session is None:
        message = None
    else:
        message = input("You: ")
        if message.lower() == "exit":
            break

    payload = {
        "user_id": user_id,
        "session": session,
        "message": message
    }

    response = requests.post(API_URL, json=payload)
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
        break

    data = response.json()
    print("Bot:", data.get("assistant_message", "[No message]"))
    print(data)
    session = data.get("session")
    if data.get("done"):
        print("Chat complete! All required information collected.")
        break