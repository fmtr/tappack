import io
import sys
import zipfile

from tappack.constants import FileName
from tappack.entrypoint import main


def test_cli_downloads_url_dependency_from_zip(tmp_path, monkeypatch):
    project = tmp_path / "download_project"
    project.mkdir()
    (project / FileName.MANIFEST).write_text(
        "name: archive_app\n"
        "dependencies:\n"
        "  - name: addon\n"
        "    source:\n"
        "      .type: URL\n"
        "      url: https://bundles.invalid/addon.tapp\n",
        encoding="utf-8",
    )
    (project / "entry.be").write_text("return true\n", encoding="utf-8")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("nested/addon.be", "return { available: true }\n")

    class Response:
        content = buffer.getvalue()

        def raise_for_status(self):
            return None

    class Client:
        def get(self, url, **_kwargs):
            assert url == "https://bundles.invalid/addon.tapp"
            return Response()

    monkeypatch.setattr("tappack.dm.dependencies.https.client", Client())
    output = tmp_path / "download.tapp"
    monkeypatch.setattr(
        sys,
        "argv",
        ["tappack", "--module-path", str(project), "--output", str(output)],
    )

    main()

    with zipfile.ZipFile(output) as archive:
        assert archive.read("addon/nested/addon.be") == b"return { available: true }\n"


def test_cli_writes_manifest_version_to_autoexec_metadata(tmp_path, monkeypatch):
    project = tmp_path / "versioned_project"
    source = project / "source"
    source.mkdir(parents=True)
    (project / FileName.MANIFEST).write_text(
        "name: versioned_app\n"
        "metadata:\n"
        "  version: 6.3.8\n",
        encoding="utf-8",
    )
    source_file = source / "version.be"
    original_source = b"var VERSION = '0.2.1'\n"
    source_file.write_bytes(original_source)
    output = tmp_path / "versioned.tapp"
    monkeypatch.setattr(
        sys,
        "argv",
        ["tappack", "--module-path", str(project), "--output", str(output)],
    )

    main()

    with zipfile.ZipFile(output) as archive:
        assert archive.read("source/version.be") == original_source
        autoexec = archive.read(FileName.AUTOEXEC).decode("utf-8")

    assert "'version': '6.3.8'" in autoexec
    assert (project / FileName.AUTOEXEC).read_text(encoding="utf-8") == autoexec


def test_cli_pinned_version_is_written_to_autoexec_metadata(tmp_path, monkeypatch):
    project = tmp_path / "pinned_project"
    project.mkdir()
    (project / FileName.MANIFEST).write_text(
        "name: pinned_app\n"
        "metadata:\n"
        "  version: 6.3.8\n",
        encoding="utf-8",
    )
    source_file = project / "entry.be"
    original_source = b"var VERSION = '0.2.1'\n"
    source_file.write_bytes(original_source)
    output = tmp_path / "pinned.tapp"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "tappack",
            "--module-path",
            str(project),
            "--output",
            str(output),
            "--version",
            "8.4.1-rc.2",
        ],
    )

    main()

    with zipfile.ZipFile(output) as archive:
        assert archive.read("entry.be") == original_source
        autoexec = archive.read(FileName.AUTOEXEC).decode("utf-8")

    assert "'version': '8.4.1-rc.2'" in autoexec
