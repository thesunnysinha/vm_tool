# Pipeline Generator

Use this tool to generate a GitHub Actions workflow for your project. Fill in the details below and copy the generated YAML.

<form id="pipelineForm" style="display: grid; gap: 1rem; max-width: 600px; padding: 1rem; border: 1px solid #eee; border-radius: 8px;">
    <div style="display: flex; gap: 1rem; align-items: flex-start;">
        <div style="flex: 1;">
            <label for="branch_name" style="display: block; margin-bottom: 0.5rem; font-weight: bold;">Branch Name</label>
            <input type="text" id="branch_name" name="branch_name" value="main" style="width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px;">
        </div>
        <div style="flex: 1;">
            <label for="python_version" style="display: block; margin-bottom: 0.5rem; font-weight: bold;">Python Version</label>
            <input type="text" id="python_version" name="python_version" value="3.11" style="width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px;">
        </div>
    </div>

    <div style="margin-top: 1rem;">
        <label for="docker_compose_file" style="display: block; margin-bottom: 0.5rem; font-weight: bold;">Docker Compose File</label>
        <input type="text" id="docker_compose_file" name="docker_compose_file" value="docker-compose.yml" style="width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px;">
    </div>

    <div style="margin-top: 1rem;">
        <label for="app_port" style="display: block; margin-bottom: 0.5rem; font-weight: bold;">Application Port</label>
        <input type="number" id="app_port" name="app_port" value="8000" style="width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px;">
        <small style="color: #666;">Port your application runs on (used for health checks)</small>
    </div>

    <div style="display: flex; flex-direction: column; gap: 0.5rem; margin-top: 0.5rem; padding: 1rem; background: #f9f9f9; border-radius: 4px;">
        <h4 style="margin: 0 0 0.5rem 0;">Features (Ansible-based)</h4>
        <div style="display: flex; align-items: center; gap: 0.5rem;">
            <input type="checkbox" id="enable_backup" name="enable_backup" checked>
            <label for="enable_backup" style="cursor: pointer;">✅ Pre-deployment Backup</label>
        </div>
        <div style="display: flex; align-items: center; gap: 0.5rem;">
            <input type="checkbox" id="enable_dry_run" name="enable_dry_run" checked>
            <label for="enable_dry_run" style="cursor: pointer;">🔍 Dry-Run Preview</label>
        </div>
        <div style="display: flex; align-items: center; gap: 0.5rem;">
            <input type="checkbox" id="enable_health_check" name="enable_health_check" checked>
            <label for="enable_health_check" style="cursor: pointer;">🏥 Health Checks</label>
        </div>
        <div style="display: flex; align-items: center; gap: 0.5rem;">
            <input type="checkbox" id="enable_rollback" name="enable_rollback" checked>
            <label for="enable_rollback" style="cursor: pointer;">🔄 Auto-Rollback on Failure</label>
        </div>
    </div>

    <button type="button" onclick="generatePipeline()" style="margin-top: 1.5rem; padding: 0.75rem; background-color: #009485; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; width: 100%;">Generate Workflow</button>

</form>

<div id="output" style="margin-top: 2rem; display: none;">
    <h3>Generated Workflow (.github/workflows/deploy.yml)</h3>
    <pre><code id="yamlOutput" class="language-yaml"></code></pre>
    <div style="display: flex; gap: 0.5rem; margin-top: 0.5rem;">
        <button onclick="copyToClipboard()" style="padding: 0.5rem 1rem; background-color: #f0f0f0; border: 1px solid #ccc; border-radius: 4px; cursor: pointer;">Copy to Clipboard</button>
        <button onclick="downloadYaml()" style="padding: 0.5rem 1rem; background-color: #009485; color: white; border: 1px solid #009485; border-radius: 4px; cursor: pointer;">Download .yml</button>
    </div>
</div>

