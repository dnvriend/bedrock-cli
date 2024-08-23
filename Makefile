.PHONY: help
.DEFAULT_GOAL := help

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

init: ## init pipenv
	pipenv --python 3.12

install: ## install dependencies
	pip install --upgrade -r requirements.txt

build: ## build locally
	./install.sh

dist: ## create distribution
	pip install --upgrade pip setuptools build
	python -m build

clean: ## clean
	rm -rf dist bedrock_cli/__pycache__ bedrock_cli.egg-info
