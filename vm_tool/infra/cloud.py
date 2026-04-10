"""Multi-cloud support framework (AWS, GCP, Azure).

Each provider implements instance lifecycle only: provision, status, terminate.
Application setup after provisioning is handled by run_cloud_setup() + Ansible.
"""

import logging
import time
from typing import Any, Dict
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class CloudProvider(ABC):
    """Base class for cloud providers."""

    @abstractmethod
    def deploy_vm(self, config: Dict[str, Any]) -> str:
        """Provision VM and return instance ID / resource name."""

    @abstractmethod
    def get_vm_status(self, instance_id: str) -> str:
        """Return current state string (e.g. 'running', 'stopped')."""

    @abstractmethod
    def terminate_vm(self, instance_id: str) -> bool:
        """Terminate / delete VM. Returns True on success."""


class AWSProvider(CloudProvider):
    """AWS EC2 cloud provider (requires boto3).

    Install with: pip install vm-tool[aws]

    Example::

        from vm_tool.infra.cloud import AWSProvider
        p = AWSProvider(region="us-east-1")
        instance_id = p.deploy_vm({
            "image_id": "ami-0c55b159cbfafe1f0",
            "instance_type": "t2.micro",
            "key_name": "my-key",
            "security_groups": ["sg-12345678"],
        })
        print(p.get_vm_status(instance_id))  # "running"
        p.terminate_vm(instance_id)
    """

    def __init__(self, region: str = "us-east-1"):
        try:
            import boto3
            self.client = boto3.client("ec2", region_name=region)
        except ImportError:
            raise ImportError(
                "boto3 is required for AWS support. "
                "Install with: pip install vm-tool[aws]"
            )
        self.region = region
        logger.info(f"AWS provider initialized (region: {region})")

    def deploy_vm(self, config: Dict[str, Any]) -> str:
        """Launch an EC2 instance and return its instance ID.

        Args:
            config: Dict with keys:
                image_id (str): AMI ID (default: Amazon Linux 2 us-east-1)
                instance_type (str): Instance type (default: t2.micro)
                key_name (str): Existing EC2 key pair name (required for SSH)
                security_groups (list): List of security group IDs
                tags (dict): Tag key/value pairs (Name tag auto-added)
        """
        image_id = config.get("image_id", "ami-0c55b159cbfafe1f0")
        instance_type = config.get("instance_type", "t2.micro")
        key_name = config.get("key_name")
        security_groups = config.get("security_groups", [])
        tags = {"Name": "vm-tool-managed", **config.get("tags", {})}

        kwargs: Dict[str, Any] = {
            "ImageId": image_id,
            "InstanceType": instance_type,
            "MinCount": 1,
            "MaxCount": 1,
            "TagSpecifications": [{
                "ResourceType": "instance",
                "Tags": [{"Key": k, "Value": v} for k, v in tags.items()],
            }],
        }
        if key_name:
            kwargs["KeyName"] = key_name
        if security_groups:
            kwargs["SecurityGroupIds"] = security_groups

        response = self.client.run_instances(**kwargs)
        instance_id = response["Instances"][0]["InstanceId"]
        logger.info(f"EC2 instance launched: {instance_id}")

        waiter = self.client.get_waiter("instance_running")
        waiter.wait(InstanceIds=[instance_id])
        logger.info(f"EC2 instance running: {instance_id}")
        return instance_id

    def get_vm_status(self, instance_id: str) -> str:
        """Return the EC2 instance state name (e.g. 'running', 'stopped')."""
        resp = self.client.describe_instances(InstanceIds=[instance_id])
        return resp["Reservations"][0]["Instances"][0]["State"]["Name"]

    def terminate_vm(self, instance_id: str) -> bool:
        """Terminate an EC2 instance. Waits for termination to complete."""
        self.client.terminate_instances(InstanceIds=[instance_id])
        waiter = self.client.get_waiter("instance_terminated")
        waiter.wait(InstanceIds=[instance_id])
        logger.info(f"EC2 instance terminated: {instance_id}")
        return True


