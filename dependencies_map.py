import json
import os
import re
from formulas_extraction import get_absolute_references

def a1_to_coords(a1_ref: str):
    """
    Converts an A1-style cell reference string (e.g., "F13", "AA27")
    into a 0-indexed (row, column) tuple.
    """
    if not a1_ref:
        return None, None

    match = re.match(r"([A-Z]+)([0-9]+)", a1_ref.upper())
    if not match:
        return None, None

    col_str, row_str = match.groups()

    # Convert column letters to a 0-indexed number
    col_idx = 0
    for char in col_str:
        col_idx = col_idx * 26 + (ord(char) - ord('A') + 1)
    col_idx -= 1

    # Convert row string to 0-indexed number
    row_idx = int(row_str) - 1

    return row_idx, col_idx

def main():
    """
    Loads table data, parses formulas to find dependencies, and saves the enriched data.
    """
    # Define input and output paths relative to the script's location
    base_dir = os.path.dirname(__file__)
    input_path = os.path.join(base_dir, "sheet_name_results.json")
    output_path = os.path.join(base_dir, "dependencies_results.json")

    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Iterate through all sheets, tables, and rows to find and parse formulas
    for sheet_name, sheet_data in data.items():
        for table_name, table_data in sheet_data.get("tables", {}).items():
            for row_name, row_data in table_data.get("rows", {}).items():
                formula = row_data.get("R1C1")
                a1_ref = row_data.get("cell_name")

                dependencies = []
                if formula and a1_ref and isinstance(formula, str) and formula.startswith("="):
                    current_row, current_col = a1_to_coords(a1_ref)

                    if current_row is not None:
                        absolute_refs = get_absolute_references(formula, current_row, current_col)
                        for dep in absolute_refs:
                            dep_sheet = dep[0] if dep[0] else sheet_name
                            dependencies.append({"sheet": dep_sheet, "row": dep[1], "col": dep[2]})
                
                row_data["dependencies"] = dependencies

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

    print(f"✅ Dependency map created and saved to {output_path}")

if __name__ == "__main__":
    main()