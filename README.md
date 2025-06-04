# 📦 n8n & Person Detection API - Setup & Run Guide

This repository combines n8n (automation and workflow) with a Person Detection API using YOLOv5. Everything runs via Docker Compose for easy setup and management.

---

## 🚀 Initial Setup

### 1. 📁 Change into the project directory:
```bash
cd SERVER

2. 🧪 Run the installation script:

make up

The script will:

    Check for an existing .env file. If none exists, it will generate one with a random encryption key.

    Check for existing SSL certificates in n8n/ssl. If they don’t exist, it will run generate-ssl-certs.sh to generate them.

    Launch the services with docker-compose up -d.

3. 🧠 Load environment variables (required in your current shell):

This will load the N8N_ENCRYPTION_KEY into your current shell.
🧪 Verify Encryption Key Load

After sourcing the file, verify that the key is loaded correctly:

echo "$N8N_ENCRYPTION_KEY"

You should see a 48-character hex string (e.g., c7be6e96b402687231db62abc5f13207453eb8f447eef07a). If so, you’re all set ✅.
🔁 Future Runs

To restart the services in the future:

docker-compose up -d

If you need the N8N_ENCRYPTION_KEY available in your shell, run:

source .n8n_env.sh

🧰 run.sh Script Overview

The run.sh script performs the following steps:

    Generates (if needed) and saves a random N8N_ENCRYPTION_KEY to .env.

    Writes an export command to .n8n_env.sh so you can load the key later.

    Checks for SSL certificates in n8n/ssl and generates them if missing.

    Starts Docker Compose services.

📂 Directory Structure

SERVER/
├── run.sh
├── .env
├── .n8n_env.sh
├── docker-compose.yml
├── Person_Detection_API/
│   └── yolo11l.pt
└── n8n/
    ├── ssl/
    │   ├── privkey.pem
    │   └── fullchain.pem
    └── generate-ssl-certs.sh

🌐 Services
Service	Port	Description
n8n	8743	HTTPS interface for workflow GUI
Person Detection API	3000	YOLOv5-based person detection API
📍 Developer Tip

To avoid manually sourcing .n8n_env.sh every time, add the following to your ~/.bashrc or ~/.zshrc:

[ -f ~/SERVER/.n8n_env.sh ] && source ~/SERVER/.n8n_env.sh

    Optional Production Notes
    If you plan to deploy this in production, consider adding an Nginx reverse proxy and a systemd service unit to manage the Docker Compose stack. These are not included here but can be added later as needed.