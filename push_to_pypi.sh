#!/bin/bash

rm -rf dist
pip install twine  
mkdir dist  
python setup.py sdist
twine upload dist/* --verbose