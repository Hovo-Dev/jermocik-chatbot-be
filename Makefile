# Makefile for Django API Boilerplate

.PHONY: help dev prod logs clean down build migrate shell superuser

# Default target
help:
	@echo "Available commands:"
	@echo "  dev       - Start development environment"
	@echo "  prod      - Start production environment"
	@echo "  build     - Build Docker containers"
	@echo "  down      - Stop all services"
	@echo "  clean     - Stop and remove volumes"
	@echo "  migrate   - Run database migrations"
	@echo "  logs      - Show logs"
	@echo "  shell     - Open Django shell"
	@echo "  superuser - Create superuser"

# Production environment
prod:
	@echo "Starting production environment..."
	docker compose up --build -d

# Development environment
dev:
	@echo "Starting development environment..."
	docker compose -f docker-compose.dev.yml up --build

# Build Docker containers
build:
	docker compose -f docker-compose.dev.yml build

# Stop all services
down:
	docker compose -f docker-compose.dev.yml down

# Stop and remove volumes
clean:
	docker compose -f docker-compose.dev.yml down -v --remove-orphans

# Run database migrations
migrate:
	docker compose -f docker-compose.dev.yml exec web uv run python manage.py makemigrations
	docker compose -f docker-compose.dev.yml exec web uv run python manage.py migrate

# Show logs
logs:
	docker compose -f docker-compose.dev.yml logs -f

# Open Django shell
shell:
	docker compose -f docker-compose.dev.yml exec web uv run python manage.py shell

# Create superuser
superuser:
	docker compose -f docker-compose.dev.yml exec web uv run python manage.py createsuperuser

# Connect to database
db-shell:
	docker compose -f docker-compose.dev.yml exec db psql -U postgres -d django_api_db
