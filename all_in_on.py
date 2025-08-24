import json
import os
from collections import defaultdict

# Path to your existing JSON
input_path = "/Users/joshualevi/git_projects/playground_reg/debug_20250819_225527_529016.json"

# Load JSON
with open(input_path, "r") as f:
    data = json.load(f)

# Configure filters
IGNORE_HEADERS = {"Scenario Chosen"}

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
            # Find the next header row BELOW this row to determine the table's boundary
            next_header_row = None
            for hr in header_rows_sorted:
                if hr > r:
                    next_header_row = hr
                    break

            if next_header_row is not None:
                height = next_header_row - r
            else:
                # No next header row: extend to the last row that has any cell
                last_row_with_cells = max(row_cols.keys()) if row_cols else r
                height = (last_row_with_cells - r + 1)

            if height < 1:  # safety clamp
                height = 1

            # ---- WIDTH (columns) ----
            # Find the maximum column index within all rows of this table
            table_start_row = r
            table_end_row = next_header_row if next_header_row is not None else max_row + 1
            
            max_col_in_table = c  # Start with the header's own column
            for row_idx in range(table_start_row, table_end_row):
                if row_idx in row_cols and row_cols[row_idx]:
                    max_col_in_row = max(row_cols[row_idx])
                    if max_col_in_row > max_col_in_table:
                        max_col_in_table = max_col_in_row
            
            width = max_col_in_table - c + 1
            if width < 1:
                width = 1

            # ---- EXTRACT ROW-LEVEL DATA ----
            row_data = {}
            for current_r in range(table_start_row + 1, table_end_row):
                # Get row name from col B (index 1)
                row_name_cell = cell_map.get((current_r, 1))
                row_name_val = safe_name(row_name_cell.get("formulaR1C1") if row_name_cell else None)

                if not row_name_val:
                    continue

                row_item_data = {}

                # "extra info" from column C (index 2)
                extra_info_cell = cell_map.get((current_r, 2))
                row_item_data["extra info"] = safe_name(extra_info_cell.get("formulaR1C1") if extra_info_cell else None)

                # "R1C1" from column D (index 3)
                r1c1_cell = cell_map.get((current_r, 3))
                row_item_data["R1C1"] = safe_name(
                    r1c1_cell.get("formulaR1C1") if r1c1_cell else None, allow_formulas=True
                )
                
                row_key = disambiguate(row_name_val, row_data)
                row_data[row_key] = row_item_data

            # Ensure unique key if same name appears multiple times
            key = disambiguate(name, tables)
            tables[key] = {
                "row numbers": height,
                "column numbers": width,
                "rows": row_data
            }

        sheets_dict[sheet_name] = {"tables": tables}

# Define output path
output_path = os.path.join(os.path.dirname(input_path), "sheet_name_results.json")

with open(output_path, "w") as f:
    json.dump(sheets_dict, f, indent=2)

print(f"✅ New JSON with table dimensions and row data saved to {output_path}")