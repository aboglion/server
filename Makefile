.DEFAULT_GOAL := help

help:
	@echo ""
	@echo "שימוש ב-Makefile:"
	@echo "  make up-<service>      -- בניה והרמה של קונטיינר (trader, n8n, nginx)"
	@echo "  make down-<service>    -- עצירה ומחיקה של קונטיינר (לא מוחק volumes)"
	@echo "  make logs-<service>    -- צפייה בלוגים של קונטיינר"
	@echo "  make update            -- עדכון כל הפרויקט מגיט"
	@echo ""

up-trader:
	docker compose build trader
	docker compose up -d trader

down-trader:
	docker compose stop trader
	docker compose rm -f trader

logs-trader:
	docker logs -f $$(docker ps --filter "name=trader" -q)

up-n8n:
	docker compose build n8n
	docker compose up -d n8n

down-n8n:
	docker compose stop n8n
	docker compose rm -f n8n

logs-n8n:
	docker logs -f $$(docker ps --filter "name=n8n" -q)

up-nginx:
	docker compose build nginx
	docker compose up -d nginx

down-nginx:
	docker compose stop nginx
	docker compose rm -f nginx

logs-nginx:
	docker logs -f $$(docker ps --filter "name=nginx" -q)

update:
	git pull
