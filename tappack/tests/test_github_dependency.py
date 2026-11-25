import io
import sys
import zipfile

from tappack.entrypoint import main


def test_cli_downloads_versioned_github_release_asset(tmp_path, monkeypatch):
    project = tmp_path / "release_project"
    project.mkdir()
    (project / "manifest.yaml").write_text(
        "name: release_app\n"
        "dependencies:\n"
        "  extension:\n"
        "    .type: GitHubReleaseAsset\n"
        "    org: sample-org\n"
        "    repo: sample-repo\n"
        "    filename: extension.tapp\n"
        "    version: 2.3.4\n",
        encoding="utf-8",
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("extension.be", "return true\n")

    class Response:
        content = buffer.getvalue()

        def raise_for_status(self):
            return None

    class Client:
        def get(self, url, **_kwargs):
            assert url == (
                "https://github.com/sample-org/sample-repo/releases/download/"
                "v2.3.4/extension.tapp"
            )
            return Response()

    monkeypatch.setattr("tappack.package.https.client", Client())
    output = tmp_path / "release.tapp"
    monkeypatch.setattr(
        sys,
        "argv",
        ["tappack", "--module-path", str(project), "--output", str(output)],
    )

    main()

    with zipfile.ZipFile(output) as archive:
        assert archive.read("extension/extension.be") == b"return true\n"
