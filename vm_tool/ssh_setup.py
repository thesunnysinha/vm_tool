import os
import paramiko

class SSHSetup:
    def __init__(self, hostname, username, password, email):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.email = email
        self.private_key_path = os.path.expanduser('~/.ssh/id_rsa')
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def _generate_ssh_key(self, email):
        os.system(f'ssh-keygen -t rsa -b 4096 -C "{email}"')

    def _read_or_generate_public_key(self, email):
        public_key_path = f'{self.private_key_path}.pub'
        if not os.path.exists(public_key_path):
            self._generate_ssh_key(email)
        with open(public_key_path, 'r') as file:
            return file.read()

    def _configure_vm(self, vm_ip, vm_password, public_key):
        self.client.connect(vm_ip, username=self.username, password=vm_password)
        self.client.exec_command(f'echo "{public_key}" >> ~/.ssh/authorized_keys')
        self.client.close()

    def _update_ssh_config(self):
        config = f"""
Host {self.hostname}
  HostName {self.hostname}
  User {self.username}
  StrictHostKeyChecking no
  IdentityFile {self.private_key_path}
  ForwardAgent yes
"""
        with open(f'{os.path.expanduser("~")}/.ssh/config', 'a') as file:
            file.write(config)

    def _establish_connection(self):
        self.client.connect(self.hostname, username=self.username, key_filename=self.private_key_path)

    def _close_connection(self):
        if self.client:
            self.client.close()

    def setup(self):
        public_key = self._read_or_generate_public_key(self.email)
        self._configure_vm(self.hostname, self.password, public_key)
        self._update_ssh_config()
        self._establish_connection()
        self._close_connection()