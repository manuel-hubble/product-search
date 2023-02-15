#!/usr/bin/env python

from setuptools import find_packages, setup

setup(
    name="product-search",
    packages=find_packages(),
    version="1.0.0",
    description="Product search POC",
    author="Hubble Team",
    license="Proprietary",
    include_package_data=True,
    install_requires=requirements,
    python_requires="==3.10",
)

