# Tests for Azure Linux Base Image Recommender

This directory contains unit tests and integration tests for the secure container base image recommender.

## Test Structure

- `unit/` - Unit tests for individual modules
- `integration/` - Integration tests that test multiple components together
- `conftest.py` - Pytest configuration and fixtures
- `test_data/` - Test data files

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_database.py

# Run tests matching a pattern
pytest -k "test_recommendation"
```

## Test Categories

1. **Unit Tests**: Test individual functions and classes in isolation
2. **Integration Tests**: Test the interaction between components
3. **End-to-End Tests**: Test complete workflows
4. **Mock Tests**: Tests that mock external dependencies (Docker, Syft, etc.)
