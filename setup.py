from setuptools import setup, find_packages
import os

# Read the contents of README.md
readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
if os.path.exists(readme_path):
    with open(readme_path, encoding='utf-8') as f:
        long_description = f.read()
else:
    long_description = ''

setup(
    name='vm_tool',
    version='1.0.28',  # This will be updated by bump2version
    packages=find_packages(),
    description='A Comprehensive Tool for Setting Up Virtual Machines.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=[
        'ansible',
        'ansible-runner',
        'paramiko',
        'pydantic',
        'pyyaml'
    ],
    extras_require={
        'dev': [
            'pytest',
            'flake8',
            'bump2version'
        ]
    },
    entry_points={
        'console_scripts': [
            'vm_tool=vm_tool.cli:main',
        ],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Topic :: Software Development :: Build Tools',
        'Topic :: System :: Systems Administration',
    ],
    python_requires='>=3.6',
    keywords='virtual machine setup ansible automation',
    license='MIT',
    include_package_data=True,
    url='https://github.com/thesunnysinha/vm_tool',
    project_urls={
        'Documentation': 'https://github.com/thesunnysinha/vm_tool/README.md',
        'Source': 'https://github.com/thesunnysinha/vm_tool',
        'Tracker': 'https://github.com/thesunnysinha/vm_tool/issues',
    },
    author='Sunny Sinha',
    author_email='thesunnysinha@gmail.com',
)