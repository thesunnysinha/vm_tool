from vm_tool.ssh import SSHSetup

runner = SSHSetup(
    username='root',        # e.g., ssh_user
    password='1vOdMvb4I891',        # e.g., ssh_password
    hostname='45.79.127.191',         # e.g., ssh.example.com
    email='thesunnysinha@gmail.com'
)

runner.setup()