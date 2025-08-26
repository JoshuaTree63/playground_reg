import re

formula = "=-(scenarios!R39C4+scenarios!R40C4)*debt!R[-5]C*time_macro!R[7]C[-1]+'Annual CF'!RC * 'Time&Macro'!R16C-RC*R[-15]C3"

def get_all_references(formula):
    """
    Finds all R1C1-style cell references in a formula string using regex.
    Returns a list of tuples, where each tuple is (sheet, row_str, col_str).
    """
    pattern = r"(?:(?P<sheet>'[^']+'|\w+)!)?R(?P<row>(?:\[-?\d+\])|\d*)C(?P<col>(?:\[-?\d+\])|\d*)"
    references = re.findall(pattern, formula)
    return references

def convert_reference_to_absolute(ref, current_row, current_col):
    """
    Converts a single R1C1 reference tuple to absolute 0-indexed coordinates.
    ref is a tuple: (sheet, row_str, col_str)
    """
    sheet, row, col = ref
    # Clean up sheet name by removing single quotes if they exist
    sheet = sheet.strip("'")

    if row.startswith('['):
        row_offset = int(row[1:-1])
        abs_row = current_row + row_offset
    elif row == '':
        abs_row = current_row
    else:
        abs_row = int(row) - 1  # Convert to 0-based index

    if col.startswith('['):
        col_offset = int(col[1:-1])
        abs_col = current_col + col_offset
    elif col == '':
        abs_col = current_col
    else:
        abs_col = int(col) - 1  # Convert to 0-based index

    return (sheet, abs_row, abs_col)

def get_absolute_references(formula, current_row, current_col):
    """
    Parses a formula to find all cell references and convert them to absolute coordinates.
    """
    references = get_all_references(formula)
    absolute_references = [convert_reference_to_absolute(ref, current_row, current_col) for ref in references]
    return absolute_references

def main():
    current_row = 10  # Example current row (0-based)
    current_col = 5   # Example current column (0-based)

    references = get_all_references(formula)
    absolute_references = get_absolute_references(formula, current_row, current_col)

    for ref, abs_ref in zip(references, absolute_references):
        print(f"Original: {ref} -> Absolute: {abs_ref}")


if __name__ == "__main__":
    main()