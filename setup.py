#!/usr/bin/env python3
# =============================================================================
# @file    setup.py
# @brief   Installation setup file
# @created 2022-12-08
# @license Please see the file named LICENSE in the project directory
# @website https://github.com/caltechlibrary/iga
#
# Note: the full configuration metadata is maintained in setup.cfg, not here.
# This file exists to hook in setup.cfg and requirements.txt, so that the
# requirements don't have to be repeated and so that "python3 setup.py" works.
# =============================================================================

import os
from os import path
from setuptools import setup


def vendored_version(requirement_path):
    name = requirement_path.split('/')[-1]
    return f'{name}@file://{os.getcwd()}/{requirement_path}'


def requirements(file):
    required = []
    requirements_file = path.join(path.abspath(path.dirname(__file__)), file)
    if path.exists(requirements_file):
        with open(requirements_file, encoding='utf-8') as f:
            lines = [line for line in filter(str.strip, f.read().splitlines())
                     if not line.startswith('#')]
        # If the requirements.txt uses pip features, try to use pip's parser.
        if (any(item.startswith(('-', '.', '/')) for item in lines)
                or any('https' in item for item in required)):
            try:
                from pip._internal.req import parse_requirements
                from pip._internal.network.session import PipSession
                parsed = parse_requirements(requirements_file, PipSession())
                required = [item.requirement.strip() for item in parsed]
            except ImportError:
                # No pip, or not the expected version. Give up & return as-is.
                pass

    # Turn local paths (which work in pip) into setuptools-compatible paths.
    return [(vendored_version(item) if item.startswith('./') else item)
            for item in required]


setup(
    setup_requires=['wheel'],
    install_requires=requirements('requirements.txt'),
)