class GCPProvider(CloudProvider):
    """GCP Compute Engine provider (requires google-cloud-compute).

    Install with: pip install vm-tool[gcp]
    """

    def __init__(self, project_id: str, zone: str = "us-central1-a"):
        try:
            from google.cloud import compute_v1
            self._instances = compute_v1.InstancesClient()
        except ImportError:
            raise ImportError(
                "google-cloud-compute is required for GCP support. "
                "Install with: pip install vm-tool[gcp]"
            )
        self.project_id = project_id
        self.zone = zone
        logger.info(f"GCP provider initialized (project: {project_id}, zone: {zone})")

    def deploy_vm(self, config: Dict[str, Any]) -> str:
        """Create a GCE instance and return its name.

        Args:
            config: Dict with keys:
                name (str): Instance name (default: vm-tool-instance)
                machine_type (str): Machine type (default: n1-standard-1)
                image_family (str): Image family (default: debian-11)
                image_project (str): Image project (default: debian-cloud)
                disk_size_gb (int): Boot disk size in GB (default: 10)
        """
        from google.cloud import compute_v1

        name = config.get("name", "vm-tool-instance")
        machine_type = config.get("machine_type", "n1-standard-1")
        image_family = config.get("image_family", "debian-11")
        image_project = config.get("image_project", "debian-cloud")
        disk_size_gb = config.get("disk_size_gb", 10)

        instance = compute_v1.Instance()
        instance.name = name
        instance.machine_type = (
            f"zones/{self.zone}/machineTypes/{machine_type}"
        )

        disk = compute_v1.AttachedDisk()
        disk.boot = True
        disk.auto_delete = True
        params = compute_v1.AttachedDiskInitializeParams()
        params.source_image = (
            f"projects/{image_project}/global/images/family/{image_family}"
        )
        params.disk_size_gb = disk_size_gb
        disk.initialize_params = params
        instance.disks = [disk]

        network_interface = compute_v1.NetworkInterface()
        network_interface.name = "global/networks/default"
        access_config = compute_v1.AccessConfig()
        access_config.name = "External NAT"
        network_interface.access_configs = [access_config]
        instance.network_interfaces = [network_interface]

        operation = self._instances.insert(
            project=self.project_id, zone=self.zone, instance_resource=instance
        )
        # Wait for the operation (LRO)
        operation.result(timeout=300)
        logger.info(f"GCE instance created: {name}")
        return name

    def get_vm_status(self, instance_id: str) -> str:
        """Return GCE instance status string (e.g. 'RUNNING', 'TERMINATED')."""
        instance = self._instances.get(
            project=self.project_id, zone=self.zone, instance=instance_id
        )
        return instance.status

    def terminate_vm(self, instance_id: str) -> bool:
        """Delete a GCE instance."""
        operation = self._instances.delete(
            project=self.project_id, zone=self.zone, instance=instance_id
        )
        operation.result(timeout=300)
        logger.info(f"GCE instance deleted: {instance_id}")
        return True


class AzureProvider(CloudProvider):
    """Azure VM provider (requires azure-mgmt-compute + azure-identity).

    Install with: pip install vm-tool[azure]
    """

    def __init__(self, subscription_id: str, resource_group: str):
        try:
            from azure.identity import DefaultAzureCredential
            from azure.mgmt.compute import ComputeManagementClient
            credential = DefaultAzureCredential()
            self.compute_client = ComputeManagementClient(credential, subscription_id)
        except ImportError:
            raise ImportError(
                "azure-mgmt-compute and azure-identity are required for Azure support. "
                "Install with: pip install vm-tool[azure]"
            )
        self.subscription_id = subscription_id
        self.resource_group = resource_group
        logger.info(f"Azure provider initialized (subscription: {subscription_id})")

    def deploy_vm(self, config: Dict[str, Any]) -> str:
        """Create an Azure VM and return its name.

        Args:
            config: Dict with keys:
                name (str): VM name (required)
                location (str): Azure region (default: eastus)
                vm_size (str): VM size (default: Standard_B1s)
                admin_username (str): Admin username (default: azureuser)
                admin_password (str): Admin password (required)
                image (dict): Image reference dict with publisher/offer/sku/version
        """
        name = config["name"]
        location = config.get("location", "eastus")
        vm_size = config.get("vm_size", "Standard_B1s")
        admin_username = config.get("admin_username", "azureuser")
        admin_password = config["admin_password"]
        image = config.get("image", {
            "publisher": "Canonical",
            "offer": "UbuntuServer",
            "sku": "18.04-LTS",
            "version": "latest",
        })

        vm_params = {
            "location": location,
            "hardware_profile": {"vm_size": vm_size},
            "storage_profile": {
                "image_reference": image,
                "os_disk": {"create_option": "FromImage"},
            },
            "os_profile": {
                "computer_name": name,
                "admin_username": admin_username,
                "admin_password": admin_password,
            },
            "network_profile": {"network_interfaces": []},
        }

        poller = self.compute_client.virtual_machines.begin_create_or_update(
            self.resource_group, name, vm_params
        )
        poller.result()
        logger.info(f"Azure VM created: {name}")
        return name

    def get_vm_status(self, instance_id: str) -> str:
        """Return Azure VM power state (e.g. 'running', 'deallocated')."""
        instance_view = self.compute_client.virtual_machines.instance_view(
            self.resource_group, instance_id
        )
        for status in instance_view.statuses:
            if status.code.startswith("PowerState/"):
                return status.code.split("/", 1)[1]
        return "unknown"

    def terminate_vm(self, instance_id: str) -> bool:
        """Delete an Azure VM."""
        poller = self.compute_client.virtual_machines.begin_delete(
            self.resource_group, instance_id
        )
        poller.result()
        logger.info(f"Azure VM deleted: {instance_id}")
        return True


class MultiCloudManager:
    """Manage deployments across multiple cloud providers."""

    def __init__(self):
        self.providers: Dict[str, CloudProvider] = {}

    def register_provider(self, name: str, provider: CloudProvider):
        """Register a cloud provider."""
        self.providers[name] = provider
        logger.info(f"Registered cloud provider: {name}")

    def deploy(self, provider_name: str, config: Dict[str, Any]) -> str:
        """Deploy to the specified cloud provider."""
        if provider_name not in self.providers:
            raise ValueError(f"Unknown provider: {provider_name}")
        return self.providers[provider_name].deploy_vm(config)
