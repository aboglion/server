#!/bin/bash

# Script to obtain Let's Encrypt SSL certificates for N8N
# This script requires certbot to be installed and a domain name pointing to this server

# Check if domain name is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <domain-name>"
  echo "Example: $0 n8n.example.com"
  exit 1
fi

DOMAIN=$1
EMAIL=${2:-"admin@$DOMAIN"}

# Create SSL directory if it doesn't exist
mkdir -p ssl

# Check if certbot is installed
if ! command -v certbot &> /dev/null; then
  echo "Error: certbot is not installed."
  echo "Please install certbot first:"
  echo "  Ubuntu/Debian: sudo apt-get install certbot"
  echo "  CentOS/RHEL: sudo yum install certbot"
  exit 1
fi

# Obtain certificates using certbot
echo "Obtaining Let's Encrypt certificates for $DOMAIN..."
certbot certonly --standalone --preferred-challenges http \
  -d $DOMAIN --agree-tos --email $EMAIL --non-interactive

# Copy certificates to the ssl directory
echo "Copying certificates to ssl directory..."
cp /etc/letsencrypt/live/$DOMAIN/privkey.pem ssl/
cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem ssl/

# Set proper permissions
chmod 600 ssl/privkey.pem
chmod 644 ssl/fullchain.pem

echo "Let's Encrypt SSL certificates obtained successfully!"
echo "Files created:"
echo "  - ssl/privkey.pem (private key)"
echo "  - ssl/fullchain.pem (certificate)"
echo ""
echo "Don't forget to set up a renewal cron job for your certificates:"
echo "0 0 1 * * certbot renew --quiet && cp /etc/letsencrypt/live/$DOMAIN/privkey.pem /path/to/n8n/ssl/ && cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem /path/to/n8n/ssl/"