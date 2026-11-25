import sys
import zipfile

from tappack.entrypoint import main


def test_cli_uses_channel_only_local_dependency_for_matching_channel(tmp_path, monkeypatch):
    project = tmp_path / "channel_project"
    project.mkdir()
    dependency = tmp_path / "dependency"
    nested = dependency / "nested"
    nested.mkdir(parents=True)
    (nested / "extension.be").write_text("return true\n", encoding="utf-8")
    (project / "manifest.yaml").write_text(
        "name: channel_app\n"
        "dependencies:\n"
        "  extension:\n"
        "    .channels:\n"
        "      staging:\n"
        "        .type: LocalPath\n"
        "        path: dependency\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    output = tmp_path / "selected.tapp"
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
            "staging",
        ],
    )

    main()

    with zipfile.ZipFile(output) as archive:
        assert archive.read("extension/nested/extension.be") == b"return true\n"
