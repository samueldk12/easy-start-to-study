.PHONY: start stop restart status logs test clean

start:
	docker compose up -d
	python tests/test_services.py

test:
	python tests/test_services.py

stop:
	docker compose down

pause:
	docker compose stop

resume:
	docker compose start

restart:
	docker compose restart

status:
	docker compose ps

logs:
	docker compose logs -f

clean:
	docker compose down -v
