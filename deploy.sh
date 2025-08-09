#!/bin/bash
# Deployment script for Render

echo "Preparing deployment to Render..."

# Add all changes
git add .

# Commit changes
git commit -m "Optimize for Render free tier: fix PyTorch compatibility, add lazy loading, reduce memory usage"

# Push to remote repository
git push origin main

echo "Changes pushed to repository. Render should start auto-deploying."
echo "Check your Render dashboard for deployment status."
