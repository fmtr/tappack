import io
import json
import zipfile
from pathlib import Path

import click
import requests


class Packager:
    def __init__(self, module_path):
        self.module_path = Path(module_path).absolute().resolve()
        self.dependencies_path = self.module_path / 'dependencies.json'
        self.dependencies = None
        self.paths = None

    def download_dependencies(self):
        # Load the contents of dependencies.json into a dictionary
        self.dependencies = json.loads(self.dependencies_path.read_text())

        # Loop through each key-value pair in the dependencies dictionary
        for name, url in self.dependencies.items():
            # Download the ZIP file from the URL and extract its contents into a subfolder with the same name as the key
            response = requests.get(url)
            with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
                (self.module_path / name).mkdir(parents=True, exist_ok=True)
                zip_file.extractall(self.module_path / name)

    def find_submodules(self):
        # Find all directory paths within the "module" subdirectory
        self.paths = []
        for path in self.module_path.rglob('*'):
            if path.is_dir():
                # Make the path relative to the "module" subdirectory
                rel_path = path.relative_to(self.module_path)
                self.paths.append(str(rel_path))

    def write_paths(self):
        # Write the directory paths to a file called paths.json within the "module" subdirectory
        output_file = self.module_path / 'paths.json'
        output_file.write_text(json.dumps(self.paths))

    def store_module(self, tapp_path):
        # Create a ZIP file containing the entire module directory structure
        tapp_path = Path(tapp_path).absolute().resolve()
        with zipfile.ZipFile(tapp_path, 'w', compression=zipfile.ZIP_STORED) as zip_file:
            for path in self.module_path.glob('**/*'):
                if path.is_file():
                    rel_path = path.relative_to(self.module_path)
                    zip_file.write(path, rel_path)

    def package(self, tapp_path):
        # Download the dependencies
        self.download_dependencies()

        # Find the directory paths
        self.find_submodules()

        # Write the directory paths to the output file
        self.write_paths()

        # Create a ZIP file containing the entire module directory structure
        self.store_module(tapp_path)


@click.command()
@click.argument('module_path', metavar='PATH')
@click.argument('tapp_path', metavar='PATH')
def main(module_path, tapp_path):
    packager = Packager(module_path)
    packager.package(tapp_path)


if __name__ == '__main__':
    main()
