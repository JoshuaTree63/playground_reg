import json
import os
from collections import defaultdict

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

def main():
    """
    Loads raw cell data, parses tables and rows, finds formula dependencies,
    and saves the complete metadata to a single JSON file.
    """
    sheets_dict = {}

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
                        "cell_name": a1_ref,      
                        "R1C1": main_value_formula,
                        "extra info": extra_info_val,
                        "dependencies": dependencies
                    }
                    
                    row_key = disambiguate(row_name_val, row_data)
                    row_data[row_key] = row_item_data

                key = disambiguate(name, tables)
                tables[key] = {
                    "row numbers": height,
                    "column numbers": width,
                    "rows": row_data
                }

            sheets_dict[sheet_name] = {"tables": tables}

    # Define output path
    output_path = os.path.join(os.path.dirname(input_path), "meta_data.json")

    with open(output_path, "w", encoding='utf-8') as f:
        json.dump(sheets_dict, f, indent=2)

    print(f"✅ Metadata with dependencies saved to {output_path}")

if __name__ == "__main__":
    main()