import json
import os
import shutil
import zipfile

def convert_modrinth_to_curseforge(modrinth_path, curseforge_path):
    # Load the modrinth modpack
    with open(os.path.join(modrinth_path, 'index.toml'), 'r') as file:
        modrinth_modpack = file.read()

    # Parse the modrinth modpack
    modrinth_modpack = toml.loads(modrinth_modpack)

    # Create the curseforge modpack structure
    curseforge_modpack = {
        "manifestType": "minecraftModpack",
        "manifestVersion": 1,
        "name": modrinth_modpack['name'],
        "version": modrinth_modpack['version'],
        "author": modrinth_modpack['author'],
        "minecraft": {
            "version": modrinth_modpack['minecraft']['version'],
            "modLoaders": [
                {
                    "id": modrinth_modpack['minecraft']['modLoaders'][0]['id'],
                    "primary": True
                }
            ]
        },
        "files": [],
        "overrides": "overrides"
    }

    # Add the mods to the curseforge modpack
    for mod in modrinth_modpack['mods']:
        curseforge_modpack['files'].append({
            "projectID": mod['projectID'],
            "fileID": mod['fileID'],
            "required": mod['required']
        })

    # Save the curseforge modpack
    with open(os.path.join(curseforge_path, 'manifest.json'), 'w') as file:
        json.dump(curseforge_modpack, file, indent=4)

    # Copy the overrides
    shutil.copytree(os.path.join(modrinth_path, 'overrides'), os.path.join(curseforge_path, 'overrides'))

    # Create the zip file
    with zipfile.ZipFile(os.path.join(curseforge_path, f"{curseforge_modpack['name']}-{curseforge_modpack['version']}.zip"), 'w') as zipf:
        for root, dirs, files in os.walk(curseforge_path):
            for file in files:
                zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), curseforge_path))

if __name__ == "__main__":
    modrinth_path = '/path/to/modrinth/modpack'
    curseforge_path = '/path/to/curseforge/modpack'
    convert_modrinth_to_curseforge(modrinth_path, curseforge_path)