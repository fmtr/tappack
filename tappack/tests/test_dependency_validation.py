import sys

import pytest
from pydantic import ValidationError

from tappack.entrypoint import main


def test_cli_rejects_missing_local_dependency_without_writing(tmp_path, monkeypatch):
    project = tmp_path / "local_project"
    project.mkdir()
    (project / "manifest.yaml").write_text(
        "name: local_app\n"
        "dependencies:\n"
        "  extension:\n"
        "    .type: LocalPath\n"
        "    path: absent_dependency\n",
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
