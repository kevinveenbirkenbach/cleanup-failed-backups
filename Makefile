# Makefile for Cleanup Failed Backups

.PHONY: test install help

help:
	@echo "Available targets:"
	@echo "  make test     - Run unit tests"
	@echo "  make install  - Show installation instructions"

test:
	@echo ">> Running tests"
	@python3 -m unittest -v test.py

install:
	@echo ">> Installation instructions:"
	@echo "   This software can be installed with pkgmgr:"
	@echo "     pkgmgr install cleanback"
	@echo "   See project: https://github.com/kevinveenbirkenbach/package-manager"
