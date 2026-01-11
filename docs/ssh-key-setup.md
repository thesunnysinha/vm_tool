# SSH Key Setup Guide for GitHub Actions

## Quick Guide: Get Your SSH Private Key

### Step 1: Find Your SSH Key

On your **local machine**, run:

```bash
# For RSA keys (most common)
cat ~/.ssh/id_rsa

# OR for Ed25519 keys (newer, recommended)
cat ~/.ssh/id_ed25519
```

### Step 2: Copy the Output

Copy the **ENTIRE** output, including:

- `-----BEGIN ... PRIVATE KEY-----`
- All the key content
- `-----END ... PRIVATE KEY-----`

Example output:

```
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
...
(many lines)
...
-----END OPENSSH PRIVATE KEY-----
```

### Step 3: Add to GitHub Secrets

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `EC2_SSH_KEY`
5. Value: Paste the entire key content
6. Click **Add secret**

### Step 4: Add Other Required Secrets

Also add these secrets:

| Secret Name | Value               | Example              |
| ----------- | ------------------- | -------------------- |
| `EC2_HOST`  | Your EC2 IP address | `54.123.45.67`       |
| `EC2_USER`  | SSH username        | `ubuntu` or `deploy` |

---

## Don't Have an SSH Key?

### Generate New SSH Key

```bash
# Generate Ed25519 key (recommended)
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github_deploy

# This creates two files:
# - github_deploy (private key - for GitHub Secrets)
# - github_deploy.pub (public key - for EC2)
```

### Add Public Key to EC2

```bash
# 1. Copy public key
cat ~/.ssh/github_deploy.pub

# 2. SSH to EC2
ssh ubuntu@YOUR_EC2_IP

# 3. Add public key
mkdir -p ~/.ssh
echo "PASTE_PUBLIC_KEY_HERE" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh
exit
```

### Test Connection

```bash
ssh -i ~/.ssh/github_deploy ubuntu@YOUR_EC2_IP
```

If successful, you're ready!

---

## Troubleshooting

### "Permission denied (publickey)"

**Problem**: Public key not on EC2 or wrong permissions

**Solution**:

```bash
# On EC2
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys

# Verify public key is there
cat ~/.ssh/authorized_keys
```

### "Connection timed out"

**Problem**: EC2 security group doesn't allow SSH

**Solution**:

1. Go to AWS Console → EC2 → Security Groups
2. Find your instance's security group
3. Add inbound rule:
   - Type: SSH
   - Port: 22
   - Source: 0.0.0.0/0 (or restrict to GitHub IPs)

### "Host key verification failed"

**Problem**: EC2 host key not in known_hosts

**Solution**: The workflow handles this automatically with `ssh-keyscan`

### Wrong Key Format

**Problem**: Key has wrong format or line breaks

**Solution**:

```bash
# Get key in one command (preserves formatting)
cat ~/.ssh/id_rsa | pbcopy  # macOS
cat ~/.ssh/id_rsa | xclip   # Linux

# Then paste directly into GitHub Secrets
```

---

## Security Best Practices

### 1. Use Separate Keys for CI/CD

```bash
# Don't use your personal SSH key
# Generate a dedicated key for deployments
ssh-keygen -t ed25519 -C "ci-cd-deploy" -f ~/.ssh/ci_deploy
```

### 2. Restrict Key Permissions on EC2

```bash
# On EC2, create dedicated deploy user
sudo adduser deploy
sudo usermod -aG docker deploy

# Add public key only for deploy user
sudo -u deploy mkdir -p /home/deploy/.ssh
sudo -u deploy echo "PUBLIC_KEY" >> /home/deploy/.ssh/authorized_keys
```

### 3. Use GitHub Environment Secrets

For production deployments, use Environment secrets:

1. Repository → Settings → Environments
2. Create "production" environment
3. Add secrets there
4. Require manual approval

---

## Quick Reference

```bash
# View private key (for GitHub Secret)
cat ~/.ssh/id_rsa

# View public key (for EC2)
cat ~/.ssh/id_rsa.pub

# Generate new key
ssh-keygen -t ed25519 -C "deploy-key"

# Test SSH connection
ssh -i ~/.ssh/key_file user@host

# Copy key to clipboard (macOS)
cat ~/.ssh/id_rsa | pbcopy

# Copy key to clipboard (Linux)
cat ~/.ssh/id_rsa | xclip -selection clipboard
```

---

## Video Tutorial

For a visual guide, search YouTube for:

- "GitHub Actions SSH deployment"
- "Add SSH key to GitHub Secrets"
- "Deploy to EC2 with GitHub Actions"
