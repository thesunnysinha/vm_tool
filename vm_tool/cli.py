# filepath: /Users/sunnysinha/Desktop/Projects/vm_setup/vm_tool/cli.py
import argparse
from vm_tool import SetupRunner

def main():
    parser = argparse.ArgumentParser(description='Setup VMs using Ansible.')
    parser.add_argument('--ssh_host', required=True, help='SSH host (e.g. 192.168.1.1)')
    parser.add_argument('--ssh_user', required=True, help='SSH user (e.g. root)')
    parser.add_argument('--ssh_password', required=True, help='SSH password')
    parser.add_argument('--become_pass', required=True, help='Become password')
    parser.add_argument('--github_username', required=True, help='GitHub username')
    parser.add_argument('--github_token', required=True, help='GitHub token')
    parser.add_argument('--github_project_url', required=True, help='GitHub project URL (e.g. https://github.com/username/repo)')

    args = parser.parse_args()

    runner = SetupRunner(
        ssh_host=args.ssh_host,
        ssh_user=args.ssh_user,
        ssh_password=args.ssh_password,
        become_pass=args.become_pass,
        github_username=args.github_username,
        github_token=args.github_token,
        github_project_url=args.github_project_url
    )

    runner.run_setup()

if __name__ == '__main__':
    main()