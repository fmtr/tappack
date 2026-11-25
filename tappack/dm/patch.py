import re
from datetime import datetime
from typing import Literal

from pydantic import Field, field_validator

from corio import Constants, Path, dm, iterator


PATTERN_VERSION = (
    r"(?P<version>(?P<major>0|[1-9]\d*)\."
    r"(?P<minor>0|[1-9]\d*)\."
    r"(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<pre>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?"
    r"(?:\+(?P<build>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?)"
)


class VersionPatch(dm.Base):
    type: Literal["Version"] = Field(alias=".type")
    path: Path
    pattern: str
    encoding: str = Constants.ENCODING
    inc_patch: int = 1

    def apply(self, data: bytes, channel_id: str | None) -> bytes:
        expression = re.compile(self.pattern.format(version=PATTERN_VERSION))
        text = data.decode(self.encoding)
        build = datetime.now().strftime("%Y.%m.%d-%H.%M.%S")

        def replace(match):
            major, minor, patch = (
                int(match.group(name))
                for name in ("major", "minor", "patch")
            )
            version = f"{major}.{minor}.{patch + self.inc_patch}-{channel_id}+{build}"
            return match.group(0).replace(match.group("version"), version)

        return expression.sub(replace, text).encode(self.encoding)


class PatchChannelOverride(dm.Base):
    channel: str = Field(min_length=1)
    patch: VersionPatch


class ChannelPatch(dm.Base):
    channels: iterator.ilist[PatchChannelOverride] = Field(alias=".channels")

    @field_validator("channels")
    @classmethod
    def require_unique_channels(
        cls,
        channels: iterator.ilist[PatchChannelOverride],
    ) -> iterator.ilist[PatchChannelOverride]:
        channel_ids = [override.channel for override in channels]
        if len(channel_ids) != len(set(channel_ids)):
            raise ValueError("Patch channel overrides must have unique channel IDs.")
        return channels

    def for_channel(self, channel_id: str | None) -> VersionPatch | None:
        override = self.channels.channel.get(channel_id)
        if override:
            return override.patch
        return None


class Patch(dm.Root):
    root: VersionPatch | ChannelPatch

    def for_channel(self, channel_id: str | None) -> VersionPatch | None:
        if isinstance(self.root, ChannelPatch):
            return self.root.for_channel(channel_id)
        return self.root
