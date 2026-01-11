import logging
import os
import subprocess

import paramiko

# Configure logging
logger = logging.getLogger(__name__)


class SSHSetup:
    """
    A class to set up SSH configuration and keys for a VM.

    Attributes:
        hostname (str): The hostname of the VM.
        username (str): The username for SSH login.
        password (str): The password for SSH login.
        email (str): The email for SSH key generation.
        private_key_path (str): The path to the private SSH key.
        client (paramiko.SSHClient): The SSH client.
    """

    def __init__(self, hostname, username, password, email):
        """
        The constructor for SSHSetup class.

        Parameters:
            hostname (str): The hostname of the VM.
            username (str): The username for SSH login.
            password (str): The password for SSH login.
            email (str): The email for SSH key generation.
        """
        self.hostname = hostname
        self.username = username
        self.password = password
        self.email = email
        self.private_key_path = os.path.expanduser("~/.ssh/id_rsa")
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # nosec B507

    def __generate_ssh_key(self, email):
        """
        Generates an SSH key pair.

        Parameters:
            email (str): The email for SSH key generation.
        """

        logger.info(f"Generating SSH key for email: {email}")
        try:
            subprocess.run(
                [
                    "ssh-keygen",
                    "-t",
                    "rsa",
                    "-b",
                    "4096",
                    "-C",
                    email,
                    "-f",
                    self.private_key_path,
                    "-N",
                    "",
                ],
                check=True,
                capture_output=True,
            )
            logger.info("SSH key generated successfully.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to generate SSH key: {e.stderr.decode()}")
            raise RuntimeError(f"Failed to generate SSH key: {e.stderr.decode()}")

    def __read_or_generate_public_key(self, email) -> str:
        """
        Reads the public SSH key or generates a new one if it doesn't exist.

        Parameters:
            email (str): The email for SSH key generation.

        Returns:
            str: The public SSH key.
        """
        public_key_path = f"{self.private_key_path}.pub"
        if not os.path.exists(public_key_path):
            self.__generate_ssh_key(email)
        with open(public_key_path, "r") as file:
            logger.info(f"Reading public key from {public_key_path}")
            return file.read()

    def __configure_vm(self, vm_ip, vm_password, public_key):
        """
        Configures the VM by adding the public SSH key to the authorized keys.

        Parameters:
            vm_ip (str): The IP address of the VM.
            vm_password (str): The password for the VM.
            public_key (str): The public SSH key.
        """
        logger.info(f"Configuring VM at {vm_ip} with provided public key.")
        self.client.connect(vm_ip, username=self.username, password=vm_password)
        self.client.exec_command(
            f'echo "{public_key}" >> ~/.ssh/authorized_keys'
        )  # nosec B601
        self.client.close()

    def __update_ssh_config(self):
        """
        Updates the local SSH config file with the VM details.
        """
        config = f"""
Host {self.hostname}
  HostName {self.hostname}
  User {self.username}
  StrictHostKeyChecking no
  IdentityFile {self.private_key_path}
  ForwardAgent yes
"""
        logger.info(f"Updating SSH config for host {self.hostname}.")
        with open(f'{os.path.expanduser("~")}/.ssh/config', "a") as file:
            file.write(config)

    def __establish_connection(self):
        """
        Establishes an SSH connection to the VM.
        """
        logger.info(f"Establishing SSH connection to {self.hostname}.")
        self.client.connect(
            self.hostname, username=self.username, key_filename=self.private_key_path
        )

    def __close_connection(self):
        """
        Closes the SSH connection.
        """
        if self.client:
            logger.info("Closing SSH connection.")
            self.client.close()

    def setup(self):
        """
        Sets up the SSH configuration and keys for the VM.
        """
        logger.info("Starting SSH setup.")
        public_key = self.__read_or_generate_public_key(self.email)
        self.__configure_vm(self.hostname, self.password, public_key)
        self.__update_ssh_config()
        self.__establish_connection()
        self.__close_connection()
        logger.info("SSH setup completed.")
