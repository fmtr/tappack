from typing import ClassVar

from pydantic import Field, field_validator

from corio import Path, sets
from tappack.package import Package
from tappack.paths import paths


class Settings(sets.Base, cli_parse_args=True, cli_kebab_case=True):
    paths: ClassVar = paths

    module_path: Path = Field(default_factory=Path.cwd)
    output: Path | None = None
    channel_id: str | None = None

    @field_validator("module_path")
    @classmethod
    def require_module_directory(cls, path: Path) -> Path:
        if not path.is_dir():
            raise ValueError(f'Module path "{path}" is not a directory.')
        return path.resolve()

    async def run(self) -> Path:
        package = Package(self.module_path, channel_id=self.channel_id)
        output = self.output or (Path.cwd() / f"{package.name}.tapp")
        return package.write(output)


def main() -> None:
    settings = Settings()
    settings.launch()
