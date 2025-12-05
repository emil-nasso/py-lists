.PHONY: sync run lint type-check check format docker-build docker-run

sync:
	uv sync

run:
	uv run fastapi dev app/main.py

lint:
	uv run ruff check --fix app/

format:
	uv run ruff format app/

type-check:
	uv run pyright app/

check: lint type-check

docker-build:
	docker build -t py-lists .

docker-run:
	docker run --name py-lists --rm -p 8000:8000 py-lists
