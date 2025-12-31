#!/bin/bash
# Helper script to generate values for GitHub Secrets
# This script DISPLAYS the values - you still need to manually add them to GitHub

set -e

echo "=================================================="
echo "GitHub Secrets Setup Helper"
echo "=================================================="
echo ""
echo "This script will help you generate the values needed"
echo "for GitHub Secrets. You'll need to copy these values"
echo "to GitHub Settings → Secrets and variables → Actions"
echo ""

# Check if deploy key exists
DEPLOY_KEY="$HOME/.ssh/toolforge_deploy_key"

if [ ! -f "$DEPLOY_KEY" ]; then
    echo "📝 Step 1: Generate SSH Deploy Key"
    echo "=================================="
    read -p "Generate a new SSH key for deployment? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ssh-keygen -t ed25519 -f "$DEPLOY_KEY" -C "github-actions-deploy" -N ""
        echo "✅ SSH key generated!"
        echo ""
    else
        echo "❌ Cancelled. Please generate the key manually:"
        echo "   ssh-keygen -t ed25519 -f ~/.ssh/toolforge_deploy_key -C 'github-actions-deploy'"
        exit 1
    fi
else
    echo "✅ Found existing deploy key at $DEPLOY_KEY"
    echo ""
fi

echo "=================================================="
echo "📋 PUBLIC KEY (Add to Toolforge)"
echo "=================================================="
echo "Copy this public key and add it to Toolforge:"
echo "  ssh <username>@login.toolforge.org"
echo "  echo 'PUBLIC_KEY_BELOW' >> ~/.ssh/authorized_keys"
echo ""
cat "${DEPLOY_KEY}.pub"
echo ""
echo ""

echo "=================================================="
echo "🔐 SECRET 1: SSH_PRIVATE_KEY"
echo "=================================================="
echo "Copy EVERYTHING below (including BEGIN/END lines):"
echo ""
cat "$DEPLOY_KEY"
echo ""
echo ""

echo "=================================================="
echo "🔐 SECRET 2: SSH_KNOWN_HOSTS"
echo "=================================================="
echo "Copy ALL lines below:"
echo ""
ssh-keyscan login.toolforge.org 2>/dev/null
echo ""
echo ""

echo "=================================================="
echo "🔐 SECRET 3: SSH_HOST"
echo "=================================================="
echo "Copy this value:"
echo ""
echo "login.toolforge.org"
echo ""
echo ""

echo "=================================================="
echo "🔐 SECRET 4: SSH_USER"
echo "=================================================="
read -p "Enter your Toolforge username: " TOOLFORGE_USER
echo ""
echo "Copy this value:"
echo ""
echo "$TOOLFORGE_USER"
echo ""
echo ""

echo "=================================================="
echo "✅ Next Steps"
echo "=================================================="
echo "1. Add the PUBLIC KEY to Toolforge (shown above)"
echo "2. Go to your GitHub repository"
echo "3. Navigate to: Settings → Secrets and variables → Actions"
echo "4. Click 'New repository secret' and add each of the 4 secrets above"
echo "5. Test the deployment from the Actions tab"
echo ""
echo "📖 For detailed instructions, see GITHUB_SECRETS_SETUP.md"
echo ""
