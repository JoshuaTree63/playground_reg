import json
import os

# Path to your existing JSON
input_path = "/Users/joshualevi/git_projects/playground_reg/debug_20250819_225527_529016.json"

# Load JSON
with open(input_path, "r") as f:
    data = json.load(f)

# Extract sheet names and build dict
sheets_dict = {}
if "worksheets" in data:
    for ws in data["worksheets"]:
        if "name" in ws:
            sheets_dict[ws["name"]] = {}  # empty dict for each sheet

# Define output path
output_path = os.path.join(
    os.path.dirname(input_path),
    "sheets_list.json"
)

# Save to new JSON file
with open(output_path, "w") as f:
    json.dump(sheets_dict, f, indent=2)

print(f"✅ New JSON with sheet names saved to {output_path}")