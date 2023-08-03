import re
import threading
from pathlib import Path
from time import sleep

import click

from tappack.constants import CODE_MASK_DEFAULT
from tappack.source import LocalPath

try:
    from flask import Flask, send_file
    from tappack.tunnel import Tunnel
except ImportError as exception:  # pragma: no cover
    msg = f'Running tappack server requires additional dependencies. ' \
          f'To install them, run: pip install tappack[server] --upgrade'
    raise ImportError(msg) from exception

CHANNEL_ID_NONE = 'none'

class TappServer:

    def __init__(self, paths, port=8080, channel_id=None):

        self.port = port
        self.paths = paths

        self.packagers = {
            (p := LocalPath(path, channel_id=channel_id)).name: p
            for path in self.paths
        }

        self.app = Flask(self.__class__.__name__)
        self.app.route('/<download_name>')(self.serve_tapp)
        self.thread = threading.Thread(target=self.start_app)
        self.start()

    def start(self):
        self.thread.start()

    def start_app(self):
        self.app.run(port=self.port)

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.close()

    def wait(self):
        while self.thread.is_alive():
            sleep(1)

    def serve_tapp(self, download_name):

        name = Path(download_name).stem

        if name not in self.packagers:
            return f'Unknown project "{name}"'

        packager: LocalPath = self.packagers[name]
        archive_data = packager.build_archive()

        response = send_file(archive_data, as_attachment=True, download_name=download_name)
        return response


def start(paths, port, channel_id):
    with TappServer(paths, port, channel_id=channel_id) as tapp_server:
        with Tunnel(port) as tunnel:
            for name, packager in tapp_server.packagers.items():
                url_tapp = f'{tunnel.tunnel.public_url}/{name}.tapp'
                code_mask = packager.code_mask or CODE_MASK_DEFAULT
                code_mask = re.sub(r'\s+', ' ', code_mask).strip()
                code_snippet = code_mask.format(url=url_tapp, name=name)
                msg = f'Serving project "{name}": `{code_snippet}`'
                print(msg)
            tapp_server.wait()


@click.command()
@click.option('--project', '-p', multiple=True, metavar='PATH', required=True)
@click.option('--port', '-pt', default=8080, show_default=True)
@click.option('--channel-id', '-id', type=str, default='development',
              help='Identifier for the release channel. '
                   'Only relevant if your manifests contain release channel information. Example: development'
              )
def main(project, port, channel_id):
    if channel_id == CHANNEL_ID_NONE:
        channel_id = None

    start(project, port, channel_id)


if __name__ == '__main__':
    main()
