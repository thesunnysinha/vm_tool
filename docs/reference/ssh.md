# SSH

SSH utilities are provided by `vm_tool.infra.ssh`. Import from the `infra` subpackage:

```python
from vm_tool.infra.ssh import SSHSetup
```

!!! note "Security"
    Connections use `StrictHostKeyChecking=accept-new` and load system host keys automatically. Credentials are read from environment variables — never passed as Ansible extra-vars. Temporary credential files are created with `chmod 0o600`.

::: vm_tool.infra.ssh
