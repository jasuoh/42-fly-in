install:
	@uv sync

run:
	@uv run python -m src

debug:
	@uv run python -m pdb -m src

clean:
	@find . -type d -name __pycache__ -prune -exec rm -rf {} \;
	@find . -type d -name .mypy_cache -prune -exec rm -rf {} \;

fclean: clean
	@rm -rf .venv

lint:
	@uv run flake8 src
	@uv run mypy src

lint-strict:
	@uv run flake8 src
	@uv run mypy src --strict

.PHONY: install run debug clean fclean lint lint-strict