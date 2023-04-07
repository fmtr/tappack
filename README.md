# `tappack`: Tasmota Application Packager

This tool aims to simplify packaging Tasmota Berry code as a TAPP file, including basic dependency resolution. It can be
run locally, but is primarily intended for use during a release workflow, e.g. GitHub Actions.

## What Does It Do?

It performs the following:

* Reads your project manifest file (see below), with a list of dependency URLs (other `.tapp` files).
* Downloads each, extracts and merges them, in a subfolder, it into your own code.
* Auto-generates an `autoexec.be` for your library that sets up all the relevant dependency paths.
* Packages the whole structure into a `.tapp` file ready for deployment.

## Manifest File

Your project needs to contain a `tappack` manifest file, `manifest.yaml`, with at least fields `name`
and `dependencies`. The latter is a mapping of module names to URLs of corresponding `.tapp` file. For example:

```yaml
name: my_library
dependencies:
  tools: https://github.com/fmtr/tools/releases/download/v0.0.1/tools.tapp

```

You can also specify when a dependency should be read from a local path (with be recursed automatically) as follows:

```yaml
name: my_library
dependencies:
  my_dependency:
    .type: LocalPath
    path: /usr/src/my_dependency
```

Release channels are also supported. So pulling from a URL during normal packaging, but from a local path during a
development build (i.e. with parameter `--channel-id development`), is done like this:

```yaml
name: my_library
dependencies:
  tools:
    .type: URL
    url: https://github.com/fmtr/tools/releases/download/v0.0.1/tools.tapp
    .channels:
      development:
        .type: LocalPath
        path: /fm/tools.be/module
```

## Example Usage

```bash
$ tappack --help
```

```console
Usage: tappack [OPTIONS]

Options:
  --module-path DIRECTORY  Path to your module, containing any Berry files,
                           manifests, assets, etc. Example:
                           /usr/src/my_berry_project  [required]
  --output FILE            Path to write the output .tapp package. Example:
                           ~/my_project.tapp
  --channel-id TEXT        Identifier for the release channel. Only relevant
                           if your manifests contain release channel
                           information. Example: development
  --help                   Show this message and exit.
```

```bash
$tappack --module-path /usr/src/my_berry_project --tapp-path ~/my_project.tapp
```

## Installing

`$pip install tappack`

## No `autoexec.be`

Your module should _not_ contain an `autoexec.be`, as `tappack` will generate one. If you need to run any code in
the `autoexec` context, then ensure your module implements an `autoexec` method, which will be called once it is
imported. For example:

```be
var mod = module("my_module")

def autoexec()

    # Do autoexec stuff here.

end

mod.autoexec=autoexec
return mod
```



