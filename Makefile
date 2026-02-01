.PHONY: all build clean install rpm test

# Variables
APP_NAME := super-palm-tree
VERSION := 1.0.0
BUILD_DIR := build
DIST_DIR := dist
SRC_DIR := src

# Default target
all: build

# Build standalone executable
build:
	@echo "Building $(APP_NAME)..."
	mkdir -p $(DIST_DIR)
	cd $(SRC_DIR) && pyinstaller --onefile --name $(APP_NAME) --distpath ../$(DIST_DIR) main.py
	@echo "✓ Built: $(DIST_DIR)/$(APP_NAME)"

# Build for current platform
build-linux: build
	mv $(DIST_DIR)/$(APP_NAME) $(DIST_DIR)/$(APP_NAME)-linux-x64

build-windows:
	mkdir -p $(DIST_DIR)
	cd $(SRC_DIR) && pyinstaller --onefile --name $(APP_NAME) --distpath ../$(DIST_DIR) main.py
	mv $(DIST_DIR)/$(APP_NAME).exe $(DIST_DIR)/$(APP_NAME)-windows-x64.exe

build-macos:
	mkdir -p $(DIST_DIR)
	cd $(SRC_DIR) && pyinstaller --onefile --name $(APP_NAME) --distpath ../$(DIST_DIR) main.py
	mv $(DIST_DIR)/$(APP_NAME) $(DIST_DIR)/$(APP_NAME)-macos-x64

# Build RPM package (Fedora/RHEL/CentOS)
rpm: build-linux
	@echo "Building RPM package..."
	mkdir -p ~/rpmbuild/{BUILD,RPMS,SOURCES,SPECS,SRPMS}
	cp $(DIST_DIR)/$(APP_NAME)-linux-x64 ~/rpmbuild/SOURCES/superpalmtree
	cp packaging/rpm/superpalmtree.spec ~/rpmbuild/SPECS/
	rpmbuild -bb ~/rpmbuild/SPECS/superpalmtree.spec \
		--define "version $(VERSION)" \
		--define "github_user YOUR_USERNAME"
	cp ~/rpmbuild/RPMS/x86_64/superpalmtree-*.rpm $(DIST_DIR)/
	@echo "✓ RPM built: $(DIST_DIR)/superpalmtree-$(VERSION)-1.x86_64.rpm"

# Install locally
install:
	@echo "Installing $(APP_NAME)..."
	cp $(DIST_DIR)/$(APP_NAME) /usr/local/bin/
	chmod +x /usr/local/bin/$(APP_NAME)
	@echo "✓ Installed to /usr/local/bin/$(APP_NAME)"

# Uninstall
uninstall:
	rm -f /usr/local/bin/$(APP_NAME)
	@echo "✓ Uninstalled $(APP_NAME)"

# Run tests
test:
	cd $(SRC_DIR) && python -m pytest ../tests/ -v

# Clean build artifacts
clean:
	rm -rf $(BUILD_DIR) $(DIST_DIR)
	rm -rf $(SRC_DIR)/build $(SRC_DIR)/dist $(SRC_DIR)/*.spec
	rm -rf __pycache__ $(SRC_DIR)/__pycache__
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "✓ Cleaned build artifacts"

# Development setup
dev-setup:
	pip install -r requirements.txt
	pip install pyinstaller pytest flake8 black
	@echo "✓ Development environment ready"

# Format code
format:
	black $(SRC_DIR)
	@echo "✓ Code formatted"

# Lint
lint:
	flake8 $(SRC_DIR)
	@echo "✓ Linting complete"

# Help
help:
	@echo "AgentSmith Makefile targets:"
	@echo "  make build        - Build standalone executable"
	@echo "  make rpm          - Build RPM package (Linux)"
	@echo "  make install      - Install to /usr/local/bin"
	@echo "  make uninstall    - Remove from /usr/local/bin"
	@echo "  make test         - Run tests"
	@echo "  make clean        - Clean build artifacts"
	@echo "  make dev-setup    - Setup development environment"
	@echo "  make format       - Format code with black"
	@echo "  make lint         - Lint code with flake8"
