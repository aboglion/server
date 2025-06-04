#!/bin/bash
set -e

ENV_FILE=".env"
ENV_VAR_NAME="N8N_ENCRYPTION_KEY"

is_valid_key() {
    [[ "$1" =~ ^[a-f0-9]{48}$ ]]
}

generate_key() {
    openssl rand -hex 24
}

extract_key() {
    grep "^$ENV_VAR_NAME=" "$ENV_FILE" | cut -d '=' -f2
}

# אם אין קובץ .env – צור חדש עם מפתח תקין
if [ ! -f "$ENV_FILE" ]; then
    echo "📄 Creating $ENV_FILE with secure key..."
    KEY=$(generate_key)
    echo "$ENV_VAR_NAME=$KEY" > "$ENV_FILE"
    echo "✅ $ENV_FILE created with key."
else
    # קובץ קיים – נבדוק אם יש את המשתנה
    if grep -q "^$ENV_VAR_NAME=" "$ENV_FILE"; then
        CURRENT_KEY=$(extract_key)
        if is_valid_key "$CURRENT_KEY"; then
            echo "🔁 Existing key is valid. Using it."
        else
            echo "⚠️ Found invalid key. Regenerating..."
            NEW_KEY=$(generate_key)
            # מחליף את השורה עם המפתח הישן בחדש
            sed -i.bak "s/^$ENV_VAR_NAME=.*/$ENV_VAR_NAME=$NEW_KEY/" "$ENV_FILE"
            echo "✅ Key replaced."
        fi
    else
        echo "➕ Key missing. Adding to $ENV_FILE..."
        echo "$ENV_VAR_NAME=$(generate_key)" >> "$ENV_FILE"
        echo "✅ Key added."
    fi
fi

# הצגה לצורך בדיקה
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
if [ ! -d "${HOME}/n8n_data" ]; then
    echo "📂 Creating data directory...
    mkdir -p ${HOME}/n8n_data
    echo "✅ Data directory created."
else
    echo "✅ Data directory already exists."
fi
# מתן הרשאות לתיקיית נתונים ולתיקיית SSL

echo "🔒 Setting permissions for data directory and SSL..."
chmod -R 777 ${HOME}/n8n_data ./n8n/ssl