<script>
const TEMPLATE = `name: Deploy to EC2 with vm_tool

on:
  push:
    branches: [ BRANCH_NAME ]
  workflow_dispatch:

env:
  EC2_HOST: \${{ secrets.EC2_HOST }}
  EC2_USER: \${{ secrets.EC2_USER }}
  APP_PORT: APP_PORT

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Validate Required Secrets
        run: |
          echo "🔐 Validating GitHub Secrets..."
          MISSING_SECRETS=()
          
          if [ -z "\${{ secrets.EC2_HOST }}" ]; then
            MISSING_SECRETS+=("EC2_HOST")
          fi
          
          if [ -z "\${{ secrets.EC2_USER }}" ]; then
            MISSING_SECRETS+=("EC2_USER")
          fi
          
          if [ -z "\${{ secrets.EC2_SSH_KEY }}" ]; then
            MISSING_SECRETS+=("EC2_SSH_KEY")
          fi
          
          if [ \${#MISSING_SECRETS[@]} -ne 0 ]; then
            echo "❌ ERROR: Missing required GitHub Secrets!"
            echo "Missing: \${MISSING_SECRETS[*]}"
            echo "See: docs/ssh-key-setup.md"
            exit 1
          fi
          
          echo "✅ All secrets configured"

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: 'PYTHON_VERSION'

      - name: Install vm_tool
        run: pip install vm-tool

      - name: Set up SSH
        run: |
          mkdir -p ~/.ssh
          echo "\${{ secrets.EC2_SSH_KEY }}" > ~/.ssh/deploy_key
          chmod 600 ~/.ssh/deploy_key
          ssh-keyscan -H \${{ secrets.EC2_HOST }} >> ~/.ssh/known_hosts

      - name: Validate SSH Connection
        run: |
          echo "✅ Testing SSH connection..."
          ssh -i ~/.ssh/deploy_key -o StrictHostKeyChecking=no \\
            \${{ secrets.EC2_USER }}@\${{ secrets.EC2_HOST }} "echo 'Connected'" || {
            echo "❌ SSH failed! Check docs/ssh-key-setup.md"
            exit 1
          }

      - name: Copy docker-compose to EC2
        run: |
          ssh -i ~/.ssh/deploy_key \${{ secrets.EC2_USER }}@\${{ secrets.EC2_HOST }} \\
            'mkdir -p ~/app'
          
          scp -i ~/.ssh/deploy_key COMPOSE_FILE \\
            \${{ secrets.EC2_USER }}@\${{ secrets.EC2_HOST }}:~/app/
BACKUP_STEP
DRY_RUN_STEP
      - name: Deploy with vm_tool (Ansible-based)
        run: |
          cat > inventory.yml << EOF
          all:
            hosts:
              production:
                ansible_host: \${{ secrets.EC2_HOST }}
                ansible_user: \${{ secrets.EC2_USER }}
                ansible_ssh_private_key_file: ~/.ssh/deploy_key
          EOF
          
          vm_tool deploy-docker \\
            --host \${{ secrets.EC2_HOST }} \\
            --user \${{ secrets.EC2_USER }} \\
            --compose-file ~/app/COMPOSE_FILE \\
            --inventory inventory.yml \\
            --force
HEALTH_CHECK_STEP
      - name: Verify deployment
        run: |
          ssh -i ~/.ssh/deploy_key \${{ secrets.EC2_USER }}@\${{ secrets.EC2_HOST }} << 'EOF'
            cd ~/app
            docker-compose ps
            docker-compose logs --tail=20
          EOF
ROLLBACK_STEP
      - name: Cleanup old backups
        if: success()
        run: |
          ssh -i ~/.ssh/deploy_key \${{ secrets.EC2_USER }}@\${{ secrets.EC2_HOST }} << 'EOF'
            cd ~/backups 2>/dev/null || exit 0
            ls -t *.tar.gz 2>/dev/null | tail -n +6 | xargs rm -f || true
          EOF

      - name: Send notification
        if: always()
        run: |
          if [ "\${{ job.status }}" == "success" ]; then
            echo "✅ Deployment successful to \${{ secrets.EC2_HOST }}:\${{ env.APP_PORT }}"
          else
            echo "❌ Deployment failed to \${{ secrets.EC2_HOST }}"
          fi
`;

