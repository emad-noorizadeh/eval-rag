# RAG System Tests

This directory contains all test files for the RAG system components.

## Test Files

- `test_database_config.py` - Tests for DatabaseConfig class
- `test_index_builder.py` - Tests for IndexBuilder class
- `run_tests.py` - Test runner script

## Running Tests

### Run All Tests
```bash
cd backend
python tests/run_tests.py
```

### Run Specific Test
```bash
# Run database config tests
python tests/run_tests.py database

# Run index builder tests
python tests/run_tests.py index
```

### Run Individual Test Files
```bash
# Run database config tests
python tests/test_database_config.py

# Run index builder tests
python tests/test_index_builder.py
```

## Test Structure

Each test file follows this pattern:
1. **Setup** - Initialize components
2. **Test** - Run specific functionality
3. **Verify** - Check results
4. **Cleanup** - Clean up resources

## Prerequisites

- Set `OPENAI_API_KEY` environment variable
- Ensure virtual environment is activated
- Have test data in `./data` folder (for index builder tests)

## Test Data

The index builder tests expect text files in the `./data` folder. Create this folder and add `.txt` files for testing.

## Author

Emad Noorizadeh
