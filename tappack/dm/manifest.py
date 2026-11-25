from __future__ import annotations

from typing import Any

from pydantic import Field, field_validator

from corio import Constants, Path, dm, iterator, version
from tappack.dm.dependencies import DependencyEntry
from tappack.dm.patch import Patch


MANIFEST_FILENAME = "manifest.yml"


class Metadata(dm.Base):
    version: str | None = None
    org_github: str = Constants.ORG_NAME
    org_friendly: str = Constants.ORG_NAME_FRIENDLY
    description: str | None = None
    docs: dict[str, Any] = Field(default_factory=dict)
    link_id: str | None = None

    @property
    def version_obj(self) -> version.Version:
        if self.version is None:
            raise ValueError("Project metadata must define a version.")

        return version.Version.parse(self.version)


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


class Manifest(dm.Base):
    name: str | None = None
    metadata: Metadata = Field(default_factory=Metadata)
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
    def in_directory(cls, directory: Path) -> Manifest:
        directory_path = Path(directory).resolve()
        try:
            manifest_path = directory_path.find_up(MANIFEST_FILENAME)
        except FileNotFoundError:
            return cls()

        return cls.model_validate(manifest_path.read_yaml() or {})
