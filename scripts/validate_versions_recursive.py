import os
import toml
import json
import sys

# Specify the root directory to search from
root_dir = "../modpacks/1.21.4/."

def find_files(root, filenames):
    """Recursively find specified files in a directory."""
    found_files = {filename: [] for filename in filenames}
    for dirpath, _, files in os.walk(root):
        for filename in filenames:
            if filename in files:
                found_files[filename].append(os.path.join(dirpath, filename))
    return found_files

def validate_versions(pack_path, isxander_path):
    """Validate versions in a pair of pack.toml and isxander-main-menu-credits.json."""
    # Read pack.toml
    with open(pack_path, "r") as f:
        pack_data = toml.load(f)

    # Extract the version from pack.toml
    pack_version = pack_data.get("version")
    if not pack_version:
        print(f"Error: Version not found in {pack_path}!")
        return False

    # Read isxander-main-menu-credits.json
    with open(isxander_path, "r") as f:
        isxander_data = json.load(f)

    # Extract the release version from isxander-main-menu-credits.json
    isxander_version = None
    if "main_menu" in isxander_data and "bottom_right" in isxander_data["main_menu"]:
        for item in isxander_data["main_menu"]["bottom_right"]:
            if "text" in item and "Core Optimized release" in item["text"]:
                isxander_version = item["text"].split("release ")[-1]
                break

    if not isxander_version:
        print(f"Error: Release version not found in {isxander_path}!")
        return False

    # Compare the versions
    if pack_version != isxander_version:
        print(f"Error: Versions do not match in:")
        print(f" - pack.toml: {pack_path} (version: {pack_version})")
        print(f" - isxander-main-menu-credits.json: {isxander_path} (version: {isxander_version})")
        return False

    print(f"Success: Versions match in {pack_path} and {isxander_path}!")
    return True

# Find all relevant files
files_to_check = find_files(root_dir, ["pack.toml", "isxander-main-menu-credits.json"])

# Pair up matching pack.toml and isxander-main-menu-credits.json in the same folder
validation_results = []
for pack_path in files_to_check["pack.toml"]:
    folder = os.path.dirname(pack_path)
    isxander_path = os.path.join(folder, "isxander-main-menu-credits.json")
    if isxander_path in files_to_check["isxander-main-menu-credits.json"]:
        result = validate_versions(pack_path, isxander_path)
        validation_results.append(result)

# Check if all validations passed
if all(validation_results):
    print("All version validations passed!")
    sys.exit(0)
else:
    print("Some version validations failed!")
    sys.exit(1)
