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
            <input type="text" id="python_version" name="python_version" value="3.12" style="width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px;">
        </div>
    </div>

    <div style="display: flex; flex-direction: column; gap: 0.5rem; margin-top: 0.5rem;">
        <div style="display: flex; align-items: center; gap: 0.5rem;">
            <input type="checkbox" id="run_linting" name="run_linting">
            <label for="run_linting" style="cursor: pointer;">Run Linting (flake8)</label>
        </div>
        <div style="display: flex; align-items: center; gap: 0.5rem;">
            <input type="checkbox" id="run_tests" name="run_tests">
            <label for="run_tests" style="cursor: pointer;">Run Tests (pytest)</label>
        </div>
        <div style="display: flex; align-items: center; gap: 0.5rem;">
            <input type="checkbox" id="setup_monitoring" name="setup_monitoring">
            <label for="setup_monitoring" style="cursor: pointer;">Include Monitoring (Prometheus/Grafana)</label>
        </div>
    </div>

    <div style="margin-top: 1rem;">
        <label style="display: block; margin-bottom: 0.5rem; font-weight: bold;">Deployment Strategy</label>
        <div style="display: flex; gap: 1rem;">
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <input type="radio" id="deploy_k8s" name="deployment_type" value="kubernetes" onchange="toggleMonitoring()">
                <label for="deploy_k8s" style="cursor: pointer;">Kubernetes (K3s)</label>
            </div>
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <input type="radio" id="deploy_docker" name="deployment_type" value="docker" checked onchange="toggleMonitoring()">
                <label for="deploy_docker" style="cursor: pointer;">Docker Compose</label>
            </div>
        </div>
    </div>

    <div id="docker_options" style="margin-top: 1rem;">
        <label for="docker_compose_file" style="display: block; margin-bottom: 0.5rem; font-weight: bold;">Docker Compose File</label>
        <input type="text" id="docker_compose_file" name="docker_compose_file" value="docker-compose.yml" style="width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px;">
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
const TEMPLATE_BASE = `name: Project Deployment

on:
  push:
    branches: [ (( branch_name )) ]
  workflow_dispatch:  # Allow manual trigger

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - name: Checkout Code
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '(( python_version ))'

    - name: Install vm_tool
      run: pip install vm-tool
`;

const TEMPLATE_LINTING = `
    - name: Run Linting
      run: |
        pip install flake8
        flake8 .
`;

const TEMPLATE_TESTING = `
    - name: Run Tests
      run: |
        pip install pytest
        pytest
`;

const TEMPLATE_SSH = `
    - name: Check for Secrets
      run: |
        if [ -z "\${{ secrets.SSH_PRIVATE_KEY }}" ]; then
          echo "Error: SSH_PRIVATE_KEY secret is not set."
          exit 1
        fi
        if [ -z "\${{ secrets.VM_HOST }}" ]; then
          echo "Error: VM_HOST secret is not set."
          exit 1
        fi
        if [ -z "\${{ secrets.SSH_USER }}" ]; then
          echo "Error: SSH_USER secret is not set."
          exit 1
        fi

    - name: Setup SSH Key
      run: |
        mkdir -p ~/.ssh
        echo "\${{ secrets.SSH_PRIVATE_KEY }}" > ~/.ssh/id_rsa
        chmod 600 ~/.ssh/id_rsa
        ssh-keyscan -H \${{ secrets.VM_HOST }} >> ~/.ssh/known_hosts
`;

const TEMPLATE_K8S = `
    - name: Setup Kubernetes (K3s)
      run: |
        echo "Setting up K3s..."
        # vm_tool setup-k8s --inventory inventory.yml
`;

const TEMPLATE_MONITORING = `
    - name: Setup Observability (Prometheus/Grafana)
      if: success()
      run: |
        echo "Setting up Monitoring..."
        # vm_tool setup-monitoring --inventory inventory.yml
`;

const TEMPLATE_DOCKER = `
    - name: Deploy with Docker Compose
      run: |
        echo "Deploying with Docker Compose..."
        vm_tool deploy-docker --compose-file (( docker_compose_file )) --host \${{ secrets.VM_HOST }} --user \${{ secrets.SSH_USER }}
`;

function generatePipeline() {
    const branch = document.getElementById('branch_name').value;
    const pythonVersion = document.getElementById('python_version').value;
    const linkting = document.getElementById('run_linting').checked;
    const tests = document.getElementById('run_tests').checked;
    const monitoring = document.getElementById('setup_monitoring').checked;
    const deployType = document.querySelector('input[name="deployment_type"]:checked').value;
    const composeFile = document.getElementById('docker_compose_file').value;

    let output = TEMPLATE_BASE
        .replace(/\(\( branch_name \)\)/g, branch)
        .replace(/\(\( python_version \)\)/g, pythonVersion);
    
    if (linkting) output += TEMPLATE_LINTING;
    if (tests) output += TEMPLATE_TESTING;
    
    output += TEMPLATE_SSH;
    
    if (deployType === 'kubernetes') {
        output += TEMPLATE_K8S;
    } else {
        output += TEMPLATE_DOCKER.replace(/\(\( docker_compose_file \)\)/g, composeFile);
    }

    if (monitoring) output += TEMPLATE_MONITORING;

    document.getElementById('yamlOutput').textContent = output;
    document.getElementById('output').style.display = 'block';
    
    // Trigger syntax highlighting if available (MkDocs dependent)
    if (window.hljs) {
        hljs.highlightElement(document.getElementById('yamlOutput'));
    }
}
// ... copy/download functions ...

function toggleMonitoring() {
    const deployType = document.querySelector('input[name="deployment_type"]:checked').value;
    const dockerOptions = document.getElementById('docker_options');
    if (deployType === 'docker') {
        dockerOptions.style.display = 'block';
    } else {
        dockerOptions.style.display = 'none';
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

function toggleMonitoring() {
    // Optional: could enforce monitoring only for k8s if we wanted logic here
}
</script>
