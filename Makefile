up: ./init.sh
	@echo "🚀 Starting Docker services..."
	docker compose up -d
	docker logs -f $(shell docker ps -q)
	@echo "🎉 All services started!"

# עצירת כל המכולות
down:
	@echo "🛑 Stopping Docker services..."
	docker compose down
	@echo "✅ All services stopped."

# מחיקה מלאה (בזהירות!)
clean: down
	@echo "⚠️ Removing .env and backup files..."
	rm -f .env .env.bak
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