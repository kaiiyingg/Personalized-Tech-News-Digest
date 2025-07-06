SHELL := /bin/bash

VENV_PATH := ./.venv
VENV_PIP := $(VENV_PATH)/bin/pip
VENV_PYTHON := $(VENV_PATH)/bin/python
VENV_PYTHON3 := $(VENV_PATH)/bin/python3

.PHONY: install setup-db-local run test lint format activate_venv

install:
	$(VENV_PIP) install -r requirements.txt

setup-db-local:
	$(VENV_PYTHON3) src/database/connection.py

run:
	$(VENV_PYTHON) -m flask run -h 0.0.0.0 -p 5000

test:
	@echo "Running tests..."
	# $(VENV_PYTHON) -m pytest tests/

lint:
	@echo "Running linting..."
	# $(VENV_PYTHON) -m pylint src/

format:
	@echo "Running formatting..."
	# $(VENV_PYTHON) -m black src/

activate_venv:
	@echo "To activate manually, run:"
	@echo "source $(VENV_PATH)/bin/activate"
