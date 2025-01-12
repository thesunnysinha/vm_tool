from vm_tool.ssh import SSHSetup

ssh_setup = SSHSetup(
    hostname='170.187.238.32',  # e.g., vm.example.com
    username='root',  # e.g., user
    password='1vOdMvb4I891',  # e.g., password
    email='thesunnysinha@gmail.com'  # e.g., user@example.com
)

ssh_setup.setup()