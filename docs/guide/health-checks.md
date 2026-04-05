# Health Checks

vm_tool runs health checks after deployment to verify your application is working correctly.

## Types of Health Checks

### Port Check

Verify a port is listening:

```bash
vm_tool deploy-docker --profile prod --health-port 8000
```

### HTTP Check

Verify an HTTP endpoint returns 200:

```bash
vm_tool deploy-docker --profile prod \
  --health-url http://10.0.2.10:8000/health
```

### Custom Check

Run any command as a health check:

```bash
vm_tool deploy-docker --profile prod \
  --health-check "curl -f http://localhost:8000/api/status"
```

### Combined

Use multiple checks together:

```bash
vm_tool deploy-docker --profile prod \
  --health-port 8000 \
  --health-url http://10.0.2.10:8000/health
```

## Timeout

Control how long to wait for health checks (default: 300 seconds):

```bash
vm_tool deploy-docker --profile prod \
  --health-port 8000 \
  --health-timeout 120
```

## Skipping Health Checks

Deploy without health checks:

```bash
vm_tool deploy-docker --profile prod
```

Simply omit the `--health-port`, `--health-url`, and `--health-check` flags.
