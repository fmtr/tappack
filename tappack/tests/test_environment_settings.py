import sys
import zipfile

from tappack.constants import FileName
from tappack.entrypoint import main


def test_cli_loads_project_path_and_channel_from_environment(tmp_path, monkeypatch):
    project = tmp_path / "environment_project"
    project.mkdir()
    (project / FileName.MANIFEST).write_text("name: environment_app\n", encoding="utf-8")
    (project / "entry.be").write_text("return true\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TAPPACK__MODULE_PATH", str(project))
    monkeypatch.setenv("TAPPACK__CHANNEL_ID", "development")
    output = tmp_path / "environment.tapp"
    monkeypatch.setattr(sys, "argv", ["tappack", "--output", str(output)])

    main()

    with zipfile.ZipFile(output) as archive:
        assert archive.read("entry.be") == b"return true\n"
        autoexec = archive.read(FileName.AUTOEXEC).decode("utf-8")
        assert "'channel_id': 'development'" in autoexec


def test_cli_puts_environment_version_override_in_metadata(tmp_path, monkeypatch):
    project = tmp_path / "override_project"
    project.mkdir()
    (project / FileName.MANIFEST).write_text(
        "name: override_app\n"
        "metadata:\n"
        "  version: 5.8.1\n",
        encoding="utf-8",
    )
    source_file = project / "entry.be"
    original_source = b"var VERSION = '0.0.0'\n"
    source_file.write_bytes(original_source)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TAPPACK__MODULE_PATH", str(project))
    monkeypatch.setenv("TAPPACK__VERSION", "9.6.2-preview.4")
    output = tmp_path / "override.tapp"
    monkeypatch.setattr(sys, "argv", ["tappack", "--output", str(output)])

    main()

    with zipfile.ZipFile(output) as archive:
        assert archive.read("entry.be") == original_source
        autoexec = archive.read(FileName.AUTOEXEC).decode("utf-8")

    assert "'version': '9.6.2-preview.4'" in autoexec
