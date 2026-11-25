# Manifest reference

A project can contain a `manifest.yaml` at its root. `tappack` searches upward from `--module-path` for this file. If no manifest is found, it packages the directory using its name and does not resolve dependencies or patches.

The manifest describes the package name, startup behavior, dependencies, and optional version patches. The runnable sample is [embedded in the quick start](quick-start.md).

## Top-level fields

| Field | Type | Meaning |
| --- | --- | --- |
| `name` | string | Package name used in the generated `autoexec.be` and as the default output filename. If omitted, the project directory name is used. |
| `autoexec` | object | Controls the generated startup file. |
| `dependencies` | mapping | Maps package subdirectory names to dependency sources. |
| `patches` | list | File changes applied while packaging, including channel-specific version updates. |

`tappack` generates `autoexec.be` from the package's Berry file paths. Set `autoexec.import: true` to import the package during startup; the default is `false`. Use `.channels` to override autoexec settings for a channel, as in the [sample manifest](quick-start.md).

## Dependencies

Each entry under `dependencies` is keyed by the directory name where that dependency is placed in the package. Supported source forms are:

| Source | Fields |
| --- | --- |
| URL | A URL string, or an object with `.type: URL` and `url`; the target must be a `.tapp` archive. |
| Local path | `.type: LocalPath` and `path`; the directory is packaged recursively. The path is resolved from the process's current working directory. |
| GitHub release asset | `.type: GitHubReleaseAsset`, `org`, `repo`, and `filename`; optionally set `version` and `prefix`. If `version` is omitted, the latest release is used. The default tag prefix is `v`. |

For a local dependency, invoke `tappack` from the directory that makes the manifest's `path` resolve correctly. In the repository example, the command runs from `docs/examples`, so `path: shared_library` selects the sibling directory.

A complete example of a channel-specific local dependency and version patch is in the [sample manifest](examples/sample_app/manifest.yaml).

When a dependency contains only channel entries and the selected channel is not present, it is skipped. A direct source may also provide `.channels`; those entries replace the direct source when they match.

## Version patches

A patch entry uses `.type: Version` and includes a project-relative `path` and a regular-expression `pattern` containing `{version}`. The matched semantic version's patch component is increased by `inc_patch` (default `1`), then the selected channel and a build timestamp are added. Patches can be placed beneath `.channels` to apply them only to selected release channels.

The sample manifest patches `src/version.be` for the `development` channel. With no matching channel patch, no patch is applied.
