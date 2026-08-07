install:
	uv sync

run:
	uv run python -m src

debug:
	uv run python -m src -m pdb

clean:
	rm -rf .venv
	rm -rf .uv-cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} \;
	find . -type d -name .mypy_cache -prune -exec rm -rf {} \;

lint:
	uv run flake8 .
	uv run mypy .

