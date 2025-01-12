from setuptools import setup, find_packages
import os

# Read the contents of README.md
readme_path = os.path.join(os.path.dirname(__file__), 'Readme.md')
if os.path.exists(readme_path):
    with open(readme_path, encoding='utf-8') as f:
        long_description = f.read()
else:
    long_description = ''

setup(
    name='vm_tool',
    version='1.0.10',  # This will be updated by bump2version
    packages=find_packages(),
    description='A Comprehensive Tool for Setting Up Virtual Machines Using Ansible.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=[
        'ansible',
        'ansible-runner',
        'paramiko'
    ],
    entry_points={
        'console_scripts': [
            'vm_tool=vm_tool.cli:main',
        ],
    },
    license='MIT',
    include_package_data=True,
)