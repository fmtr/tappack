import io
import json
import zipfile
from pathlib import Path

import click
import requests
import yaml

ENCODING = 'utf-8'

class Packager:
    def __init__(self, module_path):
        module_path = Path(module_path or '.')
        self.module_path = Path(module_path).absolute().resolve()
        self.manifest_path = self.module_path / 'tappack.yaml'
        self.manifest = yaml.safe_load(self.manifest_path.read_text())
        self.name = self.manifest['name']
        self.paths = None

    def download_dependencies(self):
        # Load the contents of dependencies.json into a dictionary

        dependencies = self.manifest.get('dependencies', {})
        # Loop through each key-value pair in the dependencies dictionary
        for name, url in dependencies.items():
            # Download the ZIP file from the URL and extract its contents into a subfolder with the same name as the key

            print(f'Downloading dependency "{name}" from "{url}"...')
            response = requests.get(url)

            with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
                (self.module_path / name).mkdir(parents=True, exist_ok=True)
                zip_file.extractall(self.module_path / name)

    def find_submodules(self):
        # Find all directory paths within the "module" subdirectory
        self.paths = []
        for path in self.module_path.rglob('*'):

            if not path.is_dir():
                continue

            if (list(path.glob('*.be')) or list(path.glob('*.bec'))):
                # Make the path relative to the "module" subdirectory
                rel_path = path.relative_to(self.module_path)
                self.paths.append(str(rel_path))
            else:
                print(f'Not adding directory to paths, as it contains no Berry code: "{path}"')

    def write_paths(self):
        # Write the directory paths to a file called paths.json within the "module" subdirectory
        output_file = self.module_path / 'paths.json'
        output_file.write_text(json.dumps(self.paths))

    def store_module(self, tapp_path):
        # Create a ZIP file containing the entire module directory structure
        tapp_path = Path(tapp_path).absolute().resolve()
        with zipfile.ZipFile(tapp_path, 'w', compression=zipfile.ZIP_STORED) as zip_file:

            autoexec = self.get_autoexec()
            print(f'Writing generated "autoexec.be" to archive...')
            zip_file.writestr('autoexec.be', autoexec.encode(ENCODING))

            for path in self.module_path.glob('**/*'):

                if path.is_dir():
                    continue

                rel_path = path.relative_to(self.module_path)
                print(f'Writing file "{rel_path}" to archive...')
                zip_file.write(path, rel_path)

        print(f'Wrote output to "{tapp_path}"')

    def package(self, tapp_path=None):

        tapp_path = Path(tapp_path or (self.module_path / self.name).with_suffix('.tapp'))
        tapp_path = tapp_path.absolute().resolve()
        # Download the dependencies
        self.download_dependencies()

        # Find the directory paths
        self.find_submodules()

        # Write the directory paths to the output file
        # self.write_paths()

        # Create a ZIP file containing the entire module directory structure
        self.store_module(tapp_path)

    def get_autoexec(self):
        path = Path(__file__).absolute().resolve().parent / 'autoexec.be.template'
        text = path.read_text(encoding=ENCODING)

        replacements = {'paths': repr(self.paths), 'module_name': self.name}

        for key, replacement in replacements.items():
            text = text.replace(f'{{{key}}}', replacement)

        print(f'Added paths to autoexec.be: {self.paths}')

        return text


@click.command()
@click.option('-m', '--module-path', metavar='PATH')
@click.option('-t', '--tapp-path', metavar='PATH')
def main(module_path, tapp_path):
    packager = Packager(module_path)
    packager.package(tapp_path)


if __name__ == '__main__':
    main()
