"""Dynamic CI/CD pipeline generator with all vm_tool features."""

import os
from pathlib import Path
from typing import Optional


class PipelineGenerator:
    """Generate CI/CD pipelines with vm_tool features."""

    def __init__(
        self,
        platform: str = "github",
        strategy: str = "docker",  # docker, registry
        enable_monitoring: bool = False,
        enable_health_checks: bool = True,
        enable_backup: bool = True,
        enable_rollback: bool = True,
        enable_drift_detection: bool = False,
        enable_dry_run: bool = True,
        health_port: Optional[int] = 8000,
        health_url: Optional[str] = None,
        backup_paths: Optional[list] = None,
        app_port: int = 8000,
    ):
        self.platform = platform
        self.strategy = strategy
        self.enable_monitoring = enable_monitoring
        self.enable_health_checks = enable_health_checks
        self.enable_backup = enable_backup
        self.enable_rollback = enable_rollback
        self.enable_drift_detection = enable_drift_detection
        self.enable_dry_run = enable_dry_run
        self.health_port = health_port
        self.health_url = (
            health_url or f"http://${{{{ secrets.EC2_HOST }}}}:{app_port}/health"
        )
        self.backup_paths = backup_paths or ["/app", "/etc/nginx"]
        self.app_port = app_port

        # New options
        self.run_linting = False
        self.run_tests = False
        self.python_version = "3.11"
        self.branch = "main"

    def set_options(
        self,
        run_linting: bool = False,
        run_tests: bool = False,
        python_version: str = "3.11",
        branch: str = "main",
    ):
        """Set additional options for the pipeline."""
        self.run_linting = run_linting
        self.run_tests = run_tests
        self.python_version = python_version
        self.branch = branch

    def generate(self) -> str:
        """Generate pipeline based on platform."""
        if self.platform == "github":
            return self._generate_github_actions()
        elif self.platform == "gitlab":
            raise NotImplementedError("GitLab CI support coming soon")
        else:
            raise ValueError(f"Unsupported platform: {self.platform}")

    def _generate_github_actions(self) -> str:
        """Generate GitHub Actions workflow with all features."""

        # Build steps dynamically
        # Build steps dynamically
        steps = []

        # Basic setup steps
        steps.extend(
            [
                self._step_checkout(),
                self._step_validate_secrets(),
                self._step_setup_python(),
                self._step_install_vm_tool(),
            ]
        )

        if self.run_linting:
            steps.append(self._step_run_linting())

        if self.run_tests:
            steps.append(self._step_run_tests())

        # Build and Push (Registry Strategy)
        if self.strategy == "registry":
            steps.append(self._step_login_ghcr())
            steps.append(self._step_build_push())

        steps.extend(
            [
                self._step_setup_ssh(),
                self._step_validate_ssh(),
            ]
        )

        # Copy files (only if NOT registry strategy, or just config for registry)
        if self.strategy == "registry":
            # For registry, we only need docker-compose and .env, not the full source
            steps.append(self._step_copy_compose_only())
        else:
            steps.append(self._step_copy_files())

        # Backup step
        if self.enable_backup:
            steps.append(self._step_create_backup())

        # Drift detection (pre-deployment)
        if self.enable_drift_detection:
            steps.append(self._step_drift_check())

        # Dry-run step
        if self.enable_dry_run:
            steps.append(self._step_dry_run())

        # Main deployment
        steps.append(self._step_deploy())

        # Health checks
        if self.enable_health_checks:
            steps.append(self._step_health_check())

        # Verification
        steps.append(self._step_verify())

        # Rollback on failure
        if self.enable_rollback:
            steps.append(self._step_rollback())

        # Cleanup
        steps.append(self._step_cleanup())

        # Notification
        steps.append(self._step_notification())

        # Combine all steps
        steps_yaml = "\n".join(steps)

        return f"""name: Deploy to EC2 with vm_tool

on:
  push:
    branches: [ {self.branch} ]
  pull_request:
    branches: [ {self.branch} ]
  workflow_dispatch:

env:
  EC2_HOST: ${{{{ secrets.EC2_HOST }}}}
  EC2_USER: ${{{{ secrets.EC2_USER }}}}
  APP_PORT: {self.app_port}

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
{steps_yaml}
"""

    def _step_checkout(self) -> str:
        return """      - name: Checkout code
        uses: actions/checkout@v4"""

    def _step_validate_secrets(self) -> str:
        return """
      - name: Validate Required Secrets
        run: |
          echo "🔐 Validating GitHub Secrets..."
          MISSING_SECRETS=()
          
          if [ -z "${{ secrets.EC2_HOST }}" ]; then
            MISSING_SECRETS+=("EC2_HOST")
          fi
          
          if [ -z "${{ secrets.EC2_USER }}" ]; then
            MISSING_SECRETS+=("EC2_USER")
          fi
          
          if [ -z "${{ secrets.EC2_SSH_KEY }}" ]; then
            MISSING_SECRETS+=("EC2_SSH_KEY")
          fi
          
          if [ ${#MISSING_SECRETS[@]} -ne 0 ]; then
            echo ""
            echo "❌ ERROR: Missing required GitHub Secrets!"
            echo ""
            echo "Missing: ${MISSING_SECRETS[*]}"
            echo ""
            echo "📝 How to add secrets:"
            echo "1. Go to: Repository → Settings → Secrets → Actions"
            echo "2. Add each secret:"
            echo ""
            
            if [[ " ${MISSING_SECRETS[*]} " =~ " EC2_HOST " ]]; then
              echo "   EC2_HOST: Your EC2 IP (e.g., 54.123.45.67)"
            fi
            
            if [[ " ${MISSING_SECRETS[*]} " =~ " EC2_USER " ]]; then
              echo "   EC2_USER: SSH username (e.g., ubuntu)"
            fi
            
            if [[ " ${MISSING_SECRETS[*]} " =~ " EC2_SSH_KEY " ]]; then
              echo "   EC2_SSH_KEY: Run 'cat ~/.ssh/id_rsa' and copy output"
            fi
            
            echo ""
            echo "📚 See: docs/ssh-key-setup.md"
            exit 1
          fi
          
          echo "✅ All secrets configured"
"""

    def _step_setup_python(self) -> str:
        return f"""
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '{self.python_version}'"""

    def _step_install_vm_tool(self) -> str:
        return """
      - name: Install vm_tool
        run: pip install vm-tool"""

    def _step_run_linting(self) -> str:
        return """
      - name: Lint with flake8
        run: |
          pip install flake8
          # stop the build if there are Python syntax errors or undefined names
          flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
          # exit-zero treats all errors as warnings.
          flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics"""

    def _step_run_tests(self) -> str:
        return """
      - name: Test with pytest
        run: |
          pip install pytest
          pytest"""

    def _step_login_ghcr(self) -> str:
        return """
      - name: Log in to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}"""

    def _step_build_push(self) -> str:
        return """
      - name: Build and push Docker images
        env:
          GITHUB_REPOSITORY_OWNER: ${{ github.repository_owner }}
        run: |
          # Create .env file for build context if needed
          if [ -f .env.production ]; then
            cp .env.production .env
          fi
          
          # Build and push using docker-compose
          docker-compose build
          docker-compose push"""

    def _step_copy_compose_only(self) -> str:
        return """
      - name: Copy docker-compose to EC2
        run: |
          ssh -i ~/.ssh/deploy_key ${{ secrets.EC2_USER }}@${{ secrets.EC2_HOST }} \\
            'mkdir -p ~/app'
          
          scp -i ~/.ssh/deploy_key docker-compose.yml \\
            ${{ secrets.EC2_USER }}@${{ secrets.EC2_HOST }}:~/app/
          
          # Copy .env file
          if [ -f .env.production ]; then
            scp -i ~/.ssh/deploy_key .env.production \\
              ${{ secrets.EC2_USER }}@${{ secrets.EC2_HOST }}:~/app/.env
          fi"""

    def _step_setup_ssh(self) -> str:
        return """
      - name: Set up SSH
        run: |
          mkdir -p ~/.ssh
          echo "${{ secrets.EC2_SSH_KEY }}" > ~/.ssh/deploy_key
          chmod 600 ~/.ssh/deploy_key
          ssh-keyscan -H ${{ secrets.EC2_HOST }} >> ~/.ssh/known_hosts"""

    def _step_validate_ssh(self) -> str:
        return """
      - name: Validate SSH Connection
        run: |
          echo "✅ Testing SSH connection..."
          ssh -i ~/.ssh/deploy_key -o StrictHostKeyChecking=no \\
            ${{ secrets.EC2_USER }}@${{ secrets.EC2_HOST }} "echo 'Connected'" || {
            echo "❌ SSH failed! Check docs/ssh-key-setup.md"
            exit 1
          }"""

    def _step_copy_files(self) -> str:
        return """
      - name: Copy docker-compose to EC2
        run: |
          ssh -i ~/.ssh/deploy_key ${{ secrets.EC2_USER }}@${{ secrets.EC2_HOST }} \\
            'mkdir -p ~/app'
          
          scp -i ~/.ssh/deploy_key docker-compose.yml \\
            ${{ secrets.EC2_USER }}@${{ secrets.EC2_HOST }}:~/app/
          
          # Copy any .env files if they exist
          if [ -f .env.production ]; then
            scp -i ~/.ssh/deploy_key .env.production \\
              ${{ secrets.EC2_USER }}@${{ secrets.EC2_HOST }}:~/app/.env
          fi"""

    def _step_create_backup(self) -> str:
        return """
      - name: Create backup
        run: |
          ssh -i ~/.ssh/deploy_key ${{ secrets.EC2_USER }}@${{ secrets.EC2_HOST }} << 'EOF'
            mkdir -p ~/backups
            if [ -d ~/app ]; then
              tar -czf ~/backups/backup-$(date +%Y%m%d-%H%M%S).tar.gz -C ~/app . 2>/dev/null || true
              echo "✅ Backup created"
            fi
          EOF"""

    def _step_drift_check(self) -> str:
        return """
      - name: Check drift
        continue-on-error: true
        run: |
          echo "🔍 Checking for configuration drift..."
          # Add drift detection logic"""

    def _step_dry_run(self) -> str:
        return """
      - name: Dry-run
        run: |
          echo "🔍 DRY-RUN: Previewing deployment"
          ssh -i ~/.ssh/deploy_key ${{ secrets.EC2_USER }}@${{ secrets.EC2_HOST }} << 'EOF'
            cd ~/app && docker-compose config
          EOF"""

    def _step_deploy(self) -> str:
        return """
      - name: Deploy with vm_tool (Ansible-based)
        run: |
          # Create inventory file for Ansible
          cat > inventory.yml << EOF
          all:
            hosts:
              production:
                ansible_host: ${{ secrets.EC2_HOST }}
                ansible_user: ${{ secrets.EC2_USER }}
                ansible_ssh_private_key_file: ~/.ssh/deploy_key
          EOF
          
          # Deploy using vm_tool (uses Ansible under the hood)
          export GITHUB_REPOSITORY_OWNER=${{ github.repository_owner }}
          vm_tool deploy-docker \\
            --host ${{ secrets.EC2_HOST }} \\
            --user ${{ secrets.EC2_USER }} \\
            --compose-file ~/app/docker-compose.yml \\
            --inventory inventory.yml \\
            --force"""

    def _step_health_check(self) -> str:
        return f"""
      - name: Health check
        run: |
          for i in {{{{1..30}}}}; do
            if curl -f {self.health_url} 2>/dev/null; then
              echo "✅ Health check passed"
              exit 0
            fi
            sleep 2
          done
          echo "❌ Health check failed"
          exit 1"""

    def _step_verify(self) -> str:
        return """
      - name: Verify
        run: |
          ssh -i ~/.ssh/deploy_key ${{ secrets.EC2_USER }}@${{ secrets.EC2_HOST }} << 'EOF'
            cd ~/app
            docker-compose ps
            docker-compose logs --tail=20
          EOF"""

    def _step_rollback(self) -> str:
        return """
      - name: Rollback on failure
        if: failure()
        run: |
          echo "⚠️  Rolling back..."
          ssh -i ~/.ssh/deploy_key ${{ secrets.EC2_USER }}@${{ secrets.EC2_HOST }} << 'EOF'
            BACKUP=$(ls -t ~/backups/*.tar.gz 2>/dev/null | head -1)
            if [ -n "$BACKUP" ]; then
              cd ~/app && tar -xzf $BACKUP
              docker-compose up -d
              echo "✅ Rolled back"
            fi
          EOF"""

    def _step_cleanup(self) -> str:
        return """
      - name: Cleanup
        if: success()
        run: |
          ssh -i ~/.ssh/deploy_key ${{ secrets.EC2_USER }}@${{ secrets.EC2_HOST }} << 'EOF'
            cd ~/backups 2>/dev/null || exit 0
            ls -t *.tar.gz 2>/dev/null | tail -n +6 | xargs rm -f || true
          EOF"""

    def _step_notification(self) -> str:
        return """
      - name: Notify
        if: always()
        run: |
          if [ "${{ job.status }}" == "success" ]; then
            echo "✅ Deployed to ${{ secrets.EC2_HOST }}:${{ env.APP_PORT }}"
          else
            echo "❌ Deployment failed"
          fi"""

    def _generate_gitlab_ci(self) -> str:
        """Generate GitLab CI pipeline."""
        return """# GitLab CI (Coming Soon)
# Use GitHub Actions for now
"""

    def save(self, output_path: Optional[str] = None) -> str:
        """Save generated pipeline to file."""
        content = self.generate()

        if output_path is None:
            if self.platform == "github":
                output_path = ".github/workflows/deploy.yml"
            elif self.platform == "gitlab":
                output_path = ".gitlab-ci.yml"

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Write file
        with open(output_path, "w") as f:
            f.write(content)

        return output_path
