import sys

import pytest
from pydantic import ValidationError

from tappack.dm.manifest import Manifest
from tappack.entrypoint import main


@pytest.mark.parametrize("name", [None, ""])
def test_manifest_requires_nonempty_dependency_names(name):
    dependency = {
        "source": {".type": "URL", "url": "https://packages.invalid/item.tapp"},
    }
    if name is not None:
        dependency["name"] = name

    with pytest.raises(ValidationError):
        Manifest.model_validate({"dependencies": [dependency]})


@pytest.mark.parametrize(
    "manifest_data",
    [
        {
            "dependencies": [
                {
                    "name": "addon",
                    "source": {
                        ".type": "URL",
                        "url": "https://packages.invalid/addon.tapp",
                        ".channels": [
                            {
                                "channel": "preview",
                                "dependency": {
                                    ".type": "URL",
                                    "url": "https://packages.invalid/first.tapp",
                                },
                            },
                            {
                                "channel": "preview",
                                "dependency": {
                                    ".type": "URL",
                                    "url": "https://packages.invalid/second.tapp",
                                },
                            },
                        ],
                    },
                },
            ],
        },
        {
            "autoexec": {
                ".channels": [
                    {"channel": "preview", "settings": {"import": True}},
                    {"channel": "preview", "settings": {"import": False}},
                ],
            },
        },
        {
            "patches": [
                {
                    ".channels": [
                        {
                            "channel": "preview",
                            "patch": {
                                ".type": "Version",
                                "path": "version.be",
                                "pattern": "{version}",
                            },
                        },
                        {
                            "channel": "preview",
                            "patch": {
                                ".type": "Version",
                                "path": "version.be",
                                "pattern": "{version}",
                            },
                        },
                    ],
                },
            ],
        },
    ],
)
def test_manifest_rejects_duplicate_channel_overrides(manifest_data):
    with pytest.raises(ValidationError):
        Manifest.model_validate(manifest_data)


def test_cli_rejects_duplicate_dependency_names_without_writing(tmp_path, monkeypatch):
    project = tmp_path / "duplicate_project"
    project.mkdir()
    (project / "manifest.yaml").write_text(
        "dependencies:\n"
        "  - name: widget\n"
        "    source:\n"
        "      .type: URL\n"
        "      url: https://packages.invalid/first.tapp\n"
        "  - name: widget\n"
        "    source:\n"
        "      .type: URL\n"
        "      url: https://packages.invalid/second.tapp\n",
        encoding="utf-8",
    )

    class Client:
        def get(self, url, **_kwargs):
            pytest.fail(f"Unexpected request to {url}")

    monkeypatch.setattr("tappack.dm.dependencies.https.client", Client())
    output = tmp_path / "duplicate.tapp"
    monkeypatch.setattr(
        sys,
        "argv",
        ["tappack", "--module-path", str(project), "--output", str(output)],
    )

    with pytest.raises(ValidationError):
        main()

    assert not output.exists()


def test_cli_rejects_missing_local_dependency_without_writing(tmp_path, monkeypatch):
    project = tmp_path / "local_project"
    project.mkdir()
    (project / "manifest.yaml").write_text(
        "name: local_app\n"
        "dependencies:\n"
        "  - name: extension\n"
        "    source:\n"
        "      .type: LocalPath\n"
        "      path: absent_dependency\n",
        encoding="utf-8",
    )
    output = tmp_path / "local.tapp"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        ["tappack", "--module-path", str(project), "--output", str(output)],
    )

    with pytest.raises(ValidationError):
        main()

    assert not output.exists()
