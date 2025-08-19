from xai_sdk import Client
from xai_sdk.chat import user, system

client = Client(
    api_key="",
    timeout=3600,
)

chat = client.chat.create(model="grok-3-mini")
chat.append(system("You are a PhD-level mathematician."))
chat.append(user("What is 2 + 2? be short and concise."))

response = chat.sample()
print(response.content)