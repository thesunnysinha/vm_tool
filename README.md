# **VM Setup Tool**  
### **A Comprehensive Solution for Streamlining Virtual Machine Configuration**

## **Overview**  
The **VM Setup Tool** is an efficient, user-friendly solution designed to simplify the process of setting up and managing virtual machines (VMs) using Ansible. Ideal for automating VM deployment and configuration, this tool ensures consistency and enhances operational efficiency across your infrastructure.

---

## **Pre-requisites**  
This tool supports projects utilizing **Docker Compose**.

---

## **Installation**  
Install the VM Setup Tool using **pip**, the Python package manager:  

```bash
pip install vm-tool
```

---

## **Example Usage**  

### **Automated VM Setup**  
Use the following example to configure and run the VM setup:  

```python
from vm_tool.runner import SetupRunner, SetupRunnerConfig

config = SetupRunnerConfig(
    github_username='your_github_username',  # e.g., username
    github_token='your_github_token',        # e.g., token
    github_project_url='your_github_project_url',  # e.g., https://github.com/username/repo
    docker_compose_file_path='path_to_your_docker_compose_file'  # Optional, defaults to 'docker-compose.yml'
)

runner = SetupRunner(config)

runner.run_setup()
```

### **What Happens During Setup**  
The VM Setup Tool will:  
1. Clone the specified GitHub repository to your local machine.  
2. Install **Docker** if it’s not already available on the target machine.  
3. Install **Docker Compose** for managing multi-container applications.  
4. Create, enable, and start the Docker service.  
5. Ensure the Docker container remains active, providing a robust environment for your applications.  

By automating these tasks, the tool minimizes errors and saves time, allowing you to focus on development and deployment.

---

## **Cloud Setup**  
The **VM Setup Tool** also supports cloud setup for VMs. Use the following example to configure and run the cloud setup:

```python
from vm_tool.runner import SetupRunner, SetupRunnerConfig, SSHConfig

config = SetupRunnerConfig(
    github_username='your_github_username',  # e.g., username
    github_token='your_github_token',        # e.g., token
    github_project_url='your_github_project_url',  # e.g., https://github.com/username/repo
    docker_compose_file_path='path_to_your_docker_compose_file'  # Optional, defaults to 'docker-compose.yml'
)

runner = SetupRunner(config)

ssh_configs = [
    SSHConfig(
        ssh_username='your_ssh_username_1',        # e.g., ssh_user_1
        ssh_password='your_ssh_password_1',        # e.g., ssh_password_1
        ssh_hostname='your_ssh_hostname_1'         # e.g., ssh1.example.com
    ),
    SSHConfig(
        ssh_username='your_ssh_username_2',        # e.g., ssh_user_2
        ssh_password='your_ssh_password_2',        # e.g., ssh_password_2
        ssh_hostname='your_ssh_hostname_2'         # e.g., ssh2.example.com
    )
    # Add more SSHConfig instances as needed
]

runner.run_cloud_setup(ssh_configs)
```

### **What Happens During Cloud Setup**  
When you run the cloud setup, the tool will:  
1. Connect to the specified cloud VM using SSH.  
2. Clone the specified GitHub repository to the VM.  
3. Install **Docker** if it’s not already available on the VM.  
4. Install **Docker Compose** for managing multi-container applications.  
5. Create, enable, and start the Docker service on the VM.  
6. Ensure the Docker container remains active, providing a robust environment for your applications.  

---

## **SSH Client Feature**  
The **VM Setup Tool** also includes a dedicated **SSH client** feature to simplify the configuration of SSH access for VMs, including automated SSH key generation and management.

### **Example Usage**  

```python
from vm_tool.ssh import SSHSetup

ssh_setup = SSHSetup(
    hostname='your_vm_hostname',  # e.g., vm.example.com
    username='your_vm_username',  # e.g., user
    password='your_vm_password',  # e.g., password
    email='your_email_for_ssh_key'  # e.g., user@example.com
)

ssh_setup.setup()
```

### **What Happens During SSH Setup**  
When you run the SSH setup, the tool will:  
1. Generate an SSH key pair if none exists.  
2. Read the public SSH key or create a new one if necessary.  
3. Configure the VM by adding the public key to the VM's **authorized_keys** file.  
4. Update the local SSH configuration file with the VM's details.  
5. Establish an SSH connection to verify the setup.  
6. Close the connection once setup is complete.  

---

With its comprehensive features, the **VM Setup Tool** eliminates the hassle of manual configurations and enables seamless integration of VMs into your workflows. Start using the tool today to automate and optimize your virtual machine setup process.