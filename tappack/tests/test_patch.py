import re

import pytest

from tappack.dm.patch import VersionPatch


@pytest.mark.parametrize(
    ("channel_id", "expected"),
    [
        (
            "staging",
            r"var VERSION = '4\.7\.11-staging\+\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}'\n",
        ),
        (
            None,
            r"var VERSION = '4\.7\.11\+\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}'\n",
        ),
    ],
)
def test_version_patch_derives_from_manifest_version(channel_id, expected):
    patch = VersionPatch.model_validate(
        {
            ".type": "Version",
            "path": "release.be",
            "pattern": "var VERSION = '{version}'",
            "inc_patch": 2,
        }
    )

    result = patch.apply(
        b"var VERSION = '0.1.2'\n",
        channel_id,
        "4.7.9-alpha.2+old",
    )

    assert re.fullmatch(expected, result.decode())


def test_version_patch_uses_pinned_version_without_modifying_it():
    patch = VersionPatch.model_validate(
        {
            ".type": "Version",
            "path": "release.be",
            "pattern": "var VERSION = '{version}'",
            "inc_patch": 5,
        }
    )

    result = patch.apply(
        b"var VERSION = '0.1.2'\n",
        "staging",
        "4.7.9",
        "8.2.0-rc.3",
    )

    assert result == b"var VERSION = '8.2.0-rc.3'\n"


def test_version_patch_rejects_invalid_manifest_version():
    patch = VersionPatch.model_validate(
        {
            ".type": "Version",
            "path": "release.be",
            "pattern": "var VERSION = '{version}'",
        }
    )

    with pytest.raises(ValueError):
        patch.apply(b"var VERSION = '0.1.2'\n", "staging", "4.7.9-alpha.02")
