import os
from dotenv import load_dotenv
from xai_sdk import Client
from xai_sdk.chat import user, system

def main():
    """
    Main function to initialize the client, send a prompt to the AI,
    and print the response.
    """
    # Build the path to the .env file relative to this script's location
    script_dir = os.path.dirname(__file__)
    dotenv_path = os.path.join(script_dir, '.env')
    
    # Debug: Print the path and check if file exists
    print(f"Looking for .env file at: {dotenv_path}")
    if not os.path.exists(dotenv_path):
        raise FileNotFoundError(f".env file not found at {dotenv_path}")
    
    # Debug: Print raw contents of .env file
    with open(dotenv_path, 'r') as f:
        print(f"Raw .env file contents: {f.read().strip()}")
    
    # Load the .env file
    load_dotenv(dotenv_path=dotenv_path)

    # Get the API key from .env
    api_key = os.getenv("xai_api_key")
    # Debug: Print the loaded API key
    print(f"Loaded API key: {api_key}")
    if not api_key:
        raise ValueError("API key not found. Make sure .env contains xai_api_key=...")

    # Initialize client with the key from .env
    client = Client(
        api_key=api_key,
        timeout=3600,
    )

    try:
        chat = client.chat.create(model="grok-3-mini")
        chat.append(system(
            "You are a senior investment banker specializing in valuation and financial modeling, "
            "particularly in project finance. For each Excel concept, function, or tool, provide a "
            "clear definition explaining what it is and why it matters in finance, investment banking, "
            "or financial modeling."
        ))
        chat.append(user("What is the Terminal Value in the project finance model? Your answer can't be more than 3 sentences."))

        response = chat.sample()
        print(response.content)
    except Exception as e:
        print(f"An error occurred while communicating with the API: {e}")

if __name__ == "__main__":
    main()