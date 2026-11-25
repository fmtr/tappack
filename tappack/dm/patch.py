import re
from datetime import datetime, timezone
from typing import Literal

from pydantic import Field, field_validator

from corio import Constants, Path, dm, iterator, version


PATTERN_VERSION = (
    r"(?P<version>(?:0|[1-9]\d*)\."
    r"(?:0|[1-9]\d*)\."
    r"(?:0|[1-9]\d*)"
    r"(?:-(?:[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?"
    r"(?:\+(?:[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?)"
)


class VersionPatch(dm.Base):
    type: Literal["Version"] = Field(alias=".type")
    path: Path
    pattern: str
    encoding: str = Constants.ENCODING
    inc_patch: int = 1

    def apply(
        self,
        data: bytes,
        channel_id: str | None,
        base_version: str | None,
        version_override: str | None = None,
    ) -> bytes:
        expression = re.compile(self.pattern.format(version=PATTERN_VERSION))
        text = data.decode(self.encoding)

        if version_override is not None:
            target = str(version.Version.parse(version_override))
        else:
            if base_version is None:
                raise ValueError("A version patch requires metadata.version or --version.")

            original = version.Version.parse(base_version)
            patched = original.replace(patch=original.patch + self.inc_patch)
            build = datetime.now(timezone.utc).strftime(
                Constants.DATETIME_SEMVER_BUILD_FORMAT
            )
            target = str(patched.replace(prerelease=channel_id, build=build))

        def replace(match):
            return match.group(0).replace(match.group("version"), target)

        return expression.sub(replace, text).encode(self.encoding)


class PatchChannelOverride(VersionPatch):
    channel: str = Field(min_length=1)


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
            return override
        return None


class Patch(dm.Root):
    root: VersionPatch | ChannelPatch

    def for_channel(self, channel_id: str | None) -> VersionPatch | None:
        if isinstance(self.root, ChannelPatch):
            return self.root.for_channel(channel_id)
        return self.root
