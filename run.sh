#!/bin/bash
set -e

# טען משתנה אם קיים
load_key_if_exists() {
    if [ -f ".n8n_env.sh" ]; then
        echo "🔁 Found existing encryption key, exporting..."
        return 0
    fi
    return 1
}

# ייצר מפתח אם לא קיים
if ! load_key_if_exists; then
    echo "🔐 Generating random encryption key..."
    ENCRYPTION_KEY=$(openssl rand -hex 24)

    echo "📄 Creating .env file..."
    echo "N8N_ENCRYPTION_KEY=$ENCRYPTION_KEY" > .env

    echo "📝 Saving exportable key to .n8n_env.sh"
    echo "export N8N_ENCRYPTION_KEY=$ENCRYPTION_KEY" > .n8n_env.sh

    echo "✅ New encryption key saved."
fi

# טען אותו לסביבה הנוכחית (אם מקורבל)
if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
    source .n8n_env.sh
    echo "✅ Key loaded to current shell."
fi

# בדיקת SSL
echo "🔍 Checking for existing SSL certificates..."
if [ ! -f "n8n/ssl/privkey.pem" ] || [ ! -f "n8n/ssl/fullchain.pem" ]; then
    echo "🔧 Generating SSL certificates..."
    cd n8n && bash generate-ssl-certs.sh && cd ..
else
    echo "✅ SSL certificates already exist."
fi

echo "🚀 Starting docker-compose..."
docker compose up -d
echo "🎉 Environment and services started successfully!"
echo "🔑 Encryption key in this shell:"
echo "   $N8N_ENCRYPTION_KEY"
