from __future__ import annotations

import io
import zipfile
from corio import Path
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

        for dependency_config in self.manifest.dependencies:
            name = dependency_config.name
            dependency = dependency_config.for_channel(self.channel_id)
            if dependency is None:
                logger.warning(f'Skipping dependency "{name}": no matching channel configuration.')
                continue

            file_data.update(dependency.iter_files(name, prefix / name, self.channel_id))

        return self.apply_patches(file_data, prefix)

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
