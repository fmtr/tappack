import io
import logging
import zipfile
from pathlib import Path

import requests
import yaml

from tappack.constants import ENCODING, NAME_MANIFEST


class Source:

    def iter_files(self):
        raise NotImplemented()


class LocalPath(Source):

    def __init__(self, path, name=None, channel_id=None):

        self.channel_id = channel_id
        self.path = Path(path).resolve().absolute()

        if not self.path.exists():
            raise ValueError(f'Path "{self.path}" does not exist.')

        if not self.path.is_dir():
            raise ValueError(f'Path "{self.path}" is not a directory.')

        self.path_manifest = self.path / NAME_MANIFEST
        if self.path_manifest.exists():
            self.manifest = yaml.safe_load(self.path_manifest.read_text())
            self.name = name or self.manifest['name']
        else:
            if not name:
                self.name = self.path.name
                msg = f'No manifest found in directory "{self.path}". ' \
                      f'Will be packaged as "{self.name}" without dependencies'
                logging.warning(msg)

            self.manifest = {}

    def iter_files(self, prefix=None):
        """

        Generator that recursively iterates any files in the specified path, then any files in any sub-dependencies,
        passing down the current path prefix, plus the name of the dependency. This yields tuples containing the
        relative path of each file paired with the file data as bytes.

        """

        print(f'Iterating dependency in path "{self.path}"...')

        prefix = Path(prefix or '.')

        for path in self.path.rglob('*'):
            if path.is_dir():
                continue

            file_bytes = path.read_bytes()
            path = path.relative_to(self.path)

            if prefix:
                path = Path(prefix) / path
            yield path, file_bytes

        for name, dept in self.get_dependencies():
            yield from dept.iter_files(prefix / name)

    @staticmethod
    def get_submodule_paths(file_data):

        paths = {
            path.parent
            for path in file_data
            if path.suffix in {'.be', '.bec'} and path.parent != Path('.')
        }
        return paths



    def generate_autoexec(self, file_data):

        paths = self.get_submodule_paths(file_data)
        paths = [str(path) for path in paths]

        path = Path(__file__).absolute().resolve().parent / 'autoexec.be.template'
        text = path.read_text(encoding=ENCODING)

        replacements = {'paths': repr(paths), 'module_name': self.name}

        for key, replacement in replacements.items():
            text = text.replace(f'{{{key}}}', replacement)

        print(f'Added submodule paths to autoexec.be: {paths}')

        return text

    def get_dependencies(self):

        class_map = {
            LocalPath.__name__: LocalPath,
            URL.__name__: URL,
        }

        for name, data in self.manifest.copy().get('dependencies', {}).items():

            if type(data) is str:
                data = {'.type': 'URL', 'url': data}

            if self.channel_id in (channels := data.get('.channels', {})):
                data = channels[self.channel_id]

            class_name = data.pop('.type', None)
            source_class = class_map.get(class_name)
            if source_class is None:
                raise ValueError(f"Invalid object type: {class_name}")
            data = data | {'name': name, 'channel_id': self.channel_id}
            data = {key: value for key, value in data.items() if not key.startswith('.')}
            source = source_class(**data)
            yield name, source

    def build_archive(self):
        # Create a ZIP (tapp) file containing the entire module directory structure
        file_data = dict(self.iter_files())

        file_data_autoexec = {Path('autoexec.be'): self.generate_autoexec(file_data).encode(ENCODING)}
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_STORED) as zip_file:
            for path, file_bytes in (file_data_autoexec | file_data).items():
                print(f'Writing file "{path}" ({len(file_bytes)} bytes) to archive...')
                zip_file.writestr(str(path), file_bytes)

        return buffer.getvalue()

    def write(self, path_tapp):
        path_tapp = Path(path_tapp or (Path('.') / self.name).with_suffix('.tapp')).absolute().resolve()
        archive_bytes = self.build_archive()
        print(f'Writing output archive ({len(archive_bytes)} bytes) to "{path_tapp}"...')


class URL(Source):

    def __init__(self, name, url, channel_id=None):
        self.name = name
        self.url = url

    def get_url(self):
        return self.url

    def get_content(self):
        print(f'Downloading dependency "{self.name}" from "{self.url}"...')
        response = requests.get(self.get_url())
        return response.content

    def iter_files(self, prefix=None):
        prefix = Path(prefix or '.')

        content = self.get_content()

        with zipfile.ZipFile(io.BytesIO(content)) as zip_file:
            for info in zip_file.filelist:
                data = zip_file.read(info.filename)
                path = prefix / info.filename
                yield path, data


if __name__ == '__main__':
    pass
