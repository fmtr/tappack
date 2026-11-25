from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator

from corio import Path, dm


class DependencyBase(dm.Base):
    channels: dict[str, Dependency] = Field(default_factory=dict, alias=".channels")


class URLDependency(DependencyBase):
    type: Literal["URL"] = Field(alias=".type")
    url: str


class LocalPathDependency(DependencyBase):
    type: Literal["LocalPath"] = Field(alias=".type")
    path: Path

    @field_validator("path")
    @classmethod
    def require_existing_directory(cls, path: Path) -> Path:
        if not path.is_dir():
            raise ValueError(f'Local dependency path "{path}" is not a directory.')
        return path.resolve()


class GitHubReleaseAssetDependency(DependencyBase):
    type: Literal["GitHubReleaseAsset"] = Field(alias=".type")
    org: str
    repo: str
    filename: str
    version: str | None = None
    prefix: str = "v"


DependencySource = Annotated[
    URLDependency | LocalPathDependency | GitHubReleaseAssetDependency,
    Field(discriminator="type"),
]


class ChannelDependency(dm.Base):
    channels: dict[str, Dependency] = Field(alias=".channels")


class Dependency(dm.Root):
    root: DependencySource | ChannelDependency

    @model_validator(mode="before")
    @classmethod
    def parse_url_shorthand(cls, value):
        if isinstance(value, str):
            value = {".type": "URL", "url": value}
        return value

    def for_channel(self, channel_id: str | None) -> DependencySource | None:
        if isinstance(self.root, ChannelDependency):
            if not channel_id:
                return None
            selected = self.root.channels.get(channel_id)
            if selected is None:
                return None
            return selected.for_channel(channel_id)

        selected = self.root.channels.get(channel_id) if channel_id else None
        if selected:
            return selected.for_channel(channel_id)
        return self.root
