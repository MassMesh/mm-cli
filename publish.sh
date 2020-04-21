#!/bin/bash
# For further instructions on setting up a Pypi account, etc. see the following:
# https://packaging.python.org/tutorials/packaging-projects/
python setup.py sdist bdist_wheel
twine upload --repository-url https://test.pypi.org/legacy/ ./dist/*
