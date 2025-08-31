import os
import json
from dotenv import load_dotenv
from xai_sdk import Client
from xai_sdk.chat import user, system
from sentence_transformers import SentenceTransformer

def get_ai_client(project_root):
    """Initializes and returns the X.AI client."""
    dotenv_path = os.path.join(project_root, '.env')
 
    if not os.path.exists(dotenv_path):
        raise FileNotFoundError(f".env file not found at {dotenv_path}")

    load_dotenv(dotenv_path=dotenv_path)
    api_key = os.getenv("xai_api_key")
    if not api_key:
        raise ValueError("API key not found. Make sure .env contains xai_api_key=...")

    return Client(api_key=api_key, timeout=3600) 

def get_definition(client, term, table_name, sheet_name):
    """Gets a definition for a financial term from the AI."""
    try:
        chat = client.chat.create(model="grok-3-mini")
        chat.append(system(
            "You are a senior investment banker specializing in valuation and financial modeling, "
            "particularly in project finance. For each concept, provide a clear, concise definition "
            "(max 3 sentences) explaining what it is and why it matters in financial modeling. "
            "Use the provided sheet and table name for additional context."
        ))
        chat.append(user(
            f"In a project finance model, what is '{term}' in the context of the '{table_name}' table on the '{sheet_name}' sheet? Your answer can't be more than 3 sentences."
        ))
        response = chat.sample()
        return response.content
    except Exception as e:
        print(f"An error occurred while getting definition for '{term}': {e}")
        return None

def load_existing_knowledge_base(path):
    """Loads an existing knowledge base and creates a lookup cache."""
    if not os.path.exists(path):
        return [], {}
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            knowledge_base = json.load(f)
        # Create a cache for quick lookups based on a unique tuple
        cache = {(item['term'], item['source_table'], item['source_sheet']): item for item in knowledge_base}
        return knowledge_base, cache
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not load or parse existing knowledge base. A new one will be created. Error: {e}")
        return [], {}

def main():
    """
    Builds a knowledge base by generating definitions and embeddings for financial terms
    found in the project's metadata.
    """
    print("Building knowledge layer...")

    # --- 1. Setup ---
    # Define paths based on the script's location.
    # This assumes the script is run from the project root directory.
    project_root = os.path.abspath(os.path.dirname(__file__))
    meta_data_path = os.path.join(project_root, "meta_data.json")
    output_dir = os.path.join(project_root, "knowledge_layer")
    os.makedirs(output_dir, exist_ok=True) # Ensure the output directory exists
    output_path = os.path.join(output_dir, "knowledge_base.json")

    # Initialize AI client
    ai_client = get_ai_client(project_root)

    # Load sentence transformer model for embeddings
    # This will download the model on first run.
    print("Loading embedding model...")
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    print("Embedding model loaded.")
 
    # Load metadata
    if not os.path.exists(meta_data_path):
        raise FileNotFoundError(f"Metadata file not found. Please generate it first: {meta_data_path}")
    
    with open(meta_data_path, 'r', encoding='utf-8') as f:
        meta_data = json.load(f)

    # Load existing knowledge base to implement caching
    print(f"Checking for existing knowledge base at {output_path}...")
    knowledge_base, kb_cache = load_existing_knowledge_base(output_path)
    print(f"Found {len(knowledge_base)} existing entries.")

    # --- 2. Process Metadata and Build Knowledge Base ---
    print("Processing metadata and generating definitions...")
    # NOTE: This can be slow and costly as it makes an API call for each term.
    # Caching is now implemented to avoid re-processing existing terms.
    for sheet_name, sheet_data in meta_data.items():
        for table_name, table_data in sheet_data.get("tables", {}).items():
            for row_name, row_data in table_data.get("rows", {}).items():
                term = row_name.strip()
                if not term:
                    continue

                # Check if this specific term combination is already in our cache
                cache_key = (term, table_name, sheet_name)
                if cache_key in kb_cache:
                    # print(f"  - Skipping (cached): '{term}' from sheet: '{sheet_name}', table: '{table_name}'")
                    continue

                print(f"  - Processing (new): '{term}' from sheet: '{sheet_name}', table: '{table_name}'")

                # Get definition from AI
                definition = get_definition(ai_client, term, table_name, sheet_name)
                if not definition:
                    print(f"    -> Failed to get definition for '{term}'. Skipping.")
                    continue
                
                print(f"    -> Definition: {definition[:50]}...")

                # Generate embedding for the definition
                embedding = embedding_model.encode(definition).tolist()

                knowledge_base.append({
                    "term": term,
                    "source_sheet": sheet_name,
                    "source_table": table_name,
                    "source_cell": row_data.get("cell_name"),
                    "definition": definition,
                    "embedding": embedding
                })

    # --- 3. Save Knowledge Base ---
    print(f"\nSaving knowledge base to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(knowledge_base, f, indent=2)

    print("✅ Knowledge layer construction complete.")
    print(f"Output saved to {output_path}")


if __name__ == "__main__":
    main()