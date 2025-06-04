
# עצירת כל המכולות
down:
	@echo "🛑 Stopping Docker services..."
	docker compose down
	@echo "✅ All services stopped."

# מחיקה מלאה (בזהירות!)
clean: down
	@echo "⚠️ Removing .env and backup files..."
	rm -f .env .env.bak
	@if [ "$$(docker ps -aq)" != "" ]; then docker rm -f $$(docker ps -aq); fi
	@if [ "$$(docker images -q)" != "" ]; then docker rmi -f $$(docker images -q); fi
	@echo "🗑️ Removing all volumes..."
	@if [ "$$(docker volume ls -q)" != "" ]; then docker volume rm $$(docker volume ls -q); fi
	@echo "🧹 Cleaning up Docker system..."
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
	$(MAKE) logs
	@echo "🎉 All services started!"

