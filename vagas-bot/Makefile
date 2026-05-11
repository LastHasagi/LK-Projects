.PHONY: up down logs migrate test fmt lint shell eval

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f

migrate:
	docker compose exec bot alembic upgrade head

test:
	pytest -v

fmt:
	ruff format app tests

lint:
	ruff check app tests

shell:
	docker compose exec bot python

eval:
	python -m eval.run_matching_eval
