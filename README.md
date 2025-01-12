# **VM Setup Tool**  
### **A Comprehensive Solution for Streamlining Virtual Machine Configuration**

## **Overview**  
The **VM Setup Tool** is an efficient, user-friendly solution designed to simplify the process of setting up and managing virtual machines (VMs) using Ansible. Ideal for automating VM deployment and configuration, this tool ensures consistency and enhances operational efficiency across your infrastructure.

---

## **Pre-requisites**  
This tool supports projects utilizing **Docker Compose**. Ensure that a `docker-compose.yml` file is present at the root of your project directory before proceeding.

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
from vm_tool.runner import SetupRunner

runner = SetupRunner(
    github_username='your_github_username',  # e.g., username
    github_token='your_github_token',        # e.g., token
    github_project_url='your_github_project_url'  # e.g., https://github.com/username/repo
)

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
