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
chat.append(system("You are a senior investment banker specializing in valuation and financial modeling, particularly in project finance. For each Excel concept, function, or tool, provide a clear definition explaining what it is and why it matters in finance, investment banking, or financial modeling."))
chat.append(user("What is the Terminal Value in the project finance model? your answer cant be more then 3 sentences."))

response = chat.sample()
print(response.content)
