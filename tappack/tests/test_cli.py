import shutil
import sys
import zipfile

import pytest
from pydantic import ValidationError

from tappack.constants import FileName
from tappack.entrypoint import main
from tappack.paths import paths


ASSETS = paths.assets / "test_data"


def test_cli_packages_local_channel_dependency_and_generates_autoexec(tmp_path, monkeypatch):
    project = tmp_path / "project"
    dependency = tmp_path / "dependency"
    shutil.copytree(ASSETS / "packaging_project", project)
    shutil.copytree(ASSETS / "local_dependency", dependency)
    monkeypatch.chdir(tmp_path)
    output = tmp_path / "bundle.tapp"
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
        assert archive.read("src/entry.be") == b'return { kind: "sample" }\n'
        assert archive.read("tasks/worker.be") == b"return true\n"
        assert archive.read("plugin/nested/library.be") == b"return { ready: true }\n"
        autoexec = archive.read(FileName.AUTOEXEC).decode("utf-8")

    assert "src" in autoexec
    assert "tasks" in autoexec
    assert "plugin/nested" in autoexec
    assert "'import': true" in autoexec
    assert "'channel_id': 'local'" in autoexec


def test_cli_defaults_output_name_to_directory_without_manifest(tmp_path, monkeypatch):
    project = tmp_path / "loose_project"
    project.mkdir()
    (project / "entry.be").write_text("return true\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["tappack", "--module-path", str(project)])

    main()

    with zipfile.ZipFile(tmp_path / "loose_project.tapp") as archive:
        assert archive.read("entry.be") == b"return true\n"
        assert FileName.AUTOEXEC in archive.namelist()


def test_cli_rejects_missing_module_without_creating_output(tmp_path, monkeypatch):
    output = tmp_path / "rejected.tapp"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "tappack",
            "--module-path",
            str(tmp_path / "missing"),
            "--output",
            str(output),
        ],
    )

    with pytest.raises(ValidationError):
        main()

    assert not output.exists()
