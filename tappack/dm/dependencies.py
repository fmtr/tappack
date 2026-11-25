from __future__ import annotations

import io
import zipfile
from typing import Annotated, Literal

from pydantic import Field, field_validator

from corio import Path, dm, https, iterator
from tappack.obs import logger


class DependencyChannelOverride(dm.Base):
    channel: str = Field(min_length=1)
    dependency: Dependency


class DependencyBase(dm.Base):
    channels: iterator.ilist[DependencyChannelOverride] = Field(
        default_factory=iterator.ilist,
        alias=".channels",
    )

    @field_validator("channels")
    @classmethod
    def require_unique_channels(
        cls,
        channels: iterator.ilist[DependencyChannelOverride],
    ) -> iterator.ilist[DependencyChannelOverride]:
        channel_ids = [override.channel for override in channels]
        if len(channel_ids) != len(set(channel_ids)):
            raise ValueError("Channel overrides must have unique channel IDs.")
        return channels

    def for_channel(self, channel_id: str | None) -> DependencySource | None:
        override = self.channels.channel.get(channel_id)
        if override:
            return override.dependency.for_channel(channel_id)
        return self


class ArchiveDependency(DependencyBase):
    def get_url(self) -> str:
        raise NotImplementedError

    def get_content(self, name: str) -> bytes:
        url = self.get_url()
        logger.info(f'Downloading dependency "{name}" from "{url}".')
        response = https.client.get(url)
        response.raise_for_status()
        return response.content

    def iter_files(self, name: str, prefix: Path, _channel_id: str | None) -> dict[Path, bytes]:
        with zipfile.ZipFile(io.BytesIO(self.get_content(name))) as archive:
            return {
                prefix / info.filename: archive.read(info.filename)
                for info in archive.filelist
                if not info.is_dir()
            }


class URL(ArchiveDependency):
    type: Literal["URL"] = Field(alias=".type")
    url: str

    def get_url(self) -> str:
        return self.url


class LocalPath(DependencyBase):
    type: Literal["LocalPath"] = Field(alias=".type")
    path: Path

    @field_validator("path")
    @classmethod
    def require_existing_directory(cls, path: Path) -> Path:
        if not path.is_dir():
            raise ValueError(f'Local dependency path "{path}" is not a directory.')
        return path.resolve()

    def iter_files(self, name: str, prefix: Path, channel_id: str | None) -> dict[Path, bytes]:
        from tappack.package import Package

        package = Package(self.path, name=name, channel_id=channel_id)
        return package.iter_files(prefix)


class GitHubReleaseAsset(ArchiveDependency):
    type: Literal["GitHubReleaseAsset"] = Field(alias=".type")
    org: str
    repo: str
    filename: str
    version: str | None = None
    prefix: str = "v"

    def get_url(self) -> str:
        if self.version:
            tag = f"{self.prefix}{self.version}"
        else:
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

        return (
            f"https://github.com/{self.org}/{self.repo}/releases/download/"
            f"{tag}/{self.filename}"
        )


DependencySource = Annotated[
    URL | LocalPath | GitHubReleaseAsset,
    Field(discriminator="type"),
]


class ChannelDependency(DependencyBase):
    channels: iterator.ilist[DependencyChannelOverride] = Field(alias=".channels")

    def for_channel(self, channel_id: str | None) -> DependencySource | None:
        override = self.channels.channel.get(channel_id)
        if override is None:
            return None
        return override.dependency.for_channel(channel_id)


class Dependency(dm.Root):
    root: DependencySource | ChannelDependency

    def for_channel(self, channel_id: str | None) -> DependencySource | None:
        return self.root.for_channel(channel_id)


class DependencyEntry(dm.Base):
    name: str = Field(min_length=1)
    source: DependencySource | ChannelDependency

    def for_channel(self, channel_id: str | None) -> DependencySource | None:
        return self.source.for_channel(channel_id)
