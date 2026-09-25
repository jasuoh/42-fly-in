# **************************************************************************** #
#                                   FLY-IN                                     #
# **************************************************************************** #

NAME		:= fly-in
SRC			:= src
PYTHON		:= uv run python
MAP			?=
MAPS_DIR	:= maps

ifneq ($(MAP),)
	RUN_ARGS := --map $(MAP)
endif

# ---------------------------------------------------------------------------- #
#                                   Colors                                     #
# ---------------------------------------------------------------------------- #

RESET		:= \033[0m
BOLD		:= \033[1m
DIM			:= \033[2m
RED			:= \033[31m
GREEN		:= \033[32m
YELLOW		:= \033[33m
BLUE		:= \033[34m
MAGENTA		:= \033[35m
CYAN		:= \033[36m

# Logo gradient (256-color palette: cyan -> blue -> violet)
LOGO1		:= \033[1;38;5;51m
LOGO2		:= \033[1;38;5;45m
LOGO3		:= \033[1;38;5;39m
LOGO4		:= \033[1;38;5;63m
LOGO5		:= \033[1;38;5;99m
LOGO6		:= \033[1;38;5;135m

INFO		= printf "$(BOLD)$(BLUE)›$(RESET) %s\n"
OK			= printf "$(BOLD)$(GREEN)✔$(RESET) %s\n"

.DEFAULT_GOAL := help

# ---------------------------------------------------------------------------- #
##@ General
# ---------------------------------------------------------------------------- #

help: ## Show this help
	@printf '\n'
	@printf "$(LOGO1)%s$(RESET)\n" '  ███████╗██╗     ██╗   ██╗      ██╗███╗   ██╗'
	@printf "$(LOGO2)%s$(RESET)\n" '  ██╔════╝██║     ╚██╗ ██╔╝      ██║████╗  ██║'
	@printf "$(LOGO3)%s$(RESET)\n" '  █████╗  ██║      ╚████╔╝ █████╗██║██╔██╗ ██║'
	@printf "$(LOGO4)%s$(RESET)\n" '  ██╔══╝  ██║       ╚██╔╝  ╚════╝██║██║╚██╗██║'
	@printf "$(LOGO5)%s$(RESET)\n" '  ██║     ███████╗   ██║         ██║██║ ╚████║'
	@printf "$(LOGO6)%s$(RESET)\n" '  ╚═╝     ╚══════╝   ╚═╝         ╚═╝╚═╝  ╚═══╝'
	@printf "\n  $(DIM)✈  drone routing simulator · 42 project$(RESET)\n\n"
	@printf "$(BOLD)Usage:$(RESET) make $(CYAN)<target>$(RESET) [$(YELLOW)MAP=path/to/map.txt$(RESET)]\n"
	@awk 'BEGIN {FS = ":.*##"} \
		/^[a-zA-Z_-]+:.*?##/ { printf "  $(CYAN)%-14s$(RESET) %s\n", $$1, $$2 } \
		/^##@/ { printf "\n$(BOLD)$(MAGENTA)%s$(RESET)\n", substr($$0, 5) }' $(MAKEFILE_LIST)
	@printf "\n$(BOLD)Examples:$(RESET)\n"
	@printf "  make run $(DIM)# opens the interactive menu$(RESET)\n"
	@printf "  make run MAP=$(MAPS_DIR)/easy/01_linear_path.txt\n"

check-uv:
	@command -v uv >/dev/null 2>&1 || { \
		printf "$(BOLD)$(RED)✘$(RESET) uv not found — see https://docs.astral.sh/uv/\n"; \
		exit 1; }

# ---------------------------------------------------------------------------- #
##@ Setup
# ---------------------------------------------------------------------------- #

install: check-uv ## Create the venv and install dependencies
	@$(INFO) "Syncing dependencies..."
	@uv sync
	@$(OK) "Environment ready"

# ---------------------------------------------------------------------------- #
##@ Run
# ---------------------------------------------------------------------------- #

run: check-uv ## Start the simulation (optional MAP=...)
	@$(INFO) "Launching $(NAME)$(if $(MAP), with $(MAP),)"
	@$(PYTHON) -m $(SRC) $(RUN_ARGS) || true

debug: check-uv ## Run the simulation under pdb (optional MAP=...)
	@$(INFO) "Starting pdb session"
	@$(PYTHON) -m pdb -m $(SRC) $(RUN_ARGS) || true

maps: ## List all available maps
	@printf "$(BOLD)Available maps:$(RESET)\n"
	@find $(MAPS_DIR) -name '*.txt' | sort | while read -r f; do \
		dir=$$(dirname "$$f" | sed 's|^$(MAPS_DIR)/||'); \
		printf "  $(YELLOW)%-16s$(RESET) %s\n" "$$dir" "$$f"; \
	done

# ---------------------------------------------------------------------------- #
##@ Quality
# ---------------------------------------------------------------------------- #

lint: check-uv ## Run flake8 and mypy
	@$(INFO) "flake8"
	@uv run flake8 $(SRC)
	@$(INFO) "mypy"
	@uv run mypy $(SRC)
	@$(OK) "Lint passed"

lint-strict: check-uv ## Run flake8 and mypy --strict
	@$(INFO) "flake8"
	@uv run flake8 $(SRC)
	@$(INFO) "mypy --strict"
	@uv run mypy $(SRC) --strict
	@$(OK) "Strict lint passed"

# ---------------------------------------------------------------------------- #
##@ Cleanup
# ---------------------------------------------------------------------------- #

clean: ## Remove __pycache__ and .mypy_cache
	@find . -type d -name __pycache__ -prune -exec rm -rf {} +
	@find . -type d -name .mypy_cache -prune -exec rm -rf {} +
	@$(OK) "Caches removed"

fclean: clean ## clean + remove the virtual environment
	@rm -rf .venv
	@$(OK) "Virtual environment removed"

re: fclean install ## Rebuild the environment from scratch

.PHONY: help check-uv install run debug maps lint lint-strict clean fclean re
