import logging
import os

from python_terraform import Terraform

logger = logging.getLogger(__name__)


class Provisioner:
    """
    Handles infrastructure provisioning using Terraform.
    """

    def __init__(self, provider: str, working_dir: str = None):
        """
        Initialize the provisioner.

        Args:
            provider (str): The cloud provider (e.g., 'aws', 'do').
            working_dir (str): Directory containing Terraform files. Defaults to internal modules.
        """
        self.provider = provider
        if working_dir:
            self.working_dir = working_dir
        else:
            # Default to bundled modules (to be created)
            self.working_dir = os.path.join(
                os.path.dirname(__file__), "modules", provider
            )

        self.tf = Terraform(working_dir=self.working_dir)

    def init(self):
        """Initialize Terraform."""
        logger.info(f"Initializing Terraform in {self.working_dir}...")
        return_code, stdout, stderr = self.tf.init()
        if return_code != 0:
            logger.error(f"Terraform init failed: {stderr}")
            raise RuntimeError(f"Terraform init failed: {stderr}")
        logger.info("Terraform initialized successfully.")

    def apply(self, vars: dict = None):
        """Apply Terraform configuration."""
        logger.info("Applying Terraform configuration...")
        return_code, stdout, stderr = self.tf.apply(skip_plan=True, var=vars)
        if return_code != 0:
            logger.error(f"Terraform apply failed: {stderr}")
            raise RuntimeError(f"Terraform apply failed: {stderr}")
        logger.info("Terraform applied successfully.")
        return stdout

    def destroy(self, vars: dict = None):
        """Destroy Terraform infrastructure."""
        logger.info("Destroying Terraform infrastructure...")
        return_code, stdout, stderr = self.tf.destroy(var=vars)
        if return_code != 0:
            logger.error(f"Terraform destroy failed: {stderr}")
            raise RuntimeError(f"Terraform destroy failed: {stderr}")
        logger.info("Terraform destroyed successfully.")
