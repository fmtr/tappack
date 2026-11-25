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
def test_version_patch_uses_semver(channel_id, expected):
    patch = VersionPatch.model_validate(
        {
            ".type": "Version",
            "path": "release.be",
            "pattern": "var VERSION = '{version}'",
            "inc_patch": 2,
        }
    )

    result = patch.apply(b"var VERSION = '4.7.9-alpha.2+old'\n", channel_id)

    assert re.fullmatch(expected, result.decode())


def test_version_patch_rejects_invalid_semver_prerelease():
    patch = VersionPatch.model_validate(
        {
            ".type": "Version",
            "path": "release.be",
            "pattern": "var VERSION = '{version}'",
        }
    )

    with pytest.raises(ValueError):
        patch.apply(b"var VERSION = '4.7.9-alpha.02'\n", "staging")
