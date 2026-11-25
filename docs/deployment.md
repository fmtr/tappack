# Serving and remote access

`tappack` creates `.tapp` files; it no longer starts a web server or opens a tunnel. The former server feature was convenient during development, but it coupled an artifact builder to a long-running web process and a public-network tunnel. That added dependencies and operational behavior that packaging itself does not need, while making it easier to expose project files unintentionally.

Keep the responsibilities separate: build the archive with `tappack`, then publish it through a deployment or static-hosting workflow you already control. For temporary remote device access, use a separately managed tunnel tool such as `tailcat` rather than embedding tunnel lifecycle and exposure decisions in the packager.

The packaging command and manifest behavior are documented in the [quick start](quick-start.md) and [manifest reference](manifest.md).
