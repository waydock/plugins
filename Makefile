.PHONY: help venv test test-unit test-live

VENV := .venv
PY   := $(VENV)/bin/python

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-12s %s\n", $$1, $$2}'

$(PY): ## Create the virtualenv and install test deps
	python3 -m venv $(VENV)
	$(PY) -m pip install --quiet --upgrade pip pytest pyyaml

venv: $(PY) ## Set up the local test environment

test: test-unit ## Run the offline suite

test-unit: $(PY) ## Static validation of the plugin (manifests, frontmatter, structure)
	$(PY) -m pytest tests/unit -q

test-live: $(PY) ## Check skills against the live tool manifest (needs network)
	$(PY) -m pytest tests/live -q
