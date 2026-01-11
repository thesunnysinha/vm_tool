# EC2 Deployment with GitHub Actions - Complete Guide

This guide shows you how to set up automated deployment from GitHub Actions to your EC2 instance using vm_tool.

---

## Prerequisites

1. **EC2 Instance** running Ubuntu/Debian
2. **GitHub Repository** with your project
3. **SSH Access** to EC2 instance
4. **Docker** installed on EC2 (or use vm_tool to install it)

---

## Step 1: Prepare Your EC2 Instance

### 1.1 Connect to EC2

```bash
ssh -i your-key.pem ubuntu@your-ec2-ip
```

### 1.2 Install Docker (if not already installed)

```bash
# Update packages
sudo apt update

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Logout and login again
exit
```

### 1.3 Create Deployment User (Recommended)

```bash
# Create deploy user
sudo adduser deploy
sudo usermod -aG docker deploy
sudo usermod -aG sudo deploy
```

---

## Step 2: Set Up SSH Keys for GitHub Actions

### 2.1 Generate SSH Key Pair

On your **local machine**:

```bash
# Generate new SSH key for deployment
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github_deploy_key

# This creates:
# - github_deploy_key (private key - for GitHub Secrets)
# - github_deploy_key.pub (public key - for EC2)
```

### 2.2 Add Public Key to EC2

```bash
# Copy public key content
cat ~/.ssh/github_deploy_key.pub

# SSH to EC2 and add to authorized_keys
ssh ubuntu@your-ec2-ip
mkdir -p ~/.ssh
echo "YOUR_PUBLIC_KEY_CONTENT" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh
exit
```

### 2.3 Test SSH Connection

```bash
ssh -i ~/.ssh/github_deploy_key ubuntu@your-ec2-ip
```

---

## Step 3: Configure GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add these secrets:

| Secret Name   | Value                          | Description             |
| ------------- | ------------------------------ | ----------------------- |
| `EC2_HOST`    | `your-ec2-ip`                  | EC2 instance IP address |
| `EC2_USER`    | `ubuntu` or `deploy`           | SSH user                |
| `EC2_SSH_KEY` | Content of `github_deploy_key` | Private SSH key         |

To get the private key content:

```bash
cat ~/.ssh/github_deploy_key
```

---

## Step 4: Prepare Your Project

### 4.1 Create docker-compose.yml

In your project root:

```yaml
version: "3.8"

services:
  web:
    build: .
    ports:
      - "80:8000"
    environment:
      - NODE_ENV=production
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### 4.2 Create Dockerfile

```dockerfile
FROM node:18-alpine
# or FROM python:3.11-slim
# or whatever your stack needs

WORKDIR /app
COPY package*.json ./
RUN npm install --production
COPY . .
EXPOSE 8000
CMD ["npm", "start"]
```

### 4.3 Create .env.example

```bash
# Copy this to .env on server
DATABASE_URL=postgresql://user:pass@localhost/db
API_KEY=your-api-key
```

---

## Step 5: Generate GitHub Actions Workflow

### Option A: Using vm_tool (Recommended)

```bash
# Install vm_tool locally
pip install vm-tool

# Generate workflow
vm_tool generate-pipeline \
  --platform github \
  --strategy docker \
  --monitoring
```

This creates `.github/workflows/deploy.yml`

### Option B: Manual Creation

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to EC2

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up SSH
        run: |
          mkdir -p ~/.ssh
          echo "${{ secrets.EC2_SSH_KEY }}" > ~/.ssh/deploy_key
          chmod 600 ~/.ssh/deploy_key
          ssh-keyscan -H ${{ secrets.EC2_HOST }} >> ~/.ssh/known_hosts

      - name: Deploy to EC2
        run: |
          ssh -i ~/.ssh/deploy_key ${{ secrets.EC2_USER }}@${{ secrets.EC2_HOST }} << 'EOF'
            cd ~/app || mkdir -p ~/app && cd ~/app
            
            # Pull latest code
            if [ -d .git ]; then
              git pull origin main
            else
              git clone https://github.com/${{ github.repository }} .
            fi
            
            # Deploy with docker-compose
            docker-compose down
            docker-compose pull
            docker-compose up -d --build
            
            # Health check
            sleep 10
            curl -f http://localhost:8000/health || exit 1
          EOF

      - name: Verify deployment
        run: |
          ssh -i ~/.ssh/deploy_key ${{ secrets.EC2_USER }}@${{ secrets.EC2_HOST }} \
            'docker-compose ps'
```

---

## Step 6: Enhanced Workflow with vm_tool Features

For production-grade deployment with all safety features:

