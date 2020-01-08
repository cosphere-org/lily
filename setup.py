#!/usr/bin/env python

import json
import os.path
from setuptools import setup, find_packages


BASE_DIR = os.path.dirname(os.path.realpath(__file__))


#
# REQUIREMENTS
#
def parse_requirements(requirements):

    return [
        r.strip()
        for r in requirements
        if (
            not r.strip().startswith('#') and
            not r.strip().startswith('-e') and
            r.strip())
    ]


with open(os.path.join(BASE_DIR, 'requirements.txt')) as f:
    requirements = parse_requirements(f.readlines())


#
# CONFIG
#
with open(os.path.join(BASE_DIR, '.lily', 'config.json')) as f:
    config = json.loads(f.read())


setup(
    name=config['name'],
    packages=find_packages(),
    description='Lily MicroService Framework for Humans',
    url=config['repository'],
    version=config['version'],
    author='CoSphere Team',
    author_email='contact@cosphere.org',
    install_requires=requirements,
    data_files=[(
        '',
        [
            'requirements.txt',
            'README.md',
            '.lily/config.json',
            'lily/cli/base.makefile',
            'lily/search/detector/data/language_codes.yaml',
            'lily/search/detector/data/language_to_configuration_map.yaml',
            'lily/docs/renderers/markdown/base.md',
            'lily/search/stopwords/pl.json',
        ],
    )],
    include_package_data=True,
    entry_points='''
        [console_scripts]
        lily=lily.cli.cli:cli
    ''',
    keywords=['lily', 'microservice', 'django', 'drf'],
    classifiers=[])
