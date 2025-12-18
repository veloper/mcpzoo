.PHONY: help setup backend-run frontend-run frontend-build dev test clean docker-build docker-dev docker-prod docker-stop docker-logs docker-dev-shell docker-dev-cmd

BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m

help:
	@echo "$(BLUE)MCPZoo Commands$(NC)"
	@echo ""
	@echo "$(GREEN)Setup$(NC)"
	@echo "  make setup              Install all dependencies"
	@echo ""
	@echo "$(GREEN)Testing$(NC)"
	@echo "  make test               Run all tests"
	@echo ""
	@echo "$(GREEN)Docker Development$(NC)"
	@echo "  make docker-build       Build Docker image"
	@echo "  make docker-dev         Run container (development)"
	@echo "  make docker-dev-shell   Open shell in dev container"
	@echo "  make docker-dev-cmd CMD=... Run command in dev container"
	@echo "  make docker-dev-stop    Stop development container"
	@echo "  make docker-dev-logs    View development logs"
	@echo ""
	@echo "$(GREEN)Docker Production$(NC)"
	@echo "  make docker-prod        Run container (production)"
	@echo "  make docker-prod-stop   Stop production container"
	@echo "  make docker-prod-logs   View production logs"
	@echo ""
	@echo "$(GREEN)Cleanup$(NC)"
	@echo "  make clean              Remove build artifacts"
	@echo ""

setup:
	@echo "$(BLUE)Setting up development environment...$(NC)"
	cd backend && uv sync
	cd frontend && npm install
	@echo "$(GREEN)✓ Setup complete$(NC)"

dev:
	@echo "$(BLUE)Starting development setup...$(NC)"
	@echo "$(YELLOW)Step 1: Building frontend...$(NC)"
	cd frontend && npm run build
	@echo "$(GREEN)✓ Frontend built$(NC)"
	@echo ""
	@echo "$(YELLOW)Step 2: Starting Docker container with backend...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✓ Docker container running$(NC)"
	@echo "$(YELLOW)  Backend API: https://localhost:8000/api$(NC)"
	@echo ""
	@echo "$(YELLOW)Step 3: Starting local Vite dev server...$(NC)"
	@echo "$(YELLOW)  Open: http://localhost:5173$(NC)"
	@echo "$(YELLOW)  Hot reload enabled - edit files and see changes instantly$(NC)"
	@echo ""
	cd frontend && npm run dev

backend-run:
	@echo "$(BLUE)Starting backend dev server...$(NC)"
	cd backend && uv run python -m uvicorn src.backend.main:app --host 127.0.0.1 --port 8001 --reload

frontend-run:
	@echo "$(BLUE)Starting frontend dev server...$(NC)"
	cd frontend && npm run dev

frontend-build:
	@echo "$(BLUE)Building frontend...$(NC)"
	cd frontend && npm run build
	@echo "$(GREEN)✓ Frontend built to frontend/dist/$(NC)"

test:
	@echo "$(BLUE)Running tests...$(NC)"
	cd backend && uv run pytest tests/ -v

clean:
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	find backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find backend -name "*.pyc" -delete 2>/dev/null || true
	rm -rf frontend/dist 2>/dev/null || true
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

docker-build: frontend-build
	@echo "$(BLUE)Building Docker image...$(NC)"
	docker build -t mcpzoo:latest .
	@echo "$(GREEN)✓ Image built$(NC)"

docker-dev: docker-build
	@echo "$(BLUE)Starting Docker container (development)...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✓ Container running in development mode$(NC)"
	@echo "$(YELLOW)Frontend available at: https://localhost$(NC)"
	@echo "$(YELLOW)API available at: https://localhost/api$(NC)"
	@echo "$(YELLOW)Run 'make docker-dev-shell' to access the container$(NC)"

docker-dev-shell:
	@echo "$(BLUE)Opening shell in development container...$(NC)"
	docker-compose exec mcpzoo-dev bash

docker-dev-cmd:
	@echo "$(BLUE)Running command in development container...$(NC)"
	@docker-compose exec mcpzoo-dev $(CMD)

docker-dev-stop:
	@echo "$(BLUE)Stopping development container...$(NC)"
	docker-compose down
	@echo "$(GREEN)✓ Development container stopped$(NC)"

docker-dev-logs:
	@echo "$(BLUE)Viewing development container logs...$(NC)"
	docker-compose logs -f

docker-prod: docker-build
	@echo "$(BLUE)Starting Docker container (production)...$(NC)"
	docker-compose -f docker-compose.yml up -d
	@echo "$(GREEN)✓ Container running in production mode$(NC)"
	@echo "$(YELLOW)Available at: https://localhost$(NC)"

docker-prod-stop:
	@echo "$(BLUE)Stopping production container...$(NC)"
	docker-compose -f docker-compose.yml down
	@echo "$(GREEN)✓ Production container stopped$(NC)"

docker-prod-logs:
	@echo "$(BLUE)Viewing production container logs...$(NC)"
	docker-compose -f docker-compose.yml logs -f
