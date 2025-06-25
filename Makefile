.PHONY: install setup-db-local run test lint format activate_venv

install:
	pip install -r requirements.txt

setup-db-local:
	python3 src/database/connection.py

run:
	flask run -h 0.0.0.0 -p 5000

test:
	# Placeholder for running tests (e.g., pytest)
	echo "Running tests..."
	# python -m pytest tests/

lint:
	# Placeholder for linting (e.g., pylint)
	echo "Running linting..."
	# pylint src/

format:
	# Placeholder for formatting (e.g., black)
	echo "Running formatting..."
	# black src/

activate_venv:
	@echo "Activating virtual environment..."
	@source .venv/bin/activate