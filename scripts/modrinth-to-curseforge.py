import json
import os
import zipfile
import tomli
import requests
import shutil
from typing import Dict, List, Optional

class ModrinthToCurseforge:
    def __init__(self, mrpack_path: str, output_path: str):
        self.mrpack_path = mrpack_path
        self.output_path = output_path
        self.temp_dir = "temp_mrpack_extract"
        self.modrinth_data = None
        self.curseforge_manifest = {
            "minecraft": {
                "version": "",
                "modLoaders": []
            },
            "manifestType": "minecraftModpack",
            "manifestVersion": 1,
            "name": "",
            "version": "1.0.0",
            "author": "",
            "files": [],
            "overrides": "overrides"
        }
    
    def extract_mrpack(self) -> None:
        """Extract the .mrpack file (which is a zip file)"""
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
        
        with zipfile.ZipFile(self.mrpack_path, 'r') as zip_ref:
            zip_ref.extractall(self.temp_dir)

    def load_modrinth_data(self) -> None:
        """Load and parse the index.toml file"""
        toml_path = os.path.join(self.temp_dir, "modrinth.index.json")
        if os.path.exists(toml_path):
            with open(toml_path, "r") as f:
                self.modrinth_data = json.load(f)
        else:
            toml_path = os.path.join(self.temp_dir, "index.toml")
            if not os.path.exists(toml_path):
                raise FileNotFoundError(f"Could not find index.toml in {self.temp_dir}")
                
            with open(toml_path, "r", encoding='utf-8') as f:
                content = f.read()
                self.modrinth_data = tomli.loads(content)
    
    def get_curseforge_id(self, modrinth_project_id: str) -> Optional[int]:
        """Get CurseForge project ID using Modrinth's API"""
        try:
            response = requests.get(f"https://api.modrinth.com/v2/project/{modrinth_project_id}")
            data = response.json()
            
            if "project_ids" in data:
                for platform, id in data["project_ids"].items():
                    if platform.lower() == "curseforge":
                        return int(id)
            return None
        except Exception as e:
            print(f"Error getting CurseForge ID for {modrinth_project_id}: {str(e)}")
            return None

    def convert_minecraft_info(self) -> None:
        """Convert Minecraft version and loader information"""
        # Debug print to see the structure
        print("Modrinth data structure:", self.modrinth_data)
        
        try:
            # Most TOML files have a "minecraft" key for version
            if "minecraft" in self.modrinth_data:
                self.curseforge_manifest["minecraft"]["version"] = self.modrinth_data["minecraft"]
            # Fallback to other possible structures
            elif "game" in self.modrinth_data and isinstance(self.modrinth_data["game"], dict):
                self.curseforge_manifest["minecraft"]["version"] = self.modrinth_data["game"]["version"]
            else:
                print("Warning: Could not determine Minecraft version")
                self.curseforge_manifest["minecraft"]["version"] = "unknown"

            # Convert loader information
            loader_map = {
                "fabric": {"id": "fabric-loader", "primary": True},
                "forge": {"id": "forge", "primary": True},
                "quilt": {"id": "quilt-loader", "primary": True}
            }
            
            # Try to find loader in different possible locations
            loader = None
            if "modloader" in self.modrinth_data:
                loader = self.modrinth_data["modloader"].lower()
            elif "game" in self.modrinth_data and isinstance(self.modrinth_data["game"], dict):
                if "modloader" in self.modrinth_data["game"]:
                    loader = self.modrinth_data["game"]["modloader"].lower()
            
            if loader and loader in loader_map:
                self.curseforge_manifest["minecraft"]["modLoaders"].append(loader_map[loader])
            
        except Exception as e:
            print(f"Error in convert_minecraft_info: {str(e)}")
            print("Modrinth data:", self.modrinth_data)
    
    def convert_mods(self) -> None:
        """Convert mod information from Modrinth to CurseForge format"""
        try:
            files = []
            if "files" in self.modrinth_data:
                files = self.modrinth_data["files"]
            elif "mods" in self.modrinth_data:
                files = self.modrinth_data["mods"]
            
            for mod in files:
                if isinstance(mod, dict):
                    project_id = mod.get("project_id", mod.get("id"))
                    if project_id:
                        curseforge_id = self.get_curseforge_id(project_id)
                        if curseforge_id:
                            mod_data = {
                                "projectID": curseforge_id,
                                "fileID": 0,
                                "required": True
                            }
                            self.curseforge_manifest["files"].append(mod_data)
                        else:
                            print(f"Warning: Could not find CurseForge ID for mod {project_id}")
        except Exception as e:
            print(f"Error in convert_mods: {str(e)}")
            print("Modrinth data:", self.modrinth_data)

    def setup_output_structure(self) -> None:
        """Create the output directory structure"""
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)
        
        overrides_dir = os.path.join(self.output_path, "overrides")
        if not os.path.exists(overrides_dir):
            os.makedirs(overrides_dir)
        
        overrides_source = os.path.join(self.temp_dir, "overrides")
        if os.path.exists(overrides_source):
            shutil.copytree(overrides_source, overrides_dir, dirs_exist_ok=True)

    def cleanup(self) -> None:
        """Clean up temporary files"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def convert(self) -> None:
        """Main conversion process"""
        try:
            self.extract_mrpack()
            self.load_modrinth_data()
            
            # Set basic information
            self.curseforge_manifest["name"] = (
                self.modrinth_data.get("name", "Converted Modpack")
                if isinstance(self.modrinth_data, dict)
                else "Converted Modpack"
            )
            
            # Convert Minecraft and loader information
            self.convert_minecraft_info()
            
            # Convert mods
            self.convert_mods()
            
            # Setup output structure
            self.setup_output_structure()
            
            # Save the CurseForge manifest
            output_file = os.path.join(self.output_path, "manifest.json")
            with open(output_file, "w") as f:
                json.dump(self.curseforge_manifest, f, indent=4)
            
            print(f"Conversion completed. Manifest saved to {output_file}")
        finally:
            self.cleanup()

def main():
    # Example usage
    converter = ModrinthToCurseforge(
        mrpack_path="./CoreOptimized-1.1.4-beta.1.mrpack",
        output_path="./curseforge_pack"
    )
    converter.convert()

if __name__ == "__main__":
    main()