# The documentation of Beffroi. "make install" once, "make serve" to write, "make check" before a pull
# request. Every target runs in .venv, created from requirements.txt, with uv when it is installed.

VENV := .venv
BIN := $(VENV)/bin
UV := $(shell command -v uv 2>/dev/null)

.DEFAULT_GOAL := help
.PHONY: help install serve build check front-matter nav versions clean

help: ## Show this help
	@grep -E '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

$(BIN)/zensical: requirements.txt
ifdef UV
	uv venv --allow-existing $(VENV)
	VIRTUAL_ENV=$(VENV) uv pip install -r requirements.txt
else
	python3 -m venv $(VENV)
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -r requirements.txt
endif
	@touch $(BIN)/zensical

install: $(BIN)/zensical ## Install the toolchain in .venv

serve: install ## Serve the site on http://localhost:8000, rebuilt as you save
	$(BIN)/zensical serve

build: install ## Build the site into site/
	$(BIN)/zensical build

check: install front-matter nav ## Build strictly: a broken link, a missing anchor or a page outside the navigation fails
	$(BIN)/zensical build --strict

# The build stops at the first page whose front matter does not parse as YAML; this lists every one of them.
front-matter: install ## Check that the front matter of every page parses as YAML
	$(BIN)/python -I tools/front-matter.py docs

# Zensical checks links and anchors, not the navigation: this does, in both directions.
nav: install ## Check that every page is in the navigation and every entry of the navigation is a page
	$(BIN)/python -I tools/nav.py mkdocs.yml

versions: install ## List the versions published on gh-pages
	$(BIN)/mike list

clean: ## Remove the build, its cache and the virtual environment
	rm -rf site .cache $(VENV)
