.DEFAULT_GOAL := help

help:
	@echo ""
	@echo "שימוש ב-Makefile:"
	@echo "  make up                -- הרמה של כל השירותים (trader, n8n, nginx)"
	@echo "  make up-<service>      -- בניה והרמה של קונטיינר (trader, n8n, nginx)"
	@echo "  make down-<service>    -- עצירה ומחיקה של קונטיינר (לא מוחק volumes)"
	@echo "  make logs-<service>    -- צפייה בלוגים של קונטיינר"
	@echo "  make update            -- עדכון כל הפרויקט מגיט"
	@echo "  make clean             -- ניקוי אימג'ים שלא בהרצה"
	@echo ""
up:
	$(MAKE) update
	$(MAKE) up-trader
	$(MAKE) up-n8n
	$(MAKE) up-nginx
	@echo ""
	@echo "שירותים הורמו בהצלחה!"
	@echo "כתובות גישה:"
	@echo "Trader:    https://localhost:8744/  (Proxy ל-trader:7070)"
	@echo "n8n:       https://localhost:8744/n8n/  (Proxy ל-n8n:5678)"
	@echo "Nginx SSL: https://localhost:8744/  (443)"
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

up-nginx:
	openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout nginx/ssl/privkey.pem -out nginx/ssl/fullchain.pem -subj "/CN=localhost" -addext "subjectAltName=DNS:localhost,DNS:aboglion.top"
	docker compose build nginx
	docker compose up -d nginx

down-nginx:
	docker compose stop nginx
	docker compose rm -f nginx

logs-nginx:
	docker logs -f $$(docker ps --filter "name=nginx" -q)

update:
	git reset --hard HEAD
	git pull origin main

clean:
	docker image prune -f
clean-all:
	docker stop $(docker ps -aq) && docker rm -f $(docker ps -a -aq) && docker rmi -f $(docker images -q)  
format:
	docker rm -f $(docker ps -aq) && docker rmi -f $(docker images -q)  
	docker volume rm -f $(docker volume ls -q)