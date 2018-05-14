#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import os.path
from setuptools import setup, find_packages


config = open('./lily/conf/config.yaml').read()


requirements_path = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'requirements.txt')


def get_config_field(key):
    matched = re.compile(r'{}\:\s*(?P<value>.+)'.format(key)).search(config)

    if matched:
        return matched.group('value').strip()

    else:
        raise Exception('Cound not find config {}'.format(key))


setup(
    name=get_config_field('name'),
    description=get_config_field('description'),
    version=get_config_field('version'),
    author=get_config_field('author'),
    packages=find_packages(),
    install_requires=open(requirements_path).readlines(),
    package_data={'': ['requirements.txt']},
    include_package_data=True,
)