```yaml
name: Production Deploy to EC2

on:
  push:
    branches: [main]
  workflow_dispatch:

env:
  EC2_HOST: ${{ secrets.EC2_HOST }}
  EC2_USER: ${{ secrets.EC2_USER }}

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install vm_tool
        run: pip install vm-tool

      - name: Set up SSH
        run: |
          mkdir -p ~/.ssh
          echo "${{ secrets.EC2_SSH_KEY }}" > ~/.ssh/deploy_key
          chmod 600 ~/.ssh/deploy_key
          ssh-keyscan -H $EC2_HOST >> ~/.ssh/known_hosts

      - name: Create inventory file
        run: |
          cat > inventory.yml << EOF
          all:
            hosts:
              production:
                ansible_host: $EC2_HOST
                ansible_user: $EC2_USER
                ansible_ssh_private_key_file: ~/.ssh/deploy_key
          EOF

      - name: Copy files to EC2
        run: |
          scp -i ~/.ssh/deploy_key docker-compose.yml $EC2_USER@$EC2_HOST:~/app/
          scp -i ~/.ssh/deploy_key -r . $EC2_USER@$EC2_HOST:~/app/

      - name: Create backup
        run: |
          ssh -i ~/.ssh/deploy_key $EC2_USER@$EC2_HOST \
            'cd ~/app && tar -czf ~/backups/backup-$(date +%Y%m%d-%H%M%S).tar.gz .'

      - name: Deploy with health checks
        run: |
          vm_tool deploy-docker \
            --host $EC2_HOST \
            --user $EC2_USER \
            --compose-file ~/app/docker-compose.yml \
            --inventory inventory.yml \
            --health-port 8000 \
            --health-url http://$EC2_HOST:8000/health \
            --force

      - name: Verify deployment
        run: |
          ssh -i ~/.ssh/deploy_key $EC2_USER@$EC2_HOST << 'EOF'
            cd ~/app
            docker-compose ps
            docker-compose logs --tail=50
          EOF

      - name: Rollback on failure
        if: failure()
        run: |
          ssh -i ~/.ssh/deploy_key $EC2_USER@$EC2_HOST << 'EOF'
            cd ~/app
            LATEST_BACKUP=$(ls -t ~/backups/*.tar.gz | head -1)
            tar -xzf $LATEST_BACKUP
            docker-compose up -d
          EOF
```

---

## Step 7: Test Your Setup

### 7.1 Local Test

```bash
# Test SSH connection
ssh -i ~/.ssh/github_deploy_key ubuntu@your-ec2-ip

# Test docker-compose
cd ~/app
docker-compose config
docker-compose up -d
```

### 7.2 Trigger GitHub Actions

```bash
# Make a small change
echo "# Test deployment" >> README.md
git add .
git commit -m "test: trigger deployment"
git push origin main
```

Watch the deployment in GitHub Actions tab.

---

## Step 8: Production Best Practices

### 8.1 Use Environment-Specific Configs

```bash
# On EC2, create .env file
cat > ~/app/.env << EOF
NODE_ENV=production
DATABASE_URL=postgresql://...
API_KEY=...
EOF
```

### 8.2 Set Up Monitoring

```yaml
# Add to docker-compose.yml
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
```

### 8.3 Configure Nginx Reverse Proxy

```bash
# On EC2
sudo apt install nginx

# Create nginx config
sudo nano /etc/nginx/sites-available/myapp

# Add:
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Enable site
sudo ln -s /etc/nginx/sites-available/myapp /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Troubleshooting

### SSH Connection Fails

```bash
# Check SSH key permissions
chmod 600 ~/.ssh/github_deploy_key

# Test connection with verbose output
ssh -vvv -i ~/.ssh/github_deploy_key ubuntu@your-ec2-ip

# Check EC2 security group allows SSH (port 22)
```

### Docker Permission Denied

```bash
# On EC2
sudo usermod -aG docker $USER
# Logout and login again
```

### Deployment Fails

```bash
# Check logs on EC2
ssh ubuntu@your-ec2-ip
cd ~/app
docker-compose logs

# Check GitHub Actions logs
# Go to Actions tab → Click on failed workflow → View logs
```

### Health Check Fails

```bash
# Test endpoint manually
curl http://your-ec2-ip:8000/health

# Check if port is open
nc -zv your-ec2-ip 8000

# Check EC2 security group allows port 8000
```

---

## Complete Example Repository Structure

```
your-project/
├── .github/
│   └── workflows/
│       └── deploy.yml
├── src/
│   └── app.js
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── package.json
└── README.md
```

---

## Security Checklist

- [ ] SSH keys are in GitHub Secrets (not in code)
- [ ] EC2 security group allows only necessary ports
- [ ] Deploy user has minimal permissions
- [ ] Environment variables in .env (not in code)
- [ ] Regular backups configured
- [ ] SSL/TLS certificate installed (use Let's Encrypt)
- [ ] Firewall configured (ufw)
- [ ] Regular security updates

---

## Next Steps

1. Set up domain name and SSL
2. Configure automated backups
3. Set up monitoring and alerts
4. Implement blue-green deployments
5. Add staging environment

---

## Quick Reference

```bash
# Deploy manually
vm_tool deploy-docker --host IP --user USER

# View deployment history
vm_tool history --host IP

# Rollback
vm_tool rollback --host IP

# Check drift
vm_tool drift-check --host IP

# Create backup
vm_tool backup create --host IP --paths /app
```
