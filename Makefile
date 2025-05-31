# ------------------------------------------------------------------
# Makefile for Grylli Project
# ------------------------------------------------------------------

# Variables
.grylli_DIR = .grylli
PYTHON = $(.grylli_DIR)/bin/python3
PIP = $(.grylli_DIR)/bin/pip
NPM = npm

.PHONY: help
help:  ## Show this help message
	@echo "Available make targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-35s\033[0m %s\n", $$1, $$2}' | sort

# --- Translation targets ---
.PHONY: translate_pre
translate_pre: ## Extract and prepare messages.pot and .po files
	python3 -m app.pre_translations

.PHONY: translate_all
translate_all: ## Translate all supported languages with GPT
	tools/translate_all.sh

.PHONY: translate_post
translate_post: ## Clean and compile translated .po files
	python3 -m app.post_translations

# --- Local dev use ---
.PHONY: dev_git_commit_push
dev_git_commit_push: ## Add, commit, and push the latest changes
	@echo "Adding all changes, committing, and pushing to Git..."
	git add .
	git commit -m "latest updates"
	git push

.PHONY: dev_git_commit_rebase_remote_git
dev_git_commit_rebase_remote_git: ## Rebase baseline remote git repo
	@echo "Rebaselining Git repo"
	git push origin main --force

.PHONY: dev_format
dev_format: ## Normalize line endings and run isort, black, and djlint on app/ and tools/
	@echo "Normalizing line endings..."
	find . -type f \( -iname "*.py" -o -iname "*.html" -o -iname "*.css" -o -iname "*.js" -o -iname "*.txt" -o -iname "*.po" -o -iname "*.json" -o -iname "*.yml" -o -iname "*.cfg" \) \
		-not -path "*/__pycache__/*" \
		-not -path "*/node_modules/*" \
		-not -path "*/.venv/*" \
		-not -path "*/.grylli/*" \
		-not -path "*/venv/*" \
		-exec dos2unix {} +
	@echo "Running isort on app/ and tools/..."
	isort app/ tools/
	@echo "Running black on app/ and tools/..."
	black app/ tools/
	@echo "Running djlint on app/templates/..."
	djlint app/templates/ --reformat
	@echo "Formatting complete."

.PHONY: dev_build_versionsjson
dev_build_versionsjson:  ## Generate version.json locally
	node scripts/generate_versions.js

.PHONY: dev_docker_buildx
dev_docker_buildx: dev_build_versionsjson  ## Build and push multi-arch Docker image to GHCR
	docker buildx build \
		--provenance=false \
		--platform linux/amd64,linux/arm64 \
		--tag ghcr.io/samcro1967/grylli:latest \
		--tag ghcr.io/samcro1967/grylli:v1.0.0 \
		--label org.opencontainers.image.source=https://github.com/samcro1967/grylli \
		--push \
		.

.PHONY: dev_db_dump
dev_db_dump:
	@echo "Dumping database to JSON in data/ ..."
	python3 tools/dump_db_to_json.py

.PHONY: dev_upgrade_db
dev_upgrade_db: ## Generate and apply DB migration (pass MSG="desc" or enter it when prompted)
	@echo "Generating and applying database migration..."
	@if [ -z "$(MSG)" ]; then \
		read -p "Enter migration message: " MSG; \
		flask db migrate -m "$$MSG"; \
	else \
		flask db migrate -m "$(MSG)"; \
	fi
	@flask db upgrade

.PHONY: dev_css_dev
dev_css_dev: ## Compile Tailwind CSS assets and watch
	@echo "Compiling Tailwind CSS..."
	npm run dev:css

.PHONY: dev_css_build
dev_css_build: ## Compile Tailwind CSS assets
	@echo "Compiling Tailwind CSS..."
	npm run build:css

.PHONY: dev_pip_updates_available
dev_pip_updates_available: ## List installed pip packages that are out of date
	@echo "Installed pip packages that are out of date...."
	@pip list --outdated

.PHONY: dev_display_fixable_vulnerabilities
dev_display_fixable_vulnerabilities: ## Display fixable container vulnerabilities
	@echo "Displaying fixable vulnerabilities...."
	@../grype/grype ghcr.io/samcro1967/grylli:latest --scope all-layers --only-fixed

# --- Setting up local dev env helpers---
.PHONY: env_setup_env_setup_install_deps
env_setup_install_deps: ## Install Python dependencies
	@echo "Installing Python dependencies..."
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

.PHONY: env_setup_install_node_deps
env_setup_install_node_deps: ## Install Node dependencies
	@echo "Installing Node dependencies..."
	$(NPM) install

.PHONY: env_setup_tailwind_init
env_setup_tailwind_init: ## Initialize Tailwind CSS and postcss config
	npm install -D tailwindcss@npm:tailwindcss@3.4.1 postcss@latest autoprefixer@latest
	npx tailwindcss init -p
	npx update-browserslist-db@latest

.PHONY: env_setup_build_css
env_setup_build_css: ## Compile Tailwind CSS assets
	@echo "Compiling Tailwind CSS..."
	npm run build:css

.PHONY: env_setup_init_db
env_setup_init_db: ## Initialize Flask DB
	@echo "Initializing the Flask database..."
	flask db init
	flask db migrate -m "Initial"
	flask db upgrade

.PHONY: grylli_env_setup
grylli_env_setup: env_setup_install_deps env_setup_install_node_deps env_setup_tailwind_init env_setup_build_css ## Development and Build Steps

# --- Removing local dev env helpers---
.PHONY: env_remove_clean_cache
env_remove_clean_cache: ## Clean up Grylli cache and build artifacts
	@echo "🧹 Cleaning up Python and Node.js cache directories..."
	find . -type d \( \
		-name '__pycache__' -o \
		-name 'node_modules' -o \
		-name '.cache' \
	\) -exec rm -rf {} +
	@echo "🗑️ Removing Python bytecode files..."
	find . -type f -name '*.py[co]' -delete

.PHONY: env_remove_.grylli
env_remove_.grylli: ## Remove the virtual environment
	@echo "Removing virtual environment..."
	rm -rf $(.grylli_DIR)

.PHONY: env_remove_reset_db
env_remove_reset_db: ## Remove and recreate the database and migrations
	@echo "🔥 Resetting the database and migrations..."
	rm -rf migrations/
	rm -f data/grylli.db

.PHONY:  grylli_env_removal
grylli_env_removal: env_remove_clean_cache env_remove_.grylli env_remove_reset_db ## Full clean build
