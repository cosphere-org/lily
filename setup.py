#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path
from setuptools import setup, find_packages


SERVICE_NAME = 'lily'


requirements_path = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'requirements.txt')


setup(
    name=SERVICE_NAME,
    description='Lily',
    version='0.1.15',
    author='CoSphere Tech Team',
    packages=find_packages(),
    install_requires=open(requirements_path).readlines(),
    package_data={'': ['requirements.txt']},
    include_package_data=True,
)
