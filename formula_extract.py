import json

# Specify the input and output file paths
input_file_path = r'D:\python projects\playground_reg\debug_20250818_225646_965473.json'
output_file_path = r'D:\python projects\playground_reg\formula_extract_results.json'

# Load the JSON file with UTF-8 encoding
with open(input_file_path, 'r', encoding='utf-8') as file:
    data = json.load(file)

# Define min columnIndex per sheet (add more sheets as needed, e.g., for cashflow sheets)
min_column_per_sheet = {
    "Summary": 7,  # For Summary, only columns >=7 (H+) to get ratios/financial titles
    # Example: "Cashflow": 1,  # Uncomment and add if you have a "Cashflow" sheet with titles in column B
    # "OtherSheet": 1,
    "default": 0   # For other sheets like Sheet1/Terminal Value, include from column 0+
}

# Initialize a dictionary to store raw names by sheet
raw_names_by_sheet = {}

# Iterate through each worksheet
for worksheet in data['worksheets']:
    sheet_name = worksheet['name']
    raw_names = []
    
    # Get the min column for this sheet
    min_col = min_column_per_sheet.get(sheet_name, min_column_per_sheet["default"])
    
    # Iterate through cells in the worksheet
    for cell_key, cell_data in worksheet['cells'].items():
        # Check if the cell has the specified format and column >= min_col
        if (cell_data.get('format', {}).get('font', {}).get('color') == '#000000' and
            cell_data.get('format', {}).get('backgroundColor') == '#FFFFFF' and
            cell_data['columnIndex'] >= min_col):
            # Check if formulaR1C1 exists and is a string, and not a formula (does not start with '=')
            if 'formulaR1C1' in cell_data and isinstance(cell_data['formulaR1C1'], str) and not cell_data['formulaR1C1'].startswith('='):
                raw_names.append(cell_data['formulaR1C1'])
    
    # Store the raw names for this sheet
    raw_names_by_sheet[sheet_name] = raw_names

# Save the results to a new JSON file
with open(output_file_path, 'w', encoding='utf-8') as file:
    json.dump(raw_names_by_sheet, file, indent=4)

print(f"Filtered raw names have been saved to {output_file_path}")