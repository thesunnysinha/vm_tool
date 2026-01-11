# Pipeline Generator

Use this tool to generate a GitHub Actions workflow for your project. Fill in the details below and copy the generated YAML.

<form id="pipelineForm" style="display: grid; gap: 1rem; max-width: 600px; padding: 1rem; border: 1px solid #eee; border-radius: 8px;">
    <div>
        <label for="branch_name" style="display: block; margin-bottom: 0.5rem; font-weight: bold;">Branch Name</label>
        <input type="text" id="branch_name" name="branch_name" value="main" style="width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px;">
        <small style="color: #666;">The branch that triggers the deployment.</small>
    </div>

    <div>
        <label for="provider" style="display: block; margin-bottom: 0.5rem; font-weight: bold;">Cloud Provider</label>
        <select id="provider" name="provider" style="width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px;">
            <option value="aws">AWS</option>
            <option value="gcp">Google Cloud (Coming Soon)</option>
            <option value="azure">Azure (Coming Soon)</option>
        </select>
    </div>

    <div>
        <label for="aws_region" style="display: block; margin-bottom: 0.5rem; font-weight: bold;">AWS Region</label>
        <input type="text" id="aws_region" name="aws_region" value="us-east-1" style="width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px;">
    </div>

    <div>
        <label for="instance_type" style="display: block; margin-bottom: 0.5rem; font-weight: bold;">Instance Type</label>
        <input type="text" id="instance_type" name="instance_type" value="t2.small" style="width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px;">
    </div>

    <button type="button" onclick="generatePipeline()" style="padding: 0.75rem; background-color: #009485; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold;">Generate Workflow</button>

</form>

<div id="output" style="margin-top: 2rem; display: none;">
    <h3>Generated Workflow (.github/workflows/deploy.yml)</h3>
    <pre><code id="yamlOutput" class="language-yaml"></code></pre>
    <button onclick="copyToClipboard()" style="margin-top: 0.5rem; padding: 0.5rem; background-color: #f0f0f0; border: 1px solid #ccc; border-radius: 4px; cursor: pointer;">Copy to Clipboard</button>
</div>

<script>
const TEMPLATE = `name: Infrastructure Deployment

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
        python-version: '3.12'

    - name: Install vm_tool
      run: pip install vm-tool

    # Setup SSH Key for Ansible/SSH connections
    # - name: Setup SSH Key
    #   run: |
    #     mkdir -p ~/.ssh
    #     echo "\${{ secrets.SSH_PRIVATE_KEY }}" > ~/.ssh/id_rsa
    #     chmod 600 ~/.ssh/id_rsa
    #     ssh-keyscan -H \${{ secrets.VM_HOST }} >> ~/.ssh/known_hosts

    - name: Provision Infrastructure
      env:
        # Provider credentials (example for AWS)
        AWS_ACCESS_KEY_ID: \${{ secrets.AWS_ACCESS_KEY_ID }}
        AWS_SECRET_ACCESS_KEY: \${{ secrets.AWS_SECRET_ACCESS_KEY }}
        AWS_DEFAULT_REGION: '(( aws_region ))'
      run: |
        echo "Provisioning infrastructure..."
        # Uncomment to enable provisioning
        # vm_tool provision --provider (( provider )) --action apply --vars region=(( aws_region )) instance_type=(( instance_type ))

    - name: Setup Kubernetes (K3s)
      if: success()
      run: |
        echo "Setting up K3s..."
        # vm_tool setup-k8s --inventory inventory.yml

    - name: Setup Observability (Prometheus/Grafana)
      if: success()
      run: |
        echo "Setting up Monitoring..."
        # vm_tool setup-monitoring --inventory inventory.yml
`;

function generatePipeline() {
    const branch = document.getElementById('branch_name').value;
    const provider = document.getElementById('provider').value;
    const region = document.getElementById('aws_region').value;
    const instanceType = document.getElementById('instance_type').value;

    let output = TEMPLATE
        .replace(/\(\( branch_name \)\)/g, branch)
        .replace(/\(\( aws_region \)\)/g, region)
        .replace(/\(\( provider \)\)/g, provider)
        .replace(/\(\( instance_type \)\)/g, instanceType);

    document.getElementById('yamlOutput').textContent = output;
    document.getElementById('output').style.display = 'block';
    
    // Trigger syntax highlighting if available (MkDocs dependent)
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
</script>
