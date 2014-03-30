#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Setup script for Streams.
"""


from sys import version_info as python_version
from setuptools import setup, find_packages


##############################################################################


REQUIREMENTS = [
    "six==1.6.1",
    "repoze.lru==0.6"
]


##############################################################################


if python_version < (2, 7):
    REQUIREMENTS.append("unittest2==0.5.1")
if python_version < (3,):
    REQUIREMENTS.append("futures==2.1.6")


##############################################################################


setup(
    name="pystreams",
    description="Streams inspired by Java 8",
    version="0.6",
    author="Sergey Arkhipov",
    license="MIT",
    author_email="serge@aerialsounds.org",
    maintainer="Sergey Arkhipov",
    packages=find_packages(),
    maintainer_email="serge@aerialsounds.org",
    url="https://github.com/9seconds/streams/",
    install_requires=REQUIREMENTS,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Software Development :: Libraries",
    ],
    zip_safe=True
)
