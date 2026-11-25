# Manifest reference

A project can contain a `manifest.yaml` at its root. `tappack` searches upward from `--module-path` for this file. If no manifest is found, it packages the directory using its name and does not resolve dependencies or patches.

The manifest describes the package name, startup behavior, dependencies, and optional version patches. The runnable sample is [embedded in the quick start](quick-start.md).

## Top-level fields

| Field | Type | Meaning |
| --- | --- | --- |
| `name` | string | Package name used in the generated `autoexec.be` and as the default output filename. If omitted, the project directory name is used. |
| `autoexec` | object | Controls the generated startup file. |
| `dependencies` | list of objects | Each object has a unique `name` and a dependency source. The name becomes the output subdirectory. |
| `patches` | list | File changes applied while packaging, including channel-specific version updates. |

`tappack` generates `autoexec.be` from the package's Berry file paths. Set `autoexec.import: true` to import the package during startup; the default is `false`. `autoexec`'s `.channels` field is a list of entries, each with a `channel` ID and nested `settings` object, as shown in the [sample manifest](quick-start.md).

## Dependencies

Each item under `dependencies` has a required `name` and a nested `source`. The name selects the output subdirectory. Put `.type` first inside each direct source. Supported source types are:

| Source | Fields inside `source` |
| --- | --- |
| URL | `.type: URL` and `url`; the target must be a `.tapp` archive. |
| Local path | `.type: LocalPath` and `path`; the directory is packaged recursively. The path is resolved from the process's current working directory. |
| GitHub release asset | `.type: GitHubReleaseAsset`, `org`, `repo`, and `filename`; optionally set `version` and `prefix`. If `version` is omitted, the latest release is used. The default tag prefix is `v`. |

A channel-only source contains `.channels` instead of a top-level `.type`. A direct source can also contain `.channels` to override itself for selected channels. Each item in `.channels` has a `channel` ID and a nested `dependency` source. If no entry matches the selected channel, a channel-only dependency is skipped; a direct source remains the fallback.

For a local dependency, invoke `tappack` from the directory that makes the source's `path` resolve correctly. In the repository example, the command runs from `docs/examples`, so `path: shared_library` selects the sibling directory.

A complete example of nested dependency sources and channel-specific overrides is in the [sample manifest](examples/sample_app/manifest.yaml).

## Version patches

A patch entry uses `.type: Version` and includes a project-relative `path` and a regular-expression `pattern` containing `{version}`. The matched semantic version's patch component is increased by `inc_patch` (default `1`), then the selected channel and a build timestamp are added. Channel-specific patches use `.channels` as a list of entries with a `channel` and nested `patch` object.

The sample manifest patches `src/version.be` for the `development` channel. With no matching channel patch, no patch is applied.
