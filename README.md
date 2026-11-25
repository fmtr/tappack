# tappack

`tappack` builds a Tasmota Berry project into a `.tapp` package. It reads a `manifest.yaml`, collects the project files and declared dependencies, applies channel-specific version patches, generates `autoexec.be`, and writes the resulting archive.

## Install

```bash
pip install tappack
```

For a one-shot run without a separate install:

```bash
uvx tappack --help
```

## Package a project

The repository includes a runnable example. From its examples directory, build it with:

```bash
cd docs/examples
tappack --module-path sample_app --output ./sample_app.tapp --channel-id development
```

`tappack` also accepts a project path from elsewhere. Run `tappack --help` for its options; see the [quick start](https://fmtr.github.io/tappack/quick-start/) and [manifest guide](https://fmtr.github.io/tappack/manifest/) for details.

## Documentation

Read the [`tappack` documentation](https://fmtr.link/tappack/doc) for installation, CLI usage, manifest fields, and deployment guidance.
