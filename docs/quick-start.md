# Quick start

Install `tappack` from PyPI:

```bash
pip install tappack
```

The repository contains a sample project with two named dependencies. From the examples directory, package the `development` channel to use its local tools override and channel-specific version patch:

```bash
cd docs/examples
tappack --module-path sample_app --output ./sample_app.tapp --channel-id development
```

The command writes `sample_app.tapp` in the current directory. The manifest, Berry sources, and generated `autoexec.be` are stored in the archive. Dependencies are placed under their `name`: `helper_package/` comes from the local `shared_library` directory, and `tools_package/` uses the local `development_tools` directory because the `development` override is selected. Without that channel, `tools_package/` comes from the GitHub release asset.

The example manifest is a real file used by the command above:

```yaml
--8<--
docs/examples/sample_app/manifest.yaml
--8<--
```

## CLI options

- `--module-path` selects the project directory. It defaults to the current directory.
- `--output` selects the `.tapp` file. If omitted, the manifest name is used as the filename; when no manifest is present, the project directory name is used. The output is written in the current directory.
- `--channel-id` selects channel-specific dependency, autoexec, and patch settings.

The same scalar settings can be supplied through `TAPPACK__MODULE_PATH`, `TAPPACK__OUTPUT`, and `TAPPACK__CHANNEL_ID`. For example, from `docs/examples`:

```bash
TAPPACK__MODULE_PATH=sample_app TAPPACK__CHANNEL_ID=development tappack --output ./sample_app.tapp
```

Corio settings can also load a dotenv file selected with `--env` or a YAML file selected with `--config`; CLI options take precedence over environment, dotenv, and YAML values.

For an ephemeral invocation, run the same command with `uvx tappack` instead of `tappack`. Run `tappack --help` to see the available options.

For the manifest field reference and dependency forms, continue to the [manifest guide](manifest.md). For the rationale behind packaging-only scope, see [deployment guidance](deployment.md).
