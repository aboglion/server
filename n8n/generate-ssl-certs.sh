#!/bin/bash

# Script to generate self-signed SSL certificates for N8N
# For production use, consider using Let's Encrypt certificates instead

# Create SSL directory if it doesn't exist
mkdir -p ssl

# Generate private key
openssl genrsa -out ssl/privkey.pem 2048

# Generate self-signed certificate
openssl req -new -x509 -key ssl/privkey.pem -out ssl/fullchain.pem -days 365 -subj "/CN=localhost" -addext "subjectAltName = DNS:localhost,IP:127.0.0.1"

# Set proper permissions
chmod 600 ssl/privkey.pem
chmod 644 ssl/fullchain.pem

echo "Self-signed SSL certificates generated successfully!"
echo "Files created:"
echo "  - ssl/privkey.pem (private key)"
echo "  - ssl/fullchain.pem (certificate)"
echo ""
echo "For production use, consider replacing these with Let's Encrypt certificates."