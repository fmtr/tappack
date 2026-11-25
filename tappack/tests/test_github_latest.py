import sys

import pytest

from tappack.entrypoint import main


def test_cli_rejects_latest_release_without_a_tag_before_writing(tmp_path, monkeypatch):
    project = tmp_path / "tagless_project"
    project.mkdir()
    (project / "manifest.yml").write_text(
        "name: tagless_app\n"
        "dependencies:\n"
        "  - name: extension\n"
        "    source:\n"
        "      .type: GitHubReleaseAsset\n"
        "      org: sample-org\n"
        "      repo: sample-repo\n"
        "      filename: extension.tapp\n",
        encoding="utf-8",
    )
    calls = []

    class Response:
        content = b""

        def raise_for_status(self):
            return None

        def json(self):
            return {}

    class Client:
        def get(self, url, **_kwargs):
            calls.append(url)
            return Response()

    monkeypatch.setattr("tappack.dm.dependencies.https.client", Client())
    output = tmp_path / "tagless.tapp"
    monkeypatch.setattr(
        sys,
        "argv",
        ["tappack", "--module-path", str(project), "--output", str(output)],
    )

    with pytest.raises(ValueError):
        main()

    assert calls == ["https://api.github.com/repos/sample-org/sample-repo/releases/latest"]
    assert not output.exists()
