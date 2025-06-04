
# עצירת כל המכולות
down:
	@echo "🛑 Stopping Docker services..."
	docker compose down
	@echo "✅ All services stopped."

# מחיקה מלאה (בזהירות!)
clean: down
	@echo "⚠️ Removing .env and backup files..."
	rm -f .env .env.bak
	docker rm -f $$(docker ps -aq)
	docker rmi -f $$(docker images -q)
	@echo "🗑️ Removing all volumes..."
	docker volume rm $$(docker volume ls -q)
	@echo "🧹 Cleaning up Docker system...
	docker system prune -f --volumes
	@echo "🧹 Clean complete."

update: 
	@echo "🔄 Updating code from github.."
	git pull
	@echo "✅ Images updated."

push:
	@echo "🚀 Pushing changes to GitHub..."
	git add .
	git commit -m "Update code"
	git push
	@echo "✅ Changes pushed to GitHub."


logs:
	@echo "📜 Showing logs for n8n..."
	docker logs -f $$(docker ps --filter "name=n8n" -q)

	
up: ./init.sh
	@echo "🚀 Starting Docker services..."
	docker compose up -d
	logs
	@echo "🎉 All services started!"
