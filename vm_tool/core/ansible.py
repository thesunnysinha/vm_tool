"""Private module: thin, testable wrapper around ansible_runner.run().

All vm_tool playbook execution goes through AnsibleRunner.run() so there is
exactly one place to mock in tests and one place to enforce security invariants
(per-run isolated private_data_dir, envvars for secrets).
"""

import logging
import os
import shutil
import tempfile
from typing import Optional

import ansible_runner

logger = logging.getLogger(__name__)


class AnsibleRunner:
    """Executes Ansible playbooks via ansible_runner with proper isolation.

    Each call to run() gets its own private_data_dir so concurrent deployments
    do not share artifact directories or log files.
    """

    def __init__(self, playbook_dir: str):
        """
        Args:
            playbook_dir: Absolute path to the directory containing playbooks
                          (typically the vm_setup/ directory inside this package).
        """
        self.playbook_dir = playbook_dir

    def run(
        self,
        playbook: str,
        inventory: str,
        extravars: dict,
        envvars: Optional[dict] = None,
    ) -> None:
        """Run a playbook. Raises RuntimeError on failure.

        Args:
            playbook: Filename relative to playbook_dir, or absolute path.
            inventory: Absolute path to inventory file.
            extravars: Non-sensitive variables dict (appears in ansible logs).
            envvars: Sensitive env vars — passed via OS environment, NOT logged
                     by ansible-runner artifact collection.
        """
        if not os.path.isabs(playbook):
            playbook = os.path.join(self.playbook_dir, playbook)

        private_data_dir = tempfile.mkdtemp(prefix="vm_tool_runner_")
        try:
            r = ansible_runner.run(
                private_data_dir=private_data_dir,
                playbook=playbook,
                inventory=inventory,
                extravars=extravars,
                envvars=envvars or {},
            )
            if r.rc != 0:
                raise RuntimeError(
                    f"Ansible playbook {os.path.basename(playbook)} failed (rc={r.rc})"
                )
            logger.info(f"Playbook {os.path.basename(playbook)} completed successfully.")
        except RuntimeError:
            raise
        except Exception as e:
            raise RuntimeError(
                f"Error running playbook {os.path.basename(playbook)}: {e}"
            ) from e
        finally:
            shutil.rmtree(private_data_dir, ignore_errors=True)
