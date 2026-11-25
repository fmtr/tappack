import sys
import zipfile

import pytest

from tappack.entrypoint import main


@pytest.mark.parametrize("channel_id", [None, "unlisted"])
def test_cli_skips_channel_only_dependency_without_matching_channel(tmp_path, monkeypatch, channel_id):
    project = tmp_path / "channel_project"
    project.mkdir()
    (project / "manifest.yaml").write_text(
        "name: channel_app\n"
        "dependencies:\n"
        "  - name: extension\n"
        "    source:\n"
        "      .channels:\n"
        "        - channel: staging\n"
        "          dependency:\n"
        "            .type: URL\n"
        "            url: https://packages.invalid/extension.tapp\n",
        encoding="utf-8",
    )
    (project / "entry.be").write_text("return true\n", encoding="utf-8")

    class Client:
        def get(self, url, **_kwargs):
            pytest.fail(f"Unexpected request to {url}")

    monkeypatch.setattr("tappack.dm.dependencies.https.client", Client())
    output = tmp_path / "channel.tapp"
    arguments = ["tappack", "--module-path", str(project), "--output", str(output)]
    if channel_id:
        arguments.extend(["--channel-id", channel_id])
    monkeypatch.setattr(sys, "argv", arguments)

    main()

    with zipfile.ZipFile(output) as archive:
        members = archive.namelist()
        assert "entry.be" in members
        assert not any(member.startswith("extension/") for member in members)


def test_cli_skips_unselected_and_missing_version_patches(tmp_path, monkeypatch):
    project = tmp_path / "patch_project"
    project.mkdir()
    (project / "manifest.yaml").write_text(
        "name: patch_app\n"
        "patches:\n"
        "  - .channels:\n"
        "      - channel: staging\n"
        "        .type: Version\n"
        "        path: release.be\n"
        "        pattern: \"var VERSION = '{version}'\"\n"
        "  - .type: Version\n"
        "    path: absent.be\n"
        "    pattern: \"var VERSION = '{version}'\"\n",
        encoding="utf-8",
    )
    (project / "release.be").write_text("var VERSION = '4.2.1'\n", encoding="utf-8")
    output = tmp_path / "unpatched.tapp"
    monkeypatch.setattr(
        sys,
        "argv",
        ["tappack", "--module-path", str(project), "--output", str(output)],
    )

    main()

    with zipfile.ZipFile(output) as archive:
        assert archive.read("release.be") == b"var VERSION = '4.2.1'\n"
