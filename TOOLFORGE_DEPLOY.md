# Toolforge Deployment Setup

This document explains how to set up automated deployment to Toolforge using GitHub Actions.

## Required GitHub Secrets

You need to configure the following secrets in your GitHub repository settings (Settings → Secrets and variables → Actions):

### 1. SSH_PRIVATE_KEY
Your SSH private key for accessing Toolforge. Generate this on your local machine:

```bash
ssh-keygen -t ed25519 -C "toolforge-deploy-key"
```

- Copy the **private key** content from `~/.ssh/id_ed25519` (or the file you specified)
- Add the **public key** to Toolforge: `ssh-copy-id <username>@login.toolforge.org`

### 2. SSH_KNOWN_HOSTS
The SSH known hosts entry for Toolforge servers:

```bash
ssh-keyscan login.toolforge.org
```

Copy the output and add it as the `SSH_KNOWN_HOSTS` secret.

### 3. SSH_HOST
The Toolforge SSH host:
```
login.toolforge.org
```

### 4. SSH_USER
Your Toolforge username (typically your Wikimedia username).

## Deployment Workflow

The workflow automatically deploys when:
- You push to the `main` branch
- Changes are made to:
  - `uwsgi.ini`
  - Any Python files (`**/*.py`)
  - `requirements.txt`
  - Template files
  - Static files
  - The workflow file itself

You can also trigger deployment manually from the GitHub Actions tab using "Run workflow".

## Deployment Steps

The workflow performs these steps:
1. Checks out the code
2. Sets up Python 3.11
3. Installs dependencies
4. Configures SSH access
5. Connects to Toolforge and:
   - Fetches and pulls the latest code
   - Restarts the webservice pods
   - Runs database migrations
   - Collects static files
   - Restarts the webservice with 4Gi memory
   - Checks the service status

## Toolforge Setup

Before the first deployment, ensure you have:

1. Created the tool account on Toolforge
2. Cloned the repository to `~/www/python/`
3. Created a `.env` file with your configuration
4. Set up a ToolsDB database (if needed)
5. Configured `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` in your Django settings

## Manual Deployment

If you need to deploy manually, SSH into Toolforge and run:

```bash
become checklist git -C ./www/python pull origin main
become checklist webservice --mem 512Mi python3.11 shell -- webservice-python-bootstrap
become checklist webservice --mem 512Mi python3.11 shell -- ./www/python/venv/bin/python ./www/python/manage.py migrate
become checklist webservice --mem 512Mi python3.11 shell -- ./www/python/venv/bin/python ./www/python/manage.py collectstatic --noinput
become checklist webservice python3.11 restart --mem 4Gi
```

## Troubleshooting

- **Authentication fails**: Check that your SSH key is properly added to both GitHub secrets and Toolforge
- **Deployment fails**: Check the GitHub Actions logs for specific error messages
- **Service won't start**: SSH into Toolforge and check logs with `webservice python3.11 status` and `kubectl logs`
