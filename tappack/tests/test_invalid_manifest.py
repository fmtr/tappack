import sys

import pytest
from pydantic import ValidationError

from tappack.entrypoint import main


def test_cli_rejects_incomplete_remote_dependency_before_writing(tmp_path, monkeypatch):
    project = tmp_path / "invalid_project"
    project.mkdir()
    (project / "manifest.yaml").write_text(
        "name: invalid_app\n"
        "dependencies:\n"
        "  - name: extension\n"
        "    source:\n"
        "      .type: URL\n",
        encoding="utf-8",
    )
    output = tmp_path / "invalid.tapp"
    monkeypatch.setattr(
        sys,
        "argv",
        ["tappack", "--module-path", str(project), "--output", str(output)],
    )

    with pytest.raises(ValidationError):
        main()

    assert not output.exists()