const BACKUP_STEP = `
      - name: Create backup before deployment
        run: |
          ssh -i ~/.ssh/deploy_key \${{ secrets.EC2_USER }}@\${{ secrets.EC2_HOST }} << 'EOF'
            mkdir -p ~/backups
            if [ -d ~/app ]; then
              tar -czf ~/backups/backup-$(date +%Y%m%d-%H%M%S).tar.gz -C ~/app . 2>/dev/null || true
              echo "✅ Backup created"
            fi
          EOF
`;

const DRY_RUN_STEP = `
      - name: Dry-run deployment preview
        run: |
          echo "🔍 DRY-RUN: Previewing deployment"
          ssh -i ~/.ssh/deploy_key \${{ secrets.EC2_USER }}@\${{ secrets.EC2_HOST }} << 'EOF'
            cd ~/app && docker-compose config
          EOF
`;

const HEALTH_CHECK_STEP = `
      - name: Health check
        run: |
          for i in {1..30}; do
            if curl -f http://\${{ secrets.EC2_HOST }}:APP_PORT/health 2>/dev/null; then
              echo "✅ Health check passed"
              exit 0
            fi
            sleep 2
          done
          echo "❌ Health check failed"
          exit 1
`;

const ROLLBACK_STEP = `
      - name: Rollback on failure
        if: failure()
        run: |
          echo "⚠️  Rolling back..."
          ssh -i ~/.ssh/deploy_key \${{ secrets.EC2_USER }}@\${{ secrets.EC2_HOST }} << 'EOF'
            BACKUP=$(ls -t ~/backups/*.tar.gz 2>/dev/null | head -1)
            if [ -n "$BACKUP" ]; then
              cd ~/app && tar -xzf $BACKUP
              docker-compose up -d
              echo "✅ Rolled back"
            fi
          EOF
`;

function generatePipeline() {
    const branch = document.getElementById('branch_name').value;
    const pythonVersion = document.getElementById('python_version').value;
    const composeFile = document.getElementById('docker_compose_file').value;
    const appPort = document.getElementById('app_port').value;
    const enableBackup = document.getElementById('enable_backup').checked;
    const enableDryRun = document.getElementById('enable_dry_run').checked;
    const enableHealthCheck = document.getElementById('enable_health_check').checked;
    const enableRollback = document.getElementById('enable_rollback').checked;

    let output = TEMPLATE
        .replace(/BRANCH_NAME/g, branch)
        .replace(/PYTHON_VERSION/g, pythonVersion)
        .replace(/COMPOSE_FILE/g, composeFile)
        .replace(/APP_PORT/g, appPort);
    
    output = output.replace(/BACKUP_STEP/g, enableBackup ? BACKUP_STEP : '');
    output = output.replace(/DRY_RUN_STEP/g, enableDryRun ? DRY_RUN_STEP : '');
    output = output.replace(/HEALTH_CHECK_STEP/g, enableHealthCheck ? HEALTH_CHECK_STEP.replace(/APP_PORT/g, appPort) : '');
    output = output.replace(/ROLLBACK_STEP/g, enableRollback ? ROLLBACK_STEP : '');

    document.getElementById('yamlOutput').textContent = output;
    document.getElementById('output').style.display = 'block';
    
    if (window.hljs) {
        hljs.highlightElement(document.getElementById('yamlOutput'));
    }
}

function copyToClipboard() {
    const text = document.getElementById('yamlOutput').textContent;
    navigator.clipboard.writeText(text).then(() => {
        alert('Copied to clipboard!');
    });
}

function downloadYaml() {
    const text = document.getElementById('yamlOutput').textContent;
    const blob = new Blob([text], { type: 'text/yaml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'deploy.yml';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}
</script>
