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
    github_username='your_github_username',  # Required if the repository is private, e.g., username
    github_token='your_github_token',        # Required if the repository is private, e.g., token
    github_project_url='your_github_project_url',  # e.g., https://github.com/username/repo
    github_branch='your_branch_name',        # Optional, defaults to 'main'
    docker_compose_file_path='path_to_your_docker_compose_file',  # Optional, defaults to 'docker-compose.yml'
    dockerhub_username='your_dockerhub_username',  # Required if DockerHub login is needed, e.g., dockerhub_user
    dockerhub_password='your_dockerhub_password'   # Required if DockerHub login is needed, e.g., dockerhub_password
)

runner = SetupRunner(config)

runner.run_setup()
```

### **What Happens During Setup**  
The VM Setup Tool will:  
1. Configure Git with GitHub token if provided.
2. Clone the specified GitHub repository to your local machine.  
3. Install **Docker** if it’s not already available on the target machine.  
4. Install **Docker Compose** for managing multi-container applications.  
5. Log in to Docker Hub if credentials are provided.
6. Create, enable, and start the Docker service.  
7. Ensure the Docker container remains active, providing a robust environment for your applications.  

By automating these tasks, the tool minimizes errors and saves time, allowing you to focus on development and deployment.

---

## **Cloud Setup**  
The **VM Setup Tool** also supports cloud setup for VMs. Use the following example to configure and run the cloud setup:

```python
from vm_tool.runner import SetupRunner, SetupRunnerConfig, SSHConfig

config = SetupRunnerConfig(
    github_username='your_github_username',  # Required if the repository is private, e.g., username
    github_token='your_github_token',        # Required if the repository is private, e.g., token
    github_project_url='your_github_project_url',  # e.g., https://github.com/username/repo
    github_branch='your_branch_name',        # Optional, defaults to 'main'
    docker_compose_file_path='path_to_your_docker_compose_file',  # Optional, defaults to 'docker-compose.yml'
    dockerhub_username='your_dockerhub_username',  # Required if DockerHub login is needed, e.g., dockerhub_user
    dockerhub_password='your_dockerhub_password'   # Required if DockerHub login is needed, e.g., dockerhub_password
)

runner = SetupRunner(config)

ssh_configs = [
    SSHConfig(
        ssh_username='your_ssh_username_1',           # e.g., ssh_user_1
        ssh_password='your_ssh_password_1',           # Optional, only use if you don’t want to use SSH key
        ssh_hostname='your_ssh_hostname_1',           # e.g., ssh1.example.com
        ssh_identity_file='/path/to/your/ssh_key_1'   # Optional, path to SSH Identity file
    ),
    SSHConfig(
        ssh_username='your_ssh_username_2',           # e.g., ssh_user_2
        ssh_password='your_ssh_password_2',           # Optional, only use if you don’t want to use SSH key
        ssh_hostname='your_ssh_hostname_2',           # e.g., ssh2.example.com
        ssh_identity_file='/path/to/your/ssh_key_2'   # Optional, path to SSH Identity file
    )
    # Add more SSHConfig instances as needed
]

runner.run_cloud_setup(ssh_configs)
```

### **What Happens During Cloud Setup**  
When you run the cloud setup, the tool will:  
1. Connect to the specified cloud VM using SSH.  
2. Configure Git with GitHub token if provided.
3. Clone the specified GitHub repository to the VM.  
4. Install **Docker** if it’s not already available on the VM.  
5. Install **Docker Compose** for managing multi-container applications.  
6. Log in to Docker Hub if credentials are provided.
7. Create, enable, and start the Docker service on the VM.  
8. Ensure the Docker container remains active, providing a robust environment for your applications.  

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

## Command Line Version Info

If you want to check the installed version of `vm_tool`, you can use the following command:

```bash
vm_tool --version
```

This will print the current version of the package.

---

## Python API Usage

The primary class for using the VM Setup Tool is `SetupRunner`, which orchestrates the entire setup process.

### **Example Usage**  

```python
from vm_tool.runner import SetupRunner, SetupRunnerConfig

config = SetupRunnerConfig(
    # Configuration options
)

runner = SetupRunner(config)

runner.run_setup()
```

### **Configuration Options**  
- `github_username`: Your GitHub username (required for private repositories).
- `github_token`: A GitHub token with repo access (required for private repositories).
- `github_project_url`: The URL of your GitHub project.
- `github_branch`: The branch of the GitHub repository to use.
- `docker_compose_file_path`: Path to your Docker Compose file.
- `dockerhub_username`: Your Docker Hub username (if Docker Hub login is needed).
- `dockerhub_password`: Your Docker Hub password (if Docker Hub login is needed).

### **Methods**  
- `run_setup()`: Executes the VM setup process.
- `run_cloud_setup(ssh_configs)`: Executes the cloud VM setup process using the provided SSH configurations.

---

With its comprehensive features, the **VM Setup Tool** eliminates the hassle of manual configurations and enables seamless integration of VMs into your workflows. Start using the tool today to automate and optimize your virtual machine setup process.