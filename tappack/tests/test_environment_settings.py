import sys
import zipfile

from tappack.entrypoint import main


def test_cli_loads_project_path_and_channel_from_environment(tmp_path, monkeypatch):
    project = tmp_path / "environment_project"
    project.mkdir()
    (project / "manifest.yml").write_text("name: environment_app\n", encoding="utf-8")
    (project / "entry.be").write_text("return true\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TAPPACK__MODULE_PATH", str(project))
    monkeypatch.setenv("TAPPACK__CHANNEL_ID", "development")
    output = tmp_path / "environment.tapp"
    monkeypatch.setattr(sys, "argv", ["tappack", "--output", str(output)])

    main()

    with zipfile.ZipFile(output) as archive:
        assert archive.read("entry.be") == b"return true\n"
        autoexec = archive.read("autoexec.be").decode("utf-8")
        assert "'channel_id': 'development'" in autoexec


def test_cli_pins_patch_version_from_environment(tmp_path, monkeypatch):
    project = tmp_path / "pinned_project"
    project.mkdir()
    (project / "manifest.yml").write_text(
        "name: pinned_app\n"
        "metadata:\n"
        "  version: 1.2.3\n"
        "patches:\n"
        "  - .type: Version\n"
        "    path: entry.be\n"
        '    pattern: "var VERSION = \'{version}\'"\n',
        encoding="utf-8",
    )
    (project / "entry.be").write_text("var VERSION = '0.0.0'\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TAPPACK__MODULE_PATH", str(project))
    monkeypatch.setenv("TAPPACK__VERSION", "8.7.6")
    output = tmp_path / "pinned.tapp"
    monkeypatch.setattr(sys, "argv", ["tappack", "--output", str(output)])

    main()

    with zipfile.ZipFile(output) as archive:
        assert archive.read("entry.be") == b"var VERSION = '8.7.6'\n"
