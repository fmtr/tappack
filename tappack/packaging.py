from pathlib import Path

import click

from tappack import source


@click.command()
@click.option('--module-path', type=click.Path(exists=True, file_okay=False), required=True,
              help='Path to your module, containing any Berry files, manifests, assets, etc. Example: /usr/src/my_berry_project')
@click.option('--output', type=click.Path(dir_okay=False),
              help='Path to write the output .tapp package. Example: ~/my_project.tapp')
@click.option('--channel-id', type=str,
              help='Identifier for the release channel. Only relevant if your manifests contain release channel information. Example: development')
def main(module_path, output, channel_id):
    module_path = Path(module_path)
    if output is not None:
        output = Path(output)
    path_source = source.LocalPath(module_path, channel_id=channel_id)
    path_source.write(output)

if __name__ == '__main__':
    main()
