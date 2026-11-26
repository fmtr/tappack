# Manifest reference

A project can contain a `manifest.yml` at its root. `tappack` searches upward from `--module-path` for this file. If no manifest is found, it packages the directory using its name and has no declared dependencies.

The manifest describes the package name, version metadata, startup behavior, and dependencies. The runnable sample is [embedded in the quick start](quick-start.md).

## Top-level fields

| Field | Type | Meaning |
| --- | --- | --- |
| `name` | string | Package name used in the generated `autoexec.be` and as the default output filename. If omitted, the project directory name is used. |
| `metadata` | object | Optional project metadata, including the current `version` and Corio release settings. |
| `autoexec` | object | Controls the generated startup file. |
| `dependencies` | list of objects | Each object has a unique `name` and a dependency source. The name becomes the output subdirectory. |

`metadata.version` is the package version recorded in generated startup metadata unless overridden with `--version`. The Corio metadata fields `org_github`, `org_friendly`, `description`, `docs`, and `link_id` are optional; `link_id` selects a short URL to update after a Corio release. API credentials remain environment variables.

`tappack` generates `autoexec.be` from the package's Berry file paths and metadata. Set `autoexec.import: true` to import the package during startup; the default is `false`. `autoexec`'s `.channels` field is a list of entries, each with a `channel` ID and the autoexec fields to use for that channel, as shown in the [sample manifest](quick-start.md). The version is available to Berry code in the package's `TAPP_METADATA` entry. Source files are included unchanged.

## Dependencies

Each item under `dependencies` has a required `name` and a nested `source`. The name selects the output subdirectory. Put `.type` first inside each direct source. Supported source types are:

| Source | Fields inside `source` |
| --- | --- |
| URL | `.type: URL` and `url`; the target must be a `.tapp` archive. |
| Local path | `.type: LocalPath` and `path`; the directory is packaged recursively. The path is resolved from the process's current working directory. |
| GitHub release asset | `.type: GitHubReleaseAsset`, `org`, `repo`, and `filename`; optionally set `version` and `prefix`. If `version` is omitted, the latest release is used. The default tag prefix is `v`. |

A channel-only source contains `.channels` instead of a top-level `.type`. A direct source can also contain `.channels` to override itself for selected channels. The `.channels` list belongs **inside that dependency's `source`**, not beside the dependency entries. Each item has a `channel` ID and a nested `dependency` source. On a match, that nested source replaces the direct source; without a match, the direct source is used. A channel-only dependency with no matching entry is skipped.

The `name` on each dependency selects its output directory. For local sources, `path` is resolved from the process's current working directory. In the sample, run `tappack` from `docs/examples`: `helper_package` uses `shared_library`, while the `development` override for `tools_package` uses `development_tools`.

The [sample manifest](examples/sample_app/manifest.yml) shows two dependency entries, one with a direct source and one with a channel override nested inside its source.

## Version metadata

The generated `autoexec.be` adds a `version` value to the package's `TAPP_METADATA` entry. It uses `metadata.version` from the manifest, or the exact value supplied through `--version` when provided. If neither is set, the generated value is `nil`. Packaging does not rewrite Berry source files; put application-specific version handling in the source code that needs it.
