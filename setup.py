#!/usr/bin/env python

from setuptools import setup

setup(
    name = 'dockbot',
    version = '0.1.4',
    description =
    'A continuous integration system which uses Docker and Buildbot',
    long_description = open('README.md', 'rt').read(),
    author = 'Joseph Coffland',
    author_email = 'joseph@cauldrondevelopment.com',
    platforms = ['any'],
    license = 'GPL 3+',
    url = 'https://github.com/CauldronDevelopmentLLC/dockbot',
    packages = ['dockbot'],
    include_package_data = True,
    eager_resources = ['dockbot/data/*'],
    entry_points = {
        'console_scripts': [
            'dockbot = dockbot:run',
            'dockbot-publish = dockbot.publish:run',
            'github-release = dockbot.github:run',
            ]
        },
    install_requires = ['requests'],
    )
