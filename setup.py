#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path
from setuptools import setup, find_packages
import yaml


config = yaml.load(open('./lily/conf/config.yaml').read())

requirements_path = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'requirements.txt')


setup(
    name=config['name'],
    description=config['description'],
    version=config['version'],
    author=config['author'],
    packages=find_packages(),
    install_requires=open(requirements_path).readlines(),
    package_data={'': ['requirements.txt']},
    include_package_data=True,
)
