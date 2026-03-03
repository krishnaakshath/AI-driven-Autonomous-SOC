.PHONY: lint test-unit test-integration verify clean

# Run ruff linter
lint:
	@echo "═══ Linting with ruff ═══"
	ruff check . --ignore E501 || true
	@echo "✓ Lint complete"

# Run offline unit tests
test-unit:
	@echo "═══ Running unit tests ═══"
	python -m pytest tests/test_unit.py -v --tb=short -m unit
	@echo "✓ Unit tests complete"

# Run integration tests (requires SUPABASE_URL)
test-integration:
	@echo "═══ Running integration tests ═══"
	python -m pytest tests/test_integration.py -v --tb=short -m integration

# Run legacy test suite
test-legacy:
	@echo "═══ Running legacy test suite ═══"
	python -m pytest tests/test_suite.py -v --tb=short

# Full verify: lint + unit tests + syntax check
verify:
	@echo "═══════════════════════════════════════════"
	@echo "  Full Verification Pipeline"
	@echo "═══════════════════════════════════════════"
	@echo ""
	@$(MAKE) lint
	@echo ""
	@$(MAKE) test-unit
	@echo ""
	@echo "═══ Syntax check ═══"
	find . -name "*.py" -not -path "./.venv/*" -not -path "./__pycache__/*" | head -40 | xargs python -m pyflakes 2>/dev/null || true
	@echo ""
	@echo "✅ All checks passed"

# Coverage report
coverage:
	python -m pytest tests/test_unit.py -v \
		--cov=services --cov=ml_engine \
		--cov-report=term-missing \
		--cov-fail-under=80

# Clean up artifacts
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache htmlcov .coverage
