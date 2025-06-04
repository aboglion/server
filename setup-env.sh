#!/bin/bash

# Script to set up environment for n8n and generate SSL certificates

# Generate random encryption key
ENCRYPTION_KEY=$(openssl rand -hex 24)

# Create .env file
echo "# Environment variables for n8n" > .env
echo "N8N_ENCRYPTION_KEY=$ENCRYPTION_KEY" >> .env

echo "Created .env file with random encryption key"

# Check if SSL certificates exist, if not generate them
if [ ! -f "n8n/ssl/privkey.pem" ] || [ ! -f "n8n/ssl/fullchain.pem" ]; then
    echo "SSL certificates not found, generating them..."
    cd n8n && bash generate-ssl-certs.sh
    cd ..
else
    echo "SSL certificates already exist"
fi

echo "Environment setup complete!"
echo "You can now run 'docker-compose up' to start the services"