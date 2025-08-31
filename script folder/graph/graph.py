import json
import os

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

# --- Recursive function to get all dependencies ---
def get_all_dependencies(cell, graph, visited):
    """Recursively finds all dependencies for a cell using DFS."""
    if cell in visited:
        return []
    visited.add(cell)
    all_deps = []
    # Get direct dependencies and add them to the list
    direct_deps = graph.get(cell, [])
    for dep in direct_deps:
        all_deps.append(dep)
        # Recursively find dependencies of the dependency
        all_deps.extend(get_all_dependencies(dep, graph, visited))
    return all_deps

def build_dependency_graph(meta_data):
    """Builds direct and in-depth dependency graphs from Excel metadata JSON."""

    # --- Direct dependency graph ---
    graph = {}
    for sheet_name, sheet in meta_data.items():
        if not isinstance(sheet, dict):
            continue
        for table_name, table in sheet.get("tables", {}).items():
            if not isinstance(table, dict):
                continue
            for row_id, row in table.get("rows", {}).items():
                cell_a1 = row.get("cell_name")
                if not cell_a1:
                    continue
                
                # Standardize all cell names to 'SheetName!A1' format
                full_cell_name = f"{sheet_name}!{cell_a1}"
                graph[full_cell_name] = []
                
                for dep in row.get("dependencies", []):
                    # meta_data has 0-indexed row/col, r1c1_to_a1 needs 1-indexed
                    dep_a1 = r1c1_to_a1(dep['row'] + 1, dep['col'] + 1)
                    dep_cell_name = f"{dep['sheet']}!{dep_a1}"
                    graph[full_cell_name].append(dep_cell_name)

    # --- Build in-depth dependency graph ---
    in_depth_graph = {}
    for cell in graph.keys():
        visited = set()
        # Use set to remove duplicates from the final dependency list
        in_depth_graph[cell] = sorted(list(set(get_all_dependencies(cell, graph, visited))))

    return in_depth_graph


if __name__ == "__main__":
    # Input & output paths
    base_dir = "/Users/joshualevi/git_projects/playground_reg"
    meta_data_path = os.path.join(base_dir, "meta_data.json")
    output_dir = os.path.join(base_dir, "graph")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "dependency_graph.json")

    # Load metadata
    with open(meta_data_path, "r", encoding="utf-8") as f:
        meta_data = json.load(f)

    # Build graph
    dependency_graph = build_dependency_graph(meta_data)

    # Save output JSON
    with open(output_path, "w") as f:
        json.dump(dependency_graph, f, indent=2)

    print(f"✅ Dependency graph saved to: {output_path}")