import os

def print_mermaid_tree(start_path='.'):
    print("```mermaid")
    print("graph TD")
    node_id = 0
    path_to_id = {}

    for root, dirs, files in os.walk(start_path):
        # Exclude venv and __pycache__ directories
        dirs[:] = [d for d in dirs if d not in ("venv", "__pycache__")]

        rel_root = os.path.relpath(root, start_path)
        if rel_root == ".":
            parent_id = "ROOT"
            print(f'{parent_id}["{os.path.basename(os.path.abspath(start_path))}"]')
        else:
            parent_dir = os.path.dirname(rel_root)
            if parent_dir == "":
                parent_id = "ROOT"
            else:
                parent_id = path_to_id[parent_dir]
            print(f'{parent_id} --> node{node_id}["{os.path.basename(root)}"]')
            parent_id = f"node{node_id}"
            node_id += 1
        path_to_id[rel_root] = parent_id

        for file in files:
            # Exclude files in __pycache__ and venv
            if file.endswith(".pyc") or file == "__pycache__":
                continue
            file_id = f"node{node_id}"
            print(f'{parent_id} --> {file_id}["{file}"]')
            node_id += 1

    print("```")
if __name__ == "__main__":
    print_mermaid_tree(".")