#!/bin/bash

DOMAIN="aboglion.top"
EMAIL="aboglion@gmail.com"
TARGET_DIR="$(pwd)/ssl"
DOCKER_COMPOSE_PATH="$(pwd)/docker-compose.yml"

# התקנת certbot אם לא קיים
if ! command -v certbot &> /dev/null; then
  echo "🛠 Installing certbot..."
  sudo apt update && sudo apt install certbot -y
fi

# עצירה זמנית של Docker כדי לשחרר את פורט 80
echo "🛑 Stopping Docker to allow certbot on port 80..."
docker compose down

# יצירת תיקיית ssl
mkdir -p "$TARGET_DIR"

# בקשת תעודה
echo "🔐 Requesting SSL certificate for $DOMAIN"
sudo certbot certonly --standalone --preferred-challenges http \
  -d "$DOMAIN" --agree-tos --email "$EMAIL" --non-interactive

# העתקת התעודות
echo "📁 Copying certificates to $TARGET_DIR"
sudo cp /etc/letsencrypt/live/$DOMAIN/privkey.pem "$TARGET_DIR/"
sudo cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem "$TARGET_DIR/"
sudo chmod 600 "$TARGET_DIR/privkey.pem"
sudo chmod 644 "$TARGET_DIR/fullchain.pem"

# הפעלת n8n מחדש
echo "🚀 Starting n8n with Docker"
docker compose up -d

# תוספת ל-cron
CRON_CMD="certbot renew --quiet && cp /etc/letsencrypt/live/$DOMAIN/privkey.pem $TARGET_DIR/ && cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem $TARGET_DIR/ && docker compose -f $DOCKER_COMPOSE_PATH restart"
CRON_JOB="0 0 1 * * $CRON_CMD"

if ! crontab -l 2>/dev/null | grep -q "$DOMAIN"; then
  (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
  echo "✅ Cron job added to renew certificate monthly."
else
  echo "ℹ️ Cron job already exists."
fi

echo "🎉 Setup complete. N8N is available at: https://$DOMAIN:8743"
