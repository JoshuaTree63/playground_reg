import json

# Specify the input and output file paths
input_file_path = r'D:\python projects\playground_reg\debug_20250819_225527_529016.json'
output_file_path = r'D:\python projects\playground_reg\raw_name_results.json'

# Load the JSON file with UTF-8 encoding
with open(input_file_path, 'r', encoding='utf-8') as file:
    data = json.load(file)

# Initialize a dictionary to store raw names by sheet
raw_names_by_sheet = {}

# Iterate through each worksheet
for worksheet in data['worksheets']:
    sheet_name = worksheet['name']
    raw_names = []
    
    # Iterate through cells in the worksheet
    for cell_key, cell_data in worksheet['cells'].items():
        # Check if the cell is in columnIndex: 1
        if cell_data.get('columnIndex') == 1:
            # Check if formulaR1C1 exists, is a string, and is not a formula
            if 'formulaR1C1' in cell_data and isinstance(cell_data['formulaR1C1'], str) and not cell_data['formulaR1C1'].startswith('='):
                raw_names.append(cell_data['formulaR1C1'])
    
    # Store the raw names for this sheet (only if non-empty to avoid clutter)
    if raw_names:
        raw_names_by_sheet[sheet_name] = raw_names

# Save the results to a new JSON file
with open(output_file_path, 'w', encoding='utf-8') as file:
    json.dump(raw_names_by_sheet, file, indent=4)

print(f"Non-formula titles from columnIndex: 1 have been saved to {output_file_path}")