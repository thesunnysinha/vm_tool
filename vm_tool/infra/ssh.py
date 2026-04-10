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
        # RejectPolicy refuses unknown hosts; known_hosts must be pre-populated.
        # Use load_system_host_keys() so existing entries are trusted.
        self.client.load_system_host_keys()
        self.client.set_missing_host_key_policy(paramiko.RejectPolicy())

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
        # Write via stdin to avoid any shell interpolation of key contents
        stdin, stdout, stderr = self.client.exec_command(
            "mkdir -p ~/.ssh && chmod 700 ~/.ssh && "
            "tee -a ~/.ssh/authorized_keys > /dev/null && chmod 600 ~/.ssh/authorized_keys"
        )
        stdin.write(public_key.strip() + "\n")
        stdin.channel.shutdown_write()
        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
            err = stderr.read().decode().strip()
            self.client.close()
            raise RuntimeError(
                f"Failed to configure authorized_keys on {vm_ip} (exit {exit_status}): {err}"
            )
        self.client.close()

    def __update_ssh_config(self):
        """
        Updates the local SSH config file with the VM details.
        Sets StrictHostKeyChecking=accept-new so first-connection keys are stored
        but changed keys are rejected (MITM protection).
        """
        config = f"""
Host {self.hostname}
  HostName {self.hostname}
  User {self.username}
  StrictHostKeyChecking accept-new
  IdentityFile {self.private_key_path}
  ForwardAgent yes
"""
        ssh_config_path = os.path.expanduser("~/.ssh/config")
        logger.info(f"Updating SSH config for host {self.hostname}.")
        # Open with O_CREAT|O_APPEND, then enforce 0o600 immediately
        fd = os.open(ssh_config_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        try:
            with os.fdopen(fd, "a") as f:
                f.write(config)
        except Exception:
            os.close(fd)
            raise
        os.chmod(ssh_config_path, 0o600)

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
        Raises RuntimeError if any step fails; no partial state is left.
        """
        logger.info("Starting SSH setup.")
        public_key = self.__read_or_generate_public_key(self.email)
        self.__configure_vm(self.hostname, self.password, public_key)
        self.__update_ssh_config()
        self.__establish_connection()
        self.__close_connection()
        logger.info("SSH setup completed.")
