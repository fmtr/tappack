import io
import sys
import zipfile

from tappack.entrypoint import main


def test_cli_fetches_asset_for_latest_github_tag(tmp_path, monkeypatch):
    project = tmp_path / "latest_project"
    project.mkdir()
    (project / "manifest.yml").write_text(
        "name: latest_app\n"
        "dependencies:\n"
        "  - name: extension\n"
        "    source:\n"
        "      .type: GitHubReleaseAsset\n"
        "      org: sample-org\n"
        "      repo: sample-repo\n"
        "      filename: extension.tapp\n",
        encoding="utf-8",
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("extension.be", "return true\n")
    calls = []

    class Response:
        def __init__(self, content=b"", tag=None):
            self.content = content
            self.tag = tag

        def raise_for_status(self):
            return None

        def json(self):
            return {"tag_name": self.tag}

    class Client:
        def get(self, url, **_kwargs):
            calls.append(url)
            if url.endswith("/releases/latest"):
                return Response(tag="v5.6.7")
            return Response(content=buffer.getvalue())

    monkeypatch.setattr("tappack.dm.dependencies.https.client", Client())
    output = tmp_path / "latest.tapp"
    monkeypatch.setattr(
        sys,
        "argv",
        ["tappack", "--module-path", str(project), "--output", str(output)],
    )

    main()

    assert calls == [
        "https://api.github.com/repos/sample-org/sample-repo/releases/latest",
        "https://github.com/sample-org/sample-repo/releases/download/"
        "v5.6.7/extension.tapp",
    ]
    with zipfile.ZipFile(output) as archive:
        assert archive.read("extension/extension.be") == b"return true\n"
