from __future__ import annotations

import io
import zipfile
from functools import cached_property

from corio import Path, https

from tappack.dm.dependencies import (
    DependencySource,
    GitHubReleaseAssetDependency,
    LocalPathDependency,
    URLDependency,
)
from tappack.dm.manifest import Manifest
from tappack.dm.patch import VersionPatch
from tappack.obs import logger
from tappack.paths import paths


class Package:
    def __init__(self, path: Path, name: str | None = None, channel_id: str | None = None):
        self.path = Path(path).resolve()
        self.channel_id = channel_id
        self.manifest = Manifest.in_directory(self.path)
        self.name = name or self.manifest.name or self.path.name

    def iter_files(self, prefix: Path = Path(".")) -> dict[Path, bytes]:
        logger.info(f'Collecting package files from "{self.path}".')
        file_data = {}

        for path in self.path.rglob("*"):
            if not path.is_file():
                continue
            relative_path = path.relative_to(self.path)
            file_data[prefix / relative_path] = path.read_bytes()

        for name, dependency_config in self.manifest.dependencies.items():
            dependency = dependency_config.for_channel(self.channel_id)
            if dependency is None:
                logger.warning(f'Skipping dependency "{name}": no matching channel configuration.')
                continue

            dependency_package = self.create_dependency(name, dependency)
            file_data.update(dependency_package.iter_files(prefix / name))

        return self.apply_patches(file_data, prefix)

    def create_dependency(self, name: str, dependency: DependencySource) -> Package | URL:
        match dependency:
            case LocalPathDependency() as local:
                return Package(local.path, name=name, channel_id=self.channel_id)
            case URLDependency() as url:
                return URL(name, url.url)
            case GitHubReleaseAssetDependency() as asset:
                return GitHubReleaseAsset(
                    name=name,
                    org=asset.org,
                    repo=asset.repo,
                    filename=asset.filename,
                    version=asset.version,
                    prefix=asset.prefix,
                )

    def apply_patches(self, file_data: dict[Path, bytes], prefix: Path) -> dict[Path, bytes]:
        for patch_config in self.manifest.patches:
            patch = patch_config.for_channel(self.channel_id)
            if patch is None:
                continue

            target = prefix / patch.path
            if target not in file_data:
                logger.warning(
                    f'Manifest for "{self.name}" defines a patch for "{patch.path}", but the file was not found.'
                )
                continue

            logger.info(f'Applying version patch to "{target}".')
            file_data[target] = patch.apply(file_data[target], self.channel_id)

        return file_data

    def generate_autoexec(self, file_data: dict[Path, bytes]) -> str:
        module_paths = sorted(
            {
                path.parent
                for path in file_data
                if path.suffix in {".be", ".bec"} and path.parent != Path(".")
            },
            key=str,
        )
        path_names = [str(path) for path in module_paths]
        template = (paths.assets / "autoexec.be.template").read_text(encoding="utf-8")
        autoexec = self.manifest.autoexec.for_channel(self.channel_id)
        replacements = {
            "paths": repr(path_names),
            "module_name": self.name,
            "import": str(autoexec.import_enabled).lower(),
            "channel_id": repr(self.channel_id) if self.channel_id else "nil",
        }

        for key, replacement in replacements.items():
            template = template.replace(f"{{{key}}}", replacement)

        logger.info(f'Generated autoexec.be with module paths {path_names}.')
        return template

    def build_archive(self) -> io.BytesIO:
        file_data = self.iter_files()
        file_data[Path("autoexec.be")] = self.generate_autoexec(file_data).encode("utf-8")
        buffer = io.BytesIO()

        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED) as archive:
            for path, content in sorted(file_data.items(), key=lambda item: str(item[0])):
                logger.info(f'Adding "{path}" ({len(content)} bytes) to the archive.')
                archive.writestr(str(path), content)

        buffer.seek(0)
        return buffer

    def write(self, output: Path | None = None) -> Path:
        output_path = Path(output or (Path.cwd() / f"{self.name}.tapp")).resolve()
        archive = self.build_archive().getvalue()
        output_path.write_bytes(archive)
        logger.info(f'Wrote package ({len(archive)} bytes) to "{output_path}".')
        return output_path


class URL:
    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url

    def get_content(self) -> bytes:
        logger.info(f'Downloading dependency "{self.name}" from "{self.url}".')
        response = https.client.get(self.url)
        response.raise_for_status()
        return response.content

    def iter_files(self, prefix: Path = Path(".")) -> dict[Path, bytes]:
        with zipfile.ZipFile(io.BytesIO(self.get_content())) as archive:
            return {
                prefix / info.filename: archive.read(info.filename)
                for info in archive.filelist
                if not info.is_dir()
            }


class GitHubReleaseAsset(URL):
    def __init__(
        self,
        name: str,
        org: str,
        repo: str,
        filename: str,
        version: str | None = None,
        prefix: str = "v",
    ):
        self.name = name
        self.org = org
        self.repo = repo
        self.filename = filename
        self.version = version
        self.prefix = prefix

    @cached_property
    def tag(self) -> str:
        if self.version:
            return f"{self.prefix}{self.version}"

        url = f"https://api.github.com/repos/{self.org}/{self.repo}/releases/latest"
        response = https.client.get(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        response.raise_for_status()
        tag = response.json().get("tag_name")
        if not tag:
            raise ValueError(f'No release tag found for "{self.org}/{self.repo}".')
        return tag

    @cached_property
    def url(self) -> str:
        return (
            f"https://github.com/{self.org}/{self.repo}/releases/download/"
            f"{self.tag}/{self.filename}"
        )
