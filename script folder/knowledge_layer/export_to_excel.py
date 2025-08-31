import json
import os
import pandas as pd

def export_to_excel(json_path, excel_path):
    """
    Reads a JSON file containing a list of dictionaries, removes the 'embedding' key
    from each dictionary, and exports the data to an Excel file.

    Args:
        json_path (str): The path to the input knowledge_base.json file.
        excel_path (str): The path where the output Excel file will be saved.
    """
    # --- 1. Load Data ---
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"Knowledge base file not found at: {json_path}")

    with open(json_path, 'r', encoding='utf-8') as f:
        knowledge_base = json.load(f)

    # --- 2. Prepare Data for Export (Remove Embeddings) ---
    data_for_export = []
    for item in knowledge_base:
        # Create a copy of the item dictionary without the 'embedding' key
        item_copy = {key: value for key, value in item.items() if key != 'embedding'}
        data_for_export.append(item_copy)
    
    if not data_for_export:
        print("Warning: No data found to export.")
        return

    # --- 3. Create DataFrame and Export to Excel ---
    print(f"Exporting {len(data_for_export)} records to Excel...")
    df = pd.DataFrame(data_for_export)

    # Reorder columns for better readability in the Excel file
    column_order = [
        "term", 
        "definition", 
        "source_sheet", 
        "source_table", 
        "source_cell"
    ]
    df = df.reindex(columns=[col for col in column_order if col in df.columns])

    df.to_excel(excel_path, index=False, engine='openpyxl')
    print(f"✅ Successfully exported data to {excel_path}")

if __name__ == "__main__":
    project_root = os.path.dirname(__file__)
    kb_path = os.path.join(project_root, 'knowledge_base.json')
    output_excel_path = os.path.join(project_root, 'knowledge_base_export.xlsx')
    
    export_to_excel(kb_path, output_excel_path)