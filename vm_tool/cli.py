import argparse

def main():
    parser = argparse.ArgumentParser(description='Setup VMs using Ansible.')
    parser.add_argument('--version', action='version', version='vm_tool 1.0')

    args = parser.parse_args()

    # If no arguments are provided, print the help message
    if not vars(args):
        parser.print_help()

if __name__ == '__main__':
    main()