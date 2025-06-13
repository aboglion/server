n8n & Person Detection API — Setup & Run Guide

This repository integrates n8n (automation & workflow)
with a Person Detection API powered by YOLOv5.
Both run seamlessly via Docker Compose for easy setup and management.
🚀 Initial Setup
1. 🧪 Run the initialization script:

sudo make up

The script performs the following tasks automatically:

    Checks for an existing .env file.

        If missing, it generates one with a secure random encryption key (N8N_ENCRYPTION_KEY).

    Checks for SSL certificates inside n8n/ssl.

        If missing, it runs generate-ssl-certs.sh to create self-signed certificates.

    Starts the Docker Compose services in detached mode (docker-compose up -d).

2. 🧠 Load environment variables into your current shell

To use the encryption key (N8N_ENCRYPTION_KEY) in your shell session, run:

source .n8n_env.sh

Verify the key is loaded properly:

echo "$N8N_ENCRYPTION_KEY"

You should see a 48-character hex string like:
c7be6e96b402687231db62abc5f13207453eb8f447eef07a
3. 🔁 Future Runs and Service Management

To restart or start services in the future, simply run:

docker-compose up -d

If you need to reinitialize the environment variables and SSL certs, run:

sudo ./init.sh

📂 Directory Structure

SERVER/
├── run.sh                  # Main launcher script (optional)
├── .env                    # Environment variables file
├── .n8n_env.sh             # Export script for N8N_ENCRYPTION_KEY
├── docker-compose.yml      # Docker Compose configuration
├── Person_Detection_API/
│   └── yolo11l.pt          # YOLO model file
└── n8n/
    ├── ssl/
    │   ├── privkey.pem     # SSL private key
    │   └── fullchain.pem   # SSL certificate chain
    └── generate-ssl-certs.sh # SSL cert generation script

🌐 Services Overview
Service	Port	Description
n8n	8743	HTTPS interface for workflow GUI
Person Detection API	3000	YOLOv5-based person detection API
🔐 Notes & Recommendations

    SSL certificates generated are self-signed for development/testing.
    For production, replace with certificates from Let's Encrypt or another CA.

    The encryption key (N8N_ENCRYPTION_KEY) is critical for securing sensitive data inside n8n.
    Never share it publicly.

    You may consider setting up a reverse proxy (e.g., Nginx, Traefik) for better HTTPS management and access control.