.PHONY: help install run migrate upgrade clean

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

install:  ## Install dependencies
	pip install -r requirements/requirements.txt

run:  ## Run the application
	python entrypoint.py

migrate:  ## Create migration
	@read -p "Migration message: " msg; \
	alembic revision --autogenerate -m "$$msg"

upgrade:  ## Apply migrations
	alembic upgrade head

clean:  ## Clean cache files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
