import io
import re
import sys
import zipfile

from tappack.entrypoint import main


def test_cli_downloads_url_dependency_from_zip(tmp_path, monkeypatch):
    project = tmp_path / "download_project"
    project.mkdir()
    (project / "manifest.yaml").write_text(
        "name: download_app\ndependencies:\n  extension: https://packages.invalid/extension.tapp\n",
        encoding="utf-8",
    )
    (project / "entry.be").write_text("return true\n", encoding="utf-8")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("nested/extension.be", "return { remote: true }\n")

    class Response:
        content = buffer.getvalue()

        def raise_for_status(self):
            return None

    class Client:
        def get(self, url, **_kwargs):
            assert url == "https://packages.invalid/extension.tapp"
            return Response()

    monkeypatch.setattr("tappack.package.https.client", Client())
    output = tmp_path / "download.tapp"
    monkeypatch.setattr(
        sys,
        "argv",
        ["tappack", "--module-path", str(project), "--output", str(output)],
    )

    main()

    with zipfile.ZipFile(output) as archive:
        assert archive.read("extension/nested/extension.be") == b"return { remote: true }\n"


def test_cli_applies_channel_version_patch(tmp_path, monkeypatch):
    project = tmp_path / "patch_project"
    source = project / "source"
    source.mkdir(parents=True)
    (project / "manifest.yaml").write_text(
        "name: patch_app\n"
        "patches:\n"
        "  - .channels:\n"
        "      local:\n"
        "        .type: Version\n"
        "        path: source/version.be\n"
        "        pattern: \"var VERSION = '{version}'\"\n",
        encoding="utf-8",
    )
    (source / "version.be").write_text("var VERSION = '3.4.5'\n", encoding="utf-8")
    output = tmp_path / "patched.tapp"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "tappack",
            "--module-path",
            str(project),
            "--output",
            str(output),
            "--channel-id",
            "local",
        ],
    )

    main()

    with zipfile.ZipFile(output) as archive:
        version_text = archive.read("source/version.be").decode("utf-8")

    assert re.fullmatch(
        r"var VERSION = '3\.4\.6-local\+\d{4}\.\d{2}\.\d{2}-\d{2}\.\d{2}\.\d{2}'\n",
        version_text,
    )
