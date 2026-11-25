from __future__ import annotations

from typing import ClassVar

from pydantic import Field, field_validator

from corio import Path, dm, iterator, sets
from tappack.dm.dependencies import DependencyEntry
from tappack.dm.patch import Patch


MANIFEST_FILENAME = "manifest.yaml"


class AutoexecSettings(dm.Base):
    import_enabled: bool = Field(default=False, alias="import")


class Autoexec(AutoexecSettings):
    channels: iterator.ilist[AutoexecChannelOverride] = Field(
        default_factory=iterator.ilist,
        alias=".channels",
    )

    @field_validator("channels")
    @classmethod
    def require_unique_channels(
        cls,
        channels: iterator.ilist[AutoexecChannelOverride],
    ) -> iterator.ilist[AutoexecChannelOverride]:
        channel_ids = [override.channel for override in channels]
        if len(channel_ids) != len(set(channel_ids)):
            raise ValueError("Channel overrides must have unique channel IDs.")
        return channels

    def for_channel(self, channel_id: str | None) -> AutoexecSettings:
        override = self.channels.channel.get(channel_id)
        if override:
            return override
        return self


class AutoexecChannelOverride(AutoexecSettings):
    channel: str = Field(min_length=1)


class Manifest(sets.Base, dm.Base):
    manifest_directory: ClassVar[Path | None] = None

    name: str | None = None
    autoexec: Autoexec = Field(default_factory=Autoexec)
    dependencies: list[DependencyEntry] = Field(default_factory=list)
    patches: list[Patch] = Field(default_factory=list)

    @field_validator("dependencies")
    @classmethod
    def require_unique_dependency_names(
        cls,
        dependencies: list[DependencyEntry],
    ) -> list[DependencyEntry]:
        names = set()
        for dependency in dependencies:
            if dependency.name in names:
                raise ValueError(f'Duplicate dependency name "{dependency.name}".')
            names.add(dependency.name)
        return dependencies

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
