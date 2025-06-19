#!/bin/bash
set -e

ENV_FILE=".env"
ENV_VAR_NAME="N8N_ENCRYPTION_KEY"

# התקנת certbot אם לא קיים
if ! command -v certbot &> /dev/null; then
  echo "🛠 Installing certbot..."
  sudo apt update && sudo apt install certbot -y
fi
if [ $? -ne 0 ]; then
    echo "❌ Failed to install certbot. Exiting."
    exit 1
fi

is_valid_key() {
    [[ "$1" =~ ^[a-f0-9]{48}$ ]]
}

generate_key() {
    openssl rand -hex 24
}

extract_key() {
    grep "^$ENV_VAR_NAME=" "$ENV_FILE" | cut -d '=' -f2
}

if [ ! -f "$ENV_FILE" ]; then
    echo "📄 Creating $ENV_FILE with secure key..."
    KEY=$(generate_key)
    echo "$ENV_VAR_NAME=$KEY" > "$ENV_FILE"
    echo "✅ $ENV_FILE created with key."
else
    if grep -q "^$ENV_VAR_NAME=" "$ENV_FILE"; then
        CURRENT_KEY=$(extract_key)
        if is_valid_key "$CURRENT_KEY"; then
            echo "🔁 Existing key is valid. Using it."
        else
            echo "⚠️ Found invalid key. Regenerating..."
            NEW_KEY=$(generate_key)
            sed -i.bak "s/^$ENV_VAR_NAME=.*/$ENV_VAR_NAME=$NEW_KEY/" "$ENV_FILE"
            echo "✅ Key replaced."
        fi
    else
        echo "➕ Key missing. Adding to $ENV_FILE..."
        echo "$ENV_VAR_NAME=$(generate_key)" >> "$ENV_FILE"
        echo "✅ Key added."
    fi
fi

# --- הצגת המפתח לבדיקות בלבד, מומלץ להסיר בפרודקשן ---
echo "==== .env ===="
cat "$ENV_FILE"
echo "=============="

# בדיקת SSL
echo "🔍 Checking SSL certs..."
if [ ! -f "n8n/ssl/privkey.pem" ] || [ ! -f "n8n/ssl/fullchain.pem" ]; then
    echo "🔧 Generating SSL certificates..."
    cd n8n && bash generate-ssl-certs.sh && cd ..
else
    echo "✅ SSL certs already exist."
fi

# יצירת תיקיית נתונים אם לא קיימת
if [ ! -d "n8n/data" ]; then
    echo "📂 Creating data directory..."
    mkdir -p n8n/data
else
    echo "📂 Data directory already exists."
fi

sudo chown -R 1000:1000 n8n
sudo chmod -R 700 n8n
sudo chmod 700 n8n/data
sudo chmod 700 n8n/config

chmod +x n8n/generate-ssl-certs.sh
sudo chown -R 1000:1000 /root/.n8n

echo "✅ Data directory is ready."
