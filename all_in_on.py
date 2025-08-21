import json
import os

# Path to your existing JSON
input_path = "/Users/joshualevi/git_projects/playground_reg/debug_20250819_225527_529016.json"

# Load JSON
with open(input_path, "r") as f:
    data = json.load(f)

sheets_dict = {}

# Words/phrases to ignore as table headers
ignore_headers = {"Scenario Chosen"}

# Iterate worksheets
if "worksheets" in data:
    for ws in data["worksheets"]:
        if "name" in ws:
            sheet_name = ws["name"]
            tables = {}

            # Look through each cell for table headers
            for addr, cell in ws.get("cells", {}).items():
                fmt = cell.get("format", {})
                font = fmt.get("font", {})

                # Detect header by style
                if fmt.get("backgroundColor") == "#3366FF" and font.get("color") == "#FFFFFF":
                    raw_value = cell.get("formulaR1C1", "")

                    # Convert to string safely
                    table_name = str(raw_value).strip()

                    # Skip invalid names
                    if not table_name:
                        continue
                    if table_name in ignore_headers:
                        continue
                    if table_name.startswith("="):  # skip formulas
                        continue

                    # Add to table dict
                    tables[table_name] = {}

            sheets_dict[sheet_name] = {"tables": tables}

# Define output path
output_path = os.path.join(
    os.path.dirname(input_path),
    "sheets_list.json"
)

# Save to new JSON file
with open(output_path, "w") as f:
    json.dump(sheets_dict, f, indent=2)

print(f"✅ New JSON with sheet names + clean table names saved to {output_path}")