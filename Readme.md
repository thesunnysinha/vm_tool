### Welcome to initial setup of the application

1. Connect to deployment maching using VSCode.

2. Run below commnads on deployment machine:
```bash
sudo apt update && sudo apt upgrade -y && sudo apt install -y git ansible sshpass
```


6. Environment Variable required:
```bash
export ANSIBLE_SSH_HOST="HOST_IP"
export ANSIBLE_SSH_USER=""
export ANSIBLE_SSH_PASS=""
export ANSIBLE_BECOME_PASS=""
export GITHUB_USERNAME=""
export GITHUB_TOKEN=""
export GITHUB_PROJECT_URL=""
clear
```

7. Run below commands on deployment machine after cloning repository:
```bash
ansible-playbook vm_setup/setup.yml -i vm_setup/inventory.yml --ssh-extra-args='-o StrictHostKeyChecking=no'
```

```bash
ansible-playbook vm_setup/setup.yml -i vm_setup/inventory.yml --ssh-extra-args='-o StrictHostKeyChecking=no' -vvv
```


#System Management
sudo systemctl daemon-reload
sudo systemctl enable project.service
sudo systemctl start project.service
sudo systemctl status project.service