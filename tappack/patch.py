import re
from datetime import datetime
from pathlib import Path

from tappack import constants

PATTERN_VERSION = r'(?P<version>(?P<major>0|[1-9]\d*)\.' \
                  r'(?P<minor>0|[1-9]\d*)\.' \
                  r'(?P<patch>0|[1-9]\d*)' \
                  r'(?:-(?P<pre>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?' \
                  r'(?:\+(?P<build>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?)'


class Version:

    def __init__(self, path, pattern, channel_id, encoding=constants.ENCODING, inc_patch=1):
        self.path = Path(path)
        self.pattern = pattern.format(version=PATTERN_VERSION)
        self.rx = re.compile(self.pattern)
        self.encoding = encoding
        self.channel_id = channel_id
        self.inc_patch = inc_patch

    def version_replacer(self, match):
        build = datetime.now().strftime("%Y.%m.%d-%H.%M.%S")
        major, minor, patch = [int(match.group(name)) for name in ['major', 'minor', 'patch']]
        patch += self.inc_patch
        version = f'{major}.{minor}.{patch}-{self.channel_id}+{build}'
        text = match.group(0).replace(match.group('version'), version)
        return text

    def apply_text(self, text: str):
        print(f'Patching file ({self.__class__.__name__}) "{self.path}"...')

        text = self.rx.sub(self.version_replacer, text)
        return text

    def apply(self, data: bytes):
        text = data.decode(self.encoding)
        text = self.apply_text(text)
        return text.encode(self.encoding)
