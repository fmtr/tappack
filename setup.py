from pathlib import Path

from setuptools import find_packages, setup

packages = find_packages()
name = next(iter(packages))
path_base = Path(__file__).absolute().parent
path = path_base / name / 'version'
__version__ = path.read_text().strip()

setup(
    long_description=(path_base / 'README.md').read_text(),
    long_description_content_type='text/markdown',
    name=name,
    version=__version__,
    url=f'https://link.frontmatter.ai/{name}',
    license='Copyright © 2023 Frontmatter. All rights reserved.',
    author='Frontmatter',
    description='A packager for Tasmota Berry Application (TAPP) apps',
    keywords='development berry script tasmota tapp',
    packages=packages,
    package_data={
        name: [f'version', 'autoexec.be.template'],
    },
    install_requires=[
        'requests',
        'click',
        'pyyaml'
    ],
    extras_require={
        'server': [
            'flask',
            'pyngrok'
        ]
    },
    entry_points={
        'console_scripts': [
            f'{name} = {name}.packaging:main',
            f'{name}-server = {name}.server:main',
        ],
    }
)
