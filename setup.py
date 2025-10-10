"""
Backward compatibility setup.py for wagtail-seotoolkit.
All configuration is now in pyproject.toml.
"""

from setuptools import find_packages, setup

setup(
    packages=find_packages(where="src"),
    package_dir={"": "src"},
)

