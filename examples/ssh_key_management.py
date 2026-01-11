"""
Example: SSH Key Management for a VM.
- Generates an SSH key pair (if not present), configures the VM for SSH access, and updates local SSH config.
- Useful for preparing a VM for secure, passwordless SSH access.
"""

from vm_tool.ssh import SSHSetup


def main():
    ssh_setup = SSHSetup(
        hostname="your_vm_hostname",
        username="your_vm_username",
        password="your_vm_password",
        email="your_email_for_ssh_key",
    )

    ssh_setup.setup()


if __name__ == "__main__":
    main()
