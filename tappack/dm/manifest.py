from __future__ import annotations

from typing import ClassVar

from pydantic import Field

from corio import Path, dm, sets
from tappack.dm.dependencies import Dependency
from tappack.dm.patch import Patch


MANIFEST_FILENAME = "manifest.yaml"


class Autoexec(dm.Base):
    import_enabled: bool = Field(default=False, alias="import")
    channels: dict[str, Autoexec] = Field(default_factory=dict, alias=".channels")

    def for_channel(self, channel_id: str | None) -> Autoexec:
        if channel_id:
            return self.channels.get(channel_id, self)
        return self


class Manifest(sets.Base, dm.Base):
    manifest_directory: ClassVar[Path | None] = None

    name: str | None = None
    autoexec: Autoexec = Field(default_factory=Autoexec)
    dependencies: dict[str, Dependency] = Field(default_factory=dict)
    patches: list[Patch] = Field(default_factory=list)

    @classmethod
    def find_yaml_file(cls) -> Path | None:
        directory = cls.manifest_directory or Path.cwd()
        try:
            return directory.find_up(MANIFEST_FILENAME)
        except FileNotFoundError:
            return None

    @classmethod
    def in_directory(cls, directory: Path) -> Manifest:
        directory_path = Path(directory).resolve()

        class DirectoryManifest(cls, cli_parse_args=False):
            manifest_directory: ClassVar[Path] = directory_path

        return DirectoryManifest()
