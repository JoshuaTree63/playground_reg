import os
import json
import logging
from dotenv import load_dotenv
from xai_sdk import Client
from xai_sdk.chat import user, system

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration ---
# List of terms (e.g., sheet names, table names) you want to define.
# You can expand this list with your actual sheet/table names.
TERMS_TO_DEFINE = [
    "Terminal Value",
    "Discounted Cash Flow (DCF)",
    "Working Capital",
    "CAPEX Schedule",
    "Debt Service Coverage Ratio (DSCR)"
]
OUTPUT_FILENAME = "financial_terms.json"
OUTPUT_DIR = "knowledge_layer"
# --- End Configuration ---

def get_ai_definition(term: str, client: Client) -> str:
    """
    Generates a definition for a given financial term using the X AI API.

    Args:
        term: The financial term to define.
        client: The initialized X AI client.

    Returns:
        The AI-generated definition as a string, or an error message.
    """
    try:
        logging.info(f"Generating definition for: '{term}'")
        chat = client.chat.create(model="grok-3-mini")
        chat.append(system(
            "You are a senior investment banker specializing in valuation and financial modeling, "
            "particularly in project finance. For each Excel concept, function, or tool, provide a "
            "clear definition explaining what it is and why it matters in finance, investment banking, "
            "or financial modeling."
        ))
        # This line now dynamically inserts the term into the prompt
        chat.append(user(
            f"What is '{term}' in a project finance model? Your answer cannot be more than 3 sentences."
        ))

        response = chat.sample()
        return response.content.strip()
    except Exception as e:
        logging.error(f"Could not generate definition for '{term}': {e}")
        return f"Error: Could not generate definition for {term}."

def main():
    """
    Main function to generate definitions and save them to a JSON file.
    """
    # Build the path to the .env file, assuming it's in the project root
    # (one level up from the directory containing this script).
    script_dir = os.path.dirname(__file__)
    project_root = os.path.dirname(script_dir)
    dotenv_path = os.path.join(project_root, '.env')
    load_dotenv(dotenv_path=dotenv_path)
    api_key = os.getenv("xai_api_key")
    if not api_key:
        raise ValueError("API key not found. Make sure .env contains xai_api_key=...")

    # Initialize client
    client = Client(api_key=api_key, timeout=3600)

    # Create the output directory if it doesn't exist
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        logging.info(f"Created directory: {OUTPUT_DIR}")

    # Generate definitions for all terms
    definitions = {}
    for term in TERMS_TO_DEFINE:
        definition = get_ai_definition(term, client)
        definitions[term] = definition

    # Save the definitions to a JSON file
    output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILENAME)
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(definitions, f, indent=4)
        logging.info(f"Successfully saved definitions to {output_path}")
        print(f"\nDefinitions saved to {output_path}")
    except IOError as e:
        logging.error(f"Failed to write to file {output_path}: {e}")

if __name__ == "__main__":
    main()
