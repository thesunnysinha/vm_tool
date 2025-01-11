from setuptools import setup, find_packages

setup(
    name='vm_tool',
    version='0.5',
    packages=find_packages(),
    description='A tool to setup VMs using Ansible.',
    long_description='''
    This is a tool to setup VMs using Ansible.

    Example usage:

    from vm_tool import SetupRunner

    runner = SetupRunner(
        ssh_host='your_host', # e.g. 192.168.1.1
        ssh_user='your_user', # e.g. root
        ssh_password='your_password', # e.g. password
        become_pass='your_become_pass', # e.g. password
        github_username='your_github_username', # e.g. username
        github_token='your_github_token', # e.g. token
        github_project_url='your_github_project_url' # e.g. https://github.com/username/repo
    )

    runner.run_setup()
    ''',
    long_description_content_type='text/markdown',
    install_requires=[
        'ansible',
        'ansible-runner',
    ],
    entry_points={
        'console_scripts': [
            'vm_tool=vm_tool.cli:main',
        ],
    },
    license='MIT',
)