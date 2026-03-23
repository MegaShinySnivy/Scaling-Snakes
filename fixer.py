import os

def add_unlock_to_file(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()

    # Add the unlock line with double indentation directly to the last line
    lines.append("    unlock: true\n")

    # Write the updated content back to the file
    with open(file_path, 'w') as f:
        f.writelines(lines)

def find_volsync_files(root_dir):
    # Traverse the repository directory tree to find volsyncconf.yaml files
    for dirpath, _, filenames in os.walk(root_dir):
        if "volsyncconf.yaml" in filenames:
            file_path = os.path.join(dirpath, "volsyncconf.yaml")
            add_unlock_to_file(file_path)
            print(f"Updated: {file_path}")

# Provide the path to your Git repository root
repo_root = "/home/rex/git/Scaling-Snakes"
find_volsync_files(repo_root)
