.DEFAULT_GOAL := help

help:
	@echo ""
	@echo "שימוש ב-Makefile:"
	@echo "  make up                -- הרמה של כל השירותים (trader, n8n, caddy)"
	@echo "  make up-<service>      -- בניה והרמה של קונטיינר (trader, n8n, caddy)"
	@echo "  make down-<service>    -- עצירה ומחיקה של קונטיינר (לא מוחק volumes)"
	@echo "  make logs-<service>    -- צפייה בלוגים של קונטיינר"
	@echo "  make update            -- עדכון כל הפרויקט מגיט"
	@echo "  make clean             -- ניקוי אימג'ים שלא בהרצה"
	@echo ""

up:
	$(MAKE) pull
	$(MAKE) up-trader
	$(MAKE) up-n8n
	$(MAKE) up-caddy
	@echo ""
	@echo "שירותים הורמו בהצלחה!"
	@echo "כתובות גישה:"
	@echo "Trader:    https://aboglion.top:8744/trader/"
	@echo "n8n:       https://aboglion.top:8744/"
	@echo ""

up-trader:
	mkdir -p ../data_backup/TRADER/LOGS
	docker compose build trader
	docker compose up -d trader

down-trader:
	docker compose stop trader
	docker compose rm -f trader

logs-trader:
	docker logs -f $$(docker ps --filter "name=trader" -q)

up-n8n:
	mkdir -p ../data_backup/n8n_data
	sudo chown -R 1000:1000 ../data_backup/n8n_data/
	docker compose build n8n
	docker compose up -d n8n

down-n8n:
	docker compose stop n8n
	docker compose rm -f n8n

logs-n8n:
	docker logs -f $$(docker ps --filter "name=n8n" -q)

up-caddy:
	mkdir -p caddy/ssl
	# Corrected paths to be inside the TRADER build context
	mkdir -p ./TRADER/static/css 
	mkdir -p ./TRADER/static/js
	# Generate self-signed SSL certificate
	openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout caddy/ssl/privkey.pem -out caddy/ssl/fullchain.pem -subj "/CN=localhost" -addext "subjectAltName=DNS:localhost,DNS:aboglion.top"
	docker compose build caddy
	docker compose up -d caddy

down-caddy:
	docker compose stop caddy
	docker compose rm -f caddy

logs-caddy:
	docker logs -f $$(docker ps --filter "name=caddy" -q)

pull:
	git reset --hard HEAD
	git pull origin main
	sleep 4

clean:
	docker image prune -f

clean-all:
	docker stop $$(docker ps -aq) && docker rm -f $$(docker ps -a -aq) && docker rmi -f $$(docker images -q)  

format:
	docker rm -f $$(docker ps -aq) && docker rmi -f $$(docker images -q)  
	docker volume rm -f $$(docker volume ls -q)

push:
	git add .
	git commit -m "Update Makefile and docker-compose.yml"
	git push origin main
	@echo "Changes pushed to the repository."

del_trader_logs:
	rm -rf ../data_backup/TRADER/LOGS/*
	@echo "Logs deleted successfully."

data_trade:
	@echo "Data directories set to ../data_backup/TRADER/LOGS"
	cd ../data_backup/TRADER/LOGS

data_n8n:
	@echo "Data directories set to ../data_backup/n8n_data"
	cd ../data_backup/n8n_data