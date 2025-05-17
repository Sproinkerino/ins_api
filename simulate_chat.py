import requests

API_URL = "https://ins-api-unrz.onrender.com/api/chat/"
user_id = "manual_test_user"
session = None

print("Welcome to the manual chatbot simulation! Type 'exit' to quit.\n")

while True:
    print("new session")
    if session is None:
        message = None
    else:
        print(session.get("assistant_message"))
        message = input("You: ")
        if message.lower() == "exit":
            break

    payload = {
        "user_id": user_id,
        "session": session,
        "message": message
    }

    response = requests.post(API_URL, json=payload)
    print(response.json())
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
        break

    data = response.json()
    print("Bot:", data.get("assistant_message", "[No message]"))
    print(data)
    session = data.get("session")
    if data.get("done"):
        print("Chat complete! All required information collected.")
        print(data.get("session").get("answers"))
        break