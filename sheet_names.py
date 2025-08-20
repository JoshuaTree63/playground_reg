import json

# Specify the input and output file paths
input_file_path = r'D:\python projects\playground_reg\debug_20250819_225527_529016.json'
output_file_path = r'D:\python projects\playground_reg\sheet_name_results.json'

# Load the JSON file with UTF-8 encoding
with open(input_file_path, 'r', encoding='utf-8') as file:
    data = json.load(file)

# Extract the sheet names
sheet_names = [worksheet['name'] for worksheet in data['worksheets']]

# Create a dictionary for descriptions with sheet names as keys
descriptions = {sheet_name: "Add" for sheet_name in sheet_names}

# Set an example description for the first sheet (e.g., "Sheet1": "xxxx")
if sheet_names:  # Ensure there is at least one sheet
    descriptions[sheet_names[0]] = "xxxx"

# Save the descriptions dictionary directly to the JSON file
with open(output_file_path, 'w', encoding='utf-8') as file:
    json.dump(descriptions, file, indent=4)

print(f"Descriptions have been saved to {output_file_path}")