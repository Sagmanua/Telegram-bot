import requests

OLLAMA_URL = "https://superadaptably-arrowless-leann.ngrok-free.dev"
MODEL = "llama3:latest"

def chat():
    print("🦙 Ollama Chat (type 'exit' to quit)\n")

    messages = []

    while True:
        user_input = input("You: ")
        if user_input.lower() in {"exit", "quit"}:
            break

        messages.append({"role": "user", "content": user_input})

        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": MODEL,
                "messages": messages,
                "stream": False
            },
            timeout=60
        )

        response.raise_for_status()
        data = response.json()

        assistant_message = data["message"]["content"]
        messages.append({"role": "assistant", "content": assistant_message})

        print(f"\nAssistant: {assistant_message}\n")

if __name__ == "__main__":
    chat()
