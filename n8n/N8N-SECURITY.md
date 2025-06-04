# N8N Security Configuration

This document provides instructions on how to set up and use the secure N8N configuration with a non-standard port and HTTPS.

## Overview of Changes

The following security enhancements have been implemented:

1. **Non-standard Port**: Changed the default N8N port from 5678 to 8743 to avoid port scanning detection
2. **HTTPS Support**: Configured N8N to use HTTPS instead of HTTP
3. **SSL Certificates**: Added support for SSL certificates
4. **Encryption Key**: Added a configurable encryption key for sensitive data

## Setup Instructions

### 1. Generate SSL Certificates

#### Option 1: Self-signed Certificates (for Development/Testing)

Run the provided script to generate self-signed certificates:

```bash
cd n8n
./generate-ssl-certs.sh
```

This will create:
- `ssl/privkey.pem` (private key)
- `ssl/fullchain.pem` (certificate)

#### Option 2: Let's Encrypt Certificates (for Production)

For production environments, use Let's Encrypt to obtain trusted certificates:

1. Make sure you have a domain name pointing to your server
2. Install certbot on your server
3. Run the provided script:

```bash
cd n8n
./setup-letsencrypt.sh your-domain.com
```

This will:
- Obtain certificates from Let's Encrypt
- Copy them to the ssl directory
- Provide instructions for certificate renewal

### 2. Start N8N

Start N8N with the secure configuration:

```bash
# For production
docker-compose up -d

# For development
docker-compose -f docker-compose.dev.yml up -d
```

### 3. Access N8N

Access N8N through your browser at:

```
https://localhost:8743
```

Or if using a domain:

```
https://your-domain.com:8743
```

## Additional Security Recommendations

1. **Firewall Configuration**: Configure your firewall to only allow access to port 8743 from trusted IP addresses
2. **Reverse Proxy**: Consider using a reverse proxy like Nginx or Traefik for additional security layers
3. **Regular Updates**: Keep N8N and all dependencies up to date
4. **Access Control**: Implement proper authentication and authorization
5. **Monitoring**: Set up monitoring and alerting for suspicious activities
6. **Encryption Key**: The encryption key is automatically generated when the container starts. If you need to persist data between restarts, you should set a fixed encryption key in the docker-compose file.

## Troubleshooting

### Certificate Issues

If you encounter certificate issues:

1. Verify that the certificates are correctly generated and placed in the n8n/ssl directory
2. Check the permissions of the certificate files
3. Ensure the paths in the docker-compose files match the actual certificate locations

### Connection Issues

If you can't connect to N8N:

1. Verify that the container is running: `docker-compose ps`
2. Check the logs for errors: `docker-compose logs n8n`
3. Ensure the port is accessible and not blocked by a firewall