#!/bin/bash
# For further instructions on setting up a Pypi account, etc. see the following:
# https://packaging.python.org/tutorials/packaging-projects/
rm -rf dist
python setup.py sdist bdist_wheel
twine upload dist/*
