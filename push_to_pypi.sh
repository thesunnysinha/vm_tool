#!/bin/bash

rm -rf dist
pip install twine    
python setup.py sdist
twine upload dist/*