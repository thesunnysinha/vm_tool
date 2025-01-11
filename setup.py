from setuptools import setup, find_packages

setup(
    name='vm_tool',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'ansible',
        'ansible-runner',
    ],
)