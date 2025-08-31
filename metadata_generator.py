import json
import os
from collections import defaultdict
from dotenv import load_dotenv
from xai_sdk import Client
from xai_sdk.chat import user, system
from sentence_transformers import SentenceTransformer

# Import the formula parsing function from your other script
from formulas_extraction import get_absolute_references

# Path to your existing JSON
input_path = "/Users/joshualevi/git_projects/playground_reg/jsonformatter.JSON"

# Load JSON
with open(input_path, "r", encoding='utf-8') as f:
    data = json.load(f)

# Configure filters
IGNORE_HEADERS = {"Scenario Chosen"}

# By default, the script will look for the main formula for a row in Column F (index 5).
# We can define exceptions for sheets that have a different layout.
DEFAULT_VALUE_COLUMN = 5
VALUE_COLUMN_EXCEPTIONS = {
    "scenarios": 3  # For the 'scenarios' sheet, the value is in Column D (index 3)
}

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

def safe_name(value, allow_formulas=False) -> str:
    """Return a clean string name for a header cell."""
    s = "" if value is None else str(value).strip()
    # Skip formulas like "=+time_macro!R[1]C[-1]"
    if not allow_formulas and s.startswith("="):
        return ""
    return s

def disambiguate(name: str, existing: dict) -> str:
    """If name already exists in dict, append (2), (3), ..."""
    if name not in existing:
        return name
    i = 2
    while f"{name} ({i})" in existing:
        i += 1
    return f"{name} ({i})"

def col_num_to_letter(col: int) -> str:
    """Convert column number (1-based) to Excel-style letters."""
    letters = ""
    while col > 0:
        col, remainder = divmod(col - 1, 26)
        letters = chr(65 + remainder) + letters
    return letters

def r1c1_to_a1(r: int, c: int) -> str:
    """Convert absolute row/col indexes (1-based) to A1 cell reference."""
    return f"{col_num_to_letter(c)}{r}"

