# Tasmota Application Packager

## Manifest File

Your project should contain a `tappack` manifest file, `tappack.yaml`. This should contain a field names `dependencies`,
mapping module names to URLs to a corresponding `.tapp` file. For example:

```yaml
name: my_library
dependencies:
  tools: https://github.com/fmtr/tools/releases/download/v0.0.1/tools.tapp
```

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

