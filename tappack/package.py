from __future__ import annotations

import io
import zipfile
from corio import Path
from tappack.constants import FileName
from tappack.dm.manifest import Manifest
from tappack.obs import logger
from tappack.paths import paths


class Package:
    def __init__(
        self,
        path: Path,
        name: str | None = None,
        channel_id: str | None = None,
        version: str | None = None,
    ):
        self.path = Path(path).resolve()
        self.channel_id = channel_id
        self.version = version
        self.manifest = Manifest.in_directory(self.path)
        self.name = name or self.manifest.name or self.path.name

    @property
    def autoexec_path(self) -> Path:
        return self.path / FileName.AUTOEXEC

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
        template = (paths.assets / FileName.AUTOEXEC_TEMPLATE).read_text(encoding="utf-8")
        autoexec = self.manifest.autoexec.for_channel(self.channel_id)
        version = self.version if self.version is not None else self.manifest.metadata.version
        version_value = repr(version) if version is not None else "nil"
        replacements = {
            "paths": repr(path_names),
            "module_name": self.name,
            "import": str(autoexec.import_enabled).lower(),
            "channel_id": repr(self.channel_id) if self.channel_id else "nil",
            "version": version_value,
        }

        for key, replacement in replacements.items():
            template = template.replace(f"{{{key}}}", replacement)

        logger.info(f'Generated {FileName.AUTOEXEC} with module paths {path_names}.')
        return template

    def build_archive(self) -> io.BytesIO:
        file_data = self.iter_files()
        autoexec_content = self.generate_autoexec(file_data).encode("utf-8")
        self.autoexec_path.write_bytes(autoexec_content)
        logger.info(f'Wrote generated {FileName.AUTOEXEC} to "{self.autoexec_path}".')
        file_data[Path(FileName.AUTOEXEC)] = autoexec_content
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
