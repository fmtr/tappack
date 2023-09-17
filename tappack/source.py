import io
import logging
import requests
import yaml
import zipfile
from functools import cached_property
from pathlib import Path

from tappack.constants import ENCODING, NAME_MANIFEST
from tappack.patch import Version


def from_manifest(classes, data, channel_id, extra_args=None):
    class_map = {cls.__name__: cls for cls in classes or {}}

    channels = data.get('.channels', {})
    if channel_id in channels:
        data = channels[channel_id]

    if not classes:
        return data

    class_name = data.pop('.type', None)
    source_class = class_map.get(class_name)
    if source_class is None:
        if channels:
            return None
        else:
            raise ValueError(f"Invalid object type: {class_name}")
    data = data | (extra_args or {})
    data = {key: value for key, value in data.items() if not key.startswith('.')}
    obj = source_class(**data)
    return obj


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

        self.dependencies = list(self.get_dependencies())
        self.patches = self.get_patches()
        self.code_mask = self.manifest.get('code_mask')
        self.autoexec = from_manifest(None, self.manifest.get('autoexec', {}), self.channel_id)

    def iter_files(self, prefix=None):
        """

        Generator that recursively iterates any files in the specified path, then any files in any sub-dependencies,
        passing down the current path prefix, plus the name of the dependency. This yields tuples containing the
        relative path of each file paired with the file data as bytes.

        """

        print(f'Iterating dependency in path "{self.path}"...')
        prefix = Path(prefix or '.')

        file_data = {}

        for path in self.path.rglob('*'):
            if path.is_dir():
                continue

            file_bytes = path.read_bytes()
            path = path.relative_to(self.path)

            if prefix:
                path = Path(prefix) / path
            file_data[path] = file_bytes

        for name, dept in self.dependencies:
            dept_data = dept.iter_files(prefix / name)
            file_data.update(dept_data)

        file_data = self.apply_patches(file_data, prefix)

        return file_data

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

        auto_import = str(bool(self.autoexec.get('import'))).lower()

        replacements = {
            'paths': repr(paths),
            'module_name': self.name,
            'import': auto_import,
            'channel_id': repr(self.channel_id) if self.channel_id else 'nil'
        }

        for key, replacement in replacements.items():
            text = text.replace(f'{{{key}}}', replacement)

        print(f'Added submodule paths to autoexec.be: {paths}')

        return text

    def get_dependencies(self):

        for name, data in self.manifest.copy().get('dependencies', {}).items():

            if type(data) is str:
                data = {'.type': 'URL', 'url': data}

            source = from_manifest({LocalPath, URL, GitHubReleaseAsset}, data, self.channel_id,
                                   {'name': name, 'channel_id': self.channel_id})

            if not source:
                msg = f'Data resulted in no object. ' \
                      f'This should be when the object only has channel config, and that channel is not specified. {data}'
                logging.warning(msg)
                continue

            yield name, source

    def build_archive(self):
        # Create a ZIP (tapp) file containing the entire module directory structure
        file_data = dict(self.iter_files())
        file_data = {Path('autoexec.be'): self.generate_autoexec(file_data).encode(ENCODING)} | file_data
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_STORED) as zip_file:
            for path, file_bytes in file_data.items():
                print(f'Writing file "{path}" ({len(file_bytes)} bytes) to archive...')
                zip_file.writestr(str(path), file_bytes)

        buffer.seek(0)
        return buffer

    def write(self, path_tapp):
        path_tapp = Path(path_tapp or (Path('.') / self.name).with_suffix('.tapp')).absolute().resolve()
        archive_bytes = self.build_archive().getvalue()
        print(f'Writing output archive ({len(archive_bytes)} bytes) to "{path_tapp}"...')
        path_tapp.write_bytes(archive_bytes)

    def get_patches(self):
        patches = {}
        for data in self.manifest.copy().get('patches', []):
            obj = from_manifest({Version}, data, self.channel_id, {'channel_id': self.channel_id})
            if not obj:
                msg = f'Manifest data resulted in no patch object. ' \
                      f'This should be when the object only has channel config, and that channel is not specified. {data}'
                logging.warning(msg)
                continue
            patches.setdefault(obj.path, [])
            patches[obj.path].append(obj)

        return patches

    def apply_patches(self, file_data, prefix):

        for path, patches in self.patches.items():

            if prefix / path in file_data:
                for patch_obj in patches:
                    file_data[prefix / path] = patch_obj.apply(file_data[prefix / path])
                    file_data
            else:
                msg = f'Manifest for "{self.name}" defines a patch that targets path "{path}", but no such path was found.'
                logging.warning(msg)
        return file_data


class URL(Source):

    def __init__(self, name, url, channel_id=None):
        self.name = name
        self.url = url

    def get_content(self):
        print(f'Downloading dependency "{self.name}" from "{self.url}"...')
        response = requests.get(self.url)
        response.raise_for_status()
        return response.content

    def iter_files(self, prefix=None):
        prefix = Path(prefix or '.')

        content = self.get_content()

        file_data = {}

        with zipfile.ZipFile(io.BytesIO(content)) as zip_file:
            for info in zip_file.filelist:
                data = zip_file.read(info.filename)
                path = prefix / info.filename
                file_data[path] = data

        return file_data


class GitHubReleaseAsset(URL):

    def __init__(self, name, org, repo, filename, version=None, prefix='v', channel_id=None):
        self.name = name
        self.org = org
        self.repo = repo
        self.filename = filename
        self.version = version
        self.channel_id = channel_id
        self.prefix = prefix

    def get_tag_latest(self):
        url = f"https://api.github.com/repos/{self.org}/{self.repo}/releases/latest"

        headers = {
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28'
        }

        response = requests.request("GET", url, headers=headers)
        response_json = response.json()

        tag = response_json.get('tag_name')

        if not tag:
            raise ValueError(f'No tag found for "{self.org}" and "{self.repo}"')

        return tag

    @cached_property
    def tag(self):
        if not self.version:
            return None
        return f'{self.prefix or ""}{self.version}'

    @cached_property
    def url(self):
        tag = self.tag or self.get_tag_latest()
        url = f'https://github.com/{self.org}/{self.repo}/releases/download/{tag}/{self.filename}'

        return url


if __name__ == '__main__':
    pass
