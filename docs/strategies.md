# Deployment Strategies

vm_tool ships three production deployment strategies: **Blue-Green**, **Canary**, and **A/B Testing**.

Each strategy delegates the actual container deployment to `run_docker_deploy` (which is fully implemented). The **traffic switching** half is load-balancer-specific and cannot be implemented generically — you override one method for your infrastructure.

---

## Blue-Green

```python
from vm_tool.strategies.blue_green import BlueGreenDeployment

class NginxBlueGreen(BlueGreenDeployment):
    def _switch_traffic(self, target_env: str):
        """Rewrite nginx upstream and reload."""
        target_host = self.green_host if target_env == "green" else self.blue_host
        import subprocess
        subprocess.run([
            "ssh", f"ubuntu@{self.load_balancer_host}",
            f"sed -i 's/server .*/server {target_host};/' /etc/nginx/conf.d/upstream.conf && nginx -s reload"
        ], check=True)

bg = NginxBlueGreen(
    blue_host="10.0.1.10",
    green_host="10.0.1.11",
    load_balancer_host="10.0.1.1",
    ssh_user="ubuntu",
)
result = bg.deploy("docker-compose.yml")
```

### AWS ALB variant

```python
def _switch_traffic(self, target_env: str):
    import boto3
    target_host = self.green_host if target_env == "green" else self.blue_host
    elb = boto3.client("elbv2", region_name="us-east-1")
    # Modify the listener default action to point at the target group
    elb.modify_listener(
        ListenerArn="arn:aws:elasticloadbalancing:...",
        DefaultActions=[{"Type": "forward", "TargetGroupArn": self._tg_arn(target_env)}],
    )
```

### HAProxy variant

```python
def _switch_traffic(self, target_env: str):
    target_host = self.green_host if target_env == "green" else self.blue_host
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((self.load_balancer_host, 9999))  # HAProxy stats socket
        s.sendall(f"enable server app/{target_env}\n".encode())
        other = "blue" if target_env == "green" else "green"
        s.sendall(f"disable server app/{other}\n".encode())
```

---

## Canary

```python
from vm_tool.strategies.canary import CanaryDeployment, CanaryConfig

class NginxCanary(CanaryDeployment):
    def _shift_traffic(self, percentage: int):
        """Write nginx split_clients percentage and reload."""
        import subprocess
        cfg = f"""
split_clients "$request_id" $canary_upstream {{
    {percentage}%   canary;
    *               production;
}}
"""
        subprocess.run([
            "ssh", f"ubuntu@{self.load_balancer_host}",
            f"echo '{cfg}' > /etc/nginx/conf.d/canary_split.conf && nginx -s reload"
        ], check=True)

canary = NginxCanary(
    production_host="10.0.1.10",
    canary_host="10.0.1.11",
    config=CanaryConfig(initial_percentage=10, increment_percentage=10),
    ssh_user="ubuntu",
)
result = canary.deploy("docker-compose.yml")
```

---

## A/B Testing

```python
from vm_tool.strategies.ab_testing import ABTestDeployment, Variant

class NginxABTest(ABTestDeployment):
    def _configure_traffic_split(self):
        weights = {v.name: v.traffic_percentage for v in self.variants}
        # Build nginx upstream with weights
        lines = "\n".join(
            f"    server {v.host} weight={int(v.traffic_percentage)};"
            for v in self.variants
        )
        cfg = f"upstream ab_backends {{\n{lines}\n}}"
        import subprocess
        subprocess.run([
            "ssh", f"ubuntu@lb.internal",
            f"echo '{cfg}' > /etc/nginx/conf.d/ab_upstream.conf && nginx -s reload"
        ], check=True)

ab = NginxABTest(
    variants=[
        Variant(name="control", host="10.0.1.10", traffic_percentage=50),
        Variant(name="variant_a", host="10.0.1.11", traffic_percentage=50),
    ],
    ssh_user="ubuntu",
)
result = ab.deploy({
    "control": "docker-compose.yml",
    "variant_a": "docker-compose.variant-a.yml",
})
```

---

## What is implemented vs. what you must provide

| Component | Status |
|-----------|--------|
| Container deployment (`run_docker_deploy`) | Fully implemented |
| Health checks | Fully implemented |
| Gradual traffic shifting logic (loop/steps) | Fully implemented |
| Metrics monitoring during canary rollout | Stub — override `_get_canary_metrics` |
| `_switch_traffic` / `_configure_traffic_split` / `_apply_weights` | **Override required** (examples above) |
