# Makefile for Cleanup Failed Backups

.PHONY: install help test test-unit test-e2e

help:
	@echo "Available targets:"
	@echo "  make test     - Run unit tests"

test: test-unit test-e2e

test-unit:
	@echo ">> Running tests"
	@python3 -m unittest -v tests/unit/test_main.py

test-e2e:
	docker build -f tests/e2e/Dockerfile.e2e -t cleanback-e2e .
	docker run --rm cleanback-e2e
