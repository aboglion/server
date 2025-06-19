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

clean-images:
	@echo "⚠️ Removing .env and backup files..."
	rm -f .env .env.bak
	@if [ "$$(docker ps -aq)" != "" ]; then docker rm -f $$(docker ps -aq); fi
	@if [ "$$(docker images -q)" != "" ]; then docker rmi -f $$(docker images -q); fi

update:
	@echo "🔄 Updating code from GitHub..."
	git pull
	@echo "✅ Code updated from GitHub."

update_n8n:
	@echo "🔄 Updating N8N Docker image..."
	docker compose pull n8n
	@echo "🛑 Stopping N8N container..."
	docker compose stop n8n
	sudo chown -R 1000:1000 /n8n
	@echo "🚀 Starting N8N container with updated image..."
	docker compose up -d n8n
	@echo "📜 Following N8N logs..."
	docker logs -f $$(docker ps --filter "name=n8n" -q)

update_person_detection_api:
	@echo "🔄 Updating person_detection_api Docker image..."
	docker compose pull person_detection_api
	@echo "🛑 Stopping person_detection_api container..."
	docker compose stop person_detection_api
	@echo "🚀 Starting person_detection_api container with updated image..."
	docker compose up -d person_detection_api
	@echo "📜 Following person_detection_api logs..."
	docker logs -f $$(docker ps --filter "name=person_detection_api" -q)

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
