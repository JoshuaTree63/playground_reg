import os
from dotenv import load_dotenv
from xai_sdk import Client
from xai_sdk.chat import user, system

# Load environclearment variables from .env file
load_dotenv()

# Get the API key from .env
api_key = os.getenv("xai_api_key")

if not api_key:
    raise ValueError("API key not found. Make sure .env contains xai_api_key=...")

# Initialize client with the key from .env
client = Client(
    api_key=api_key,
    timeout=3600,
)

chat = client.chat.create(model="grok-3-mini")
chat.append(system("You are a PhD-level mathematician."))
chat.append(user("What is 2 + 2? be short and concise."))

response = chat.sample()
print(response.content)
