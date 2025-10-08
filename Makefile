# Makefile לניהול שירותי Docker
# ---------------------------------
# מגדיר את כל השירותים בפרויקט כדי להקל על ניהולם
SERVICES := n8n caddy searxng browserless

# Phony targets: מצהיר שאלו פקודות ולא שמות של קבצים
.PHONY: all up down restart logs status build pull update update-all push clean purge help

# פקודת ברירת המחדל שתרוץ אם נריץ 'make' ללא פרמטרים
.DEFAULT_GOAL := help

## ------------------ פקודות בסיסיות ------------------
up: ## 🚀 מפעיל את כל השירותים ברקע
	@echo "🚀 Starting all Docker services in the background..."
	docker compose up -d
	@echo "✅ All services are up and running. Use 'make logs' to see the logs."

down: ## 🛑 עוצר ומסיר את כל הקונטיינרים של הפרויקט
	@echo "🛑 Stopping and removing project containers..."
	docker compose down
	@echo "✅ All services stopped."

restart: ## 🔄 מבצע הפעלה מחדש לכל השירותים
	@echo "🔄 Restarting all services..."
	docker compose restart
	@echo "✅ All services restarted."

logs: ## 📜 מציג את הלוגים של כל השירותים (או שירות ספציפי)
	@echo "📜 Tailing logs. Press Ctrl+C to exit."
	@echo "Usage: make logs service=n8n"
	docker compose logs -f $(service)

status: ## 📊 מציג את הסטטוס הנוכחי של הקונטיינרים
	@echo "📊 Current status of services:"
	docker compose ps

## ------------------ פקודות עדכון ו-Git ------------------
build: ## 🏗️ בונה מחדש את האימג'ים (שימושי אם יש Dockerfile)
	@echo "🏗️ Building images from local Dockerfiles..."
	docker compose build

pull: ## 📥 מושך את הגרסאות האחרונות של כל האימג'ים
	@echo "📥 Pulling the latest versions of all Docker images..."
	docker compose pull
	@echo "✅ All images pulled."

update-all: pull up ## 🔄 מושך את כל האימג'ים ומפעיל מחדש את השירותים
	@echo "✅ All services have been updated and restarted."

# פקודה גנרית לעדכון שירות ספציפי
# דוגמה: make update service=n8n
update:
	@if [ -z "$(service)" ]; then \
		echo "Usage: make update service=<service_name>"; \
		exit 1; \
	fi
	@echo "🔄 Updating service: $(service)..."
	docker compose pull $(service)
	@if [ "$(service)" = "n8n" ]; then \
		echo "🔧 Fixing n8n data permissions..."; \
		sudo chown -R 1000:1000 ./n8n_data; \
	fi
	docker compose up -d --no-deps $(service)
	@echo "✅ Service $(service) updated successfully."

push: ## 📤 דוחף את השינויים המקומיים ל-GitHub
	@echo "🚀 Pushing changes to GitHub..."
	git add .
	@if ! git diff-index --quiet HEAD; then \
		git commit -m "Update via Makefile"; \
	fi
	git push
	@echo "✅ Changes pushed to GitHub."


## ------------------ פקודות ניקוי (זהירות!) ------------------
clean: down ## 🧹 מנקה את הפרויקט (מסיר קונטיינרים וווליומים של הפרויקט)
	@echo "🧹 Cleaning up the project..."
	docker compose down --volumes --remove-orphans
	@echo "✅ Project cleaned successfully."

purge: ## ☢️ מחיקה מלאה ומסוכנת של *כל* הדוקר במערכת!
	@echo "☢️ WARNING! This will permanently delete ALL Docker containers, images, and volumes on your system."
	@read -p "Are you absolutely sure? (y/N) " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		make down; \
		echo "🔥 Removing all containers..."; \
		docker rm -f $$(docker ps -aq) || true; \
		echo "🔥 Removing all images..."; \
		docker rmi -f $$(docker images -q) || true; \
		echo "🔥 Removing all volumes..."; \
		docker volume rm $$(docker volume ls -q) || true; \
		echo "🔥 Pruning Docker system..."; \
		docker system prune -af --volumes; \
		echo "✅ Docker system purged."; \
	else \
		echo "Aborted."; \
	fi

## ------------------ עזרה ------------------
help: ## ℹ️ מציג את רשימת הפקודות הזמינות
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