def load_existing_definitions_cache(path):
    """Loads existing metadata to create a cache of definitions and embeddings."""
    cache = {}
    if not os.path.exists(path):
        return cache
    try:
        with open(path, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
        
        for sheet_name, sheet_data in existing_data.items():
            for table_name, table_data in sheet_data.get("tables", {}).items():
                for row_name, row_data in table_data.get("rows", {}).items():
                    if "definition" in row_data:
                        cache_key = (sheet_name, table_name, row_name)
                        cache[cache_key] = {
                            "definition": row_data["definition"]                            
                        }
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not load or parse existing metadata for caching. Error: {e}")
    return cache

def main():
    """
    Loads raw cell data, parses tables and rows, finds formula dependencies,
    generates definitions and embeddings, and saves the complete metadata
    to a single JSON file.
    """
    sheets_dict = {}

    # Define output path early for caching
    output_path = os.path.join(os.path.dirname(input_path), "meta_data.json")

    # --- Setup for definitions and embeddings ---
    print("Initializing AI client model...")
    project_root = os.path.dirname(input_path)
    ai_client = get_ai_client(project_root)
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    print(f"Checking for existing data in {output_path} to build cache...")
    definitions_cache = load_existing_definitions_cache(output_path)
    print(f"Found {len(definitions_cache)} cached definitions.")

    if "worksheets" in data:
        for ws in data["worksheets"]:
            sheet_name = ws.get("name")
            if not sheet_name:
                continue

            cells = ws.get("cells", {})

            # Build fast lookups
            cell_map = {}              # (row, col) -> cell
            row_cols = defaultdict(set) # row -> set of columns present
            max_row = 0

            for _, cell in cells.items():
                r = cell.get("rowIndex")
                c = cell.get("columnIndex")
                if r is None or c is None:
                    continue
                cell_map[(r, c)] = cell
                row_cols[r].add(c)
                if r > max_row:
                    max_row = r

            # Collect headers: dict row -> sorted list of (col, name)
            headers_by_row = defaultdict(list)
            header_positions = []  # list of (row, col, name)

            for (r, c), cell in cell_map.items():
                fmt = cell.get("format", {})
                font = fmt.get("font", {})
                if fmt.get("backgroundColor") == "#3366FF" and font.get("color") == "#FFFFFF":
                    name = safe_name(cell.get("formulaR1C1"))
                    if not name or name in IGNORE_HEADERS:
                        continue
                    headers_by_row[r].append((c, name))
                    header_positions.append((r, c, name))

            # If no headers, still return empty tables for the sheet
            if not header_positions:
                sheets_dict[sheet_name] = {"tables": {}}
                continue

            # Sort headers for deterministic processing
            for r in headers_by_row:
                headers_by_row[r].sort(key=lambda x: x[0])  # by column
            header_positions.sort(key=lambda x: (x[0], x[1]))  # by row, then col

            # For height: precompute list of header rows
            header_rows_sorted = sorted(headers_by_row.keys())

            tables = {}

            for r, c, name in header_positions:
                # ---- HEIGHT (rows) ----
                next_header_row = None
                for hr in header_rows_sorted:
                    if hr > r:
                        next_header_row = hr
                        break

                if next_header_row is not None:
                    height = next_header_row - r
                else:
                    last_row_with_cells = max(row_cols.keys()) if row_cols else r
                    height = (last_row_with_cells - r + 1)

                if height < 1:
                    height = 1

                # ---- WIDTH (columns) ----
                table_start_row = r
                table_end_row = next_header_row if next_header_row is not None else max_row + 1
                
                max_col_in_table = c
                for row_idx in range(table_start_row, table_end_row):
                    if row_idx in row_cols and row_cols[row_idx]:
                        max_col_in_row = max(row_cols[row_idx])
                        if max_col_in_row > max_col_in_table:
                            max_col_in_table = max_col_in_row
                
                width = max_col_in_table - c + 1
                if width < 1:
                    width = 1

                # ---- EXTRACT ROW-LEVEL DATA AND DEPENDENCIES ----
                row_data = {}
                for current_r in range(table_start_row + 1, table_end_row):
                    row_name_cell = cell_map.get((current_r, 1))
                    row_name_val = safe_name(row_name_cell.get("formulaR1C1") if row_name_cell else None)

                    if not row_name_val:
                        continue

                    extra_info_cell = cell_map.get((current_r, 2))
                    extra_info_val = safe_name(extra_info_cell.get("formulaR1C1") if extra_info_cell else None)

                    value_col_index = VALUE_COLUMN_EXCEPTIONS.get(sheet_name, DEFAULT_VALUE_COLUMN)
                    
                    main_value_cell = cell_map.get((current_r, value_col_index))
                    main_value_formula = safe_name(main_value_cell.get("formulaR1C1") if main_value_cell else None, allow_formulas=True)

                    if main_value_cell:
                        cell_row = main_value_cell.get("rowIndex")
                        cell_col = main_value_cell.get("columnIndex")
                        a1_ref = r1c1_to_a1(cell_row + 1, cell_col + 1)
                    else:
                        a1_ref, cell_row, cell_col = None, None, None

                    # --- Get definition and embedding ---
                    definition = None                    
                    cache_key = (sheet_name, name, row_name_val) # sheet_name, table_name, row_name

                    if cache_key in definitions_cache:
                        cached_item = definitions_cache[cache_key]
                        definition = cached_item.get("definition")                       
                        # print(f"  - Using cached definition for '{row_name_val}'")
                    else:
                        print(f"  - Processing (new): '{row_name_val}' from sheet: '{sheet_name}', table: '{name}'")
                        definition = get_definition(ai_client, row_name_val, name, sheet_name)
                        if definition:
                            print(f"    -> Definition: {definition[:50]}...")                            
                        else:
                            print(f"    -> Failed to get definition for '{row_name_val}'. Skipping.")

                    # --- PARSE FORMULA DEPENDENCIES ---
                    dependencies = []
                    if main_value_formula and isinstance(main_value_formula, str) and main_value_formula.startswith("="):
                        if cell_row is not None and cell_col is not None:
                            absolute_refs = get_absolute_references(main_value_formula, cell_row, cell_col)
                            for dep in absolute_refs:
                                # If a reference has no sheet, it refers to the current sheet
                                dep_sheet = dep[0] if dep[0] else sheet_name
                                dependencies.append({"sheet": dep_sheet, "row": dep[1], "col": dep[2]})

                    row_item_data = {
                        "source_cell": a1_ref,
                        "R1C1": main_value_formula,
                        "extra info": extra_info_val,
                    }

                    if definition:
                        row_item_data["definition"] = definition
                    row_item_data['dependencies'] = dependencies

                    row_key = disambiguate(row_name_val, row_data)
                    row_data[row_key] = row_item_data

                key = disambiguate(name, tables)
                tables[key] = {
                    "row numbers": height,
                    "column numbers": width,
                    "rows": row_data
                }

            sheets_dict[sheet_name] = {"tables": tables}

    with open(output_path, "w", encoding='utf-8') as f:
        json.dump(sheets_dict, f, indent=2)

    print(f"✅ Metadata with dependencies saved to {output_path}")

if __name__ == "__main__":
    main()