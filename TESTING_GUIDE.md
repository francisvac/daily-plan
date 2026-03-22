# ZeroClaw Baby Planner - Testing Guide

## Overview

This comprehensive testing system ensures the reliability and accuracy of the ZeroClaw Baby Planner, with special focus on feedback processing and memory system functionality.

## Testing Architecture

### Test Structure
```
tests/
├── unit/                    # Component-level tests
│   ├── test_memory_manager.py
│   ├── test_patterns_manager.py
│   └── test_email_command_processor.py
├── integration/             # Workflow tests
│   ├── test_feedback_pipeline.py
│   └── test_memory_patterns.py
├── end_to_end/            # Full scenario tests
│   ├── test_daily_workflow.py
│   └── test_learning_cycle.py
└── fixtures/              # Test data
    ├── sample_plans/
    ├── mock_emails/
    └── test_patterns.json
```

### Test Categories

#### Unit Tests
- **MemoryManager**: Memory storage, retrieval, and persistence
- **PatternsManager**: Baby pattern management and learning
- **EmailCommandProcessor**: Email command parsing and execution

#### Integration Tests
- **Feedback Pipeline**: Complete feedback processing workflow
- **Memory Patterns**: Memory-to-patterns learning integration

#### End-to-End Tests
- **Daily Workflow**: Complete daily user workflows
- **Learning Cycle**: Feedback-to-learning-to-improvement cycles

## Running Tests

### Quick Start
```bash
# Run all tests
make test

# Run specific test categories
make test-unit          # Unit tests only
make test-integration   # Integration tests only
make test-e2e          # End-to-end tests only

# Run tests with coverage
make test-coverage
```

### Advanced Testing
```bash
# Run specific component tests
make test-feedback      # Feedback processing tests
make test-memory        # Memory management tests
make test-email         # Email integration tests

# Run tests in watch mode (for development)
make test-watch

# Run only failed tests
make test-failed

# Run performance tests
make test-performance
```

## Key Testing Areas

### 1. Memory System Testing

**Critical Tests:**
- Memory storage and retrieval accuracy
- JSON file persistence and corruption handling
- Memory cleanup and aging
- Search functionality performance
- Concurrent access safety

**Example Test:**
```python
def test_memory_storage_and_retrieval(memory_manager):
    # Test adding and retrieving memory entries
    key = "test_entry"
    entry = {"feedback": {"what_enjoyed": ["tummy_time"]}}
    
    # Add entry
    result = memory_manager.add_entry(key, entry)
    assert result is True
    
    # Retrieve entry
    retrieved = memory_manager.get_entry(key)
    assert retrieved is not None
    assert retrieved["feedback"] == entry["feedback"]
```

### 2. Feedback Processing Testing

**Critical Tests:**
- Email command parsing accuracy
- Feedback categorization (enjoyed/disliked)
- Memory integration from feedback
- Pattern learning validation
- Error handling for malformed feedback

**Example Test:**
```python
def test_feedback_categorization(processor_with_mocks, memory_manager):
    # Test feedback categorization logic
    feedback_samples = [
        ("Baby loved tummy time", "enjoyed"),
        ("Baby disliked loud noises", "disliked"),
        ("Baby had good feeding", "feeding")
    ]
    
    for feedback_text, expected_category in feedback_samples:
        command = {"command": "feedback", "args": feedback_text}
        result = processor_with_mocks._execute_command(command)
        
        # Verify categorization
        assert result is not None
```

### 3. Pattern Learning Testing

**Critical Tests:**
- Pattern extraction from feedback
- Developmental stage progression
- Activity preference learning
- Sleep/feeding schedule optimization
- Pattern accuracy over time

**Example Test:**
```python
def test_pattern_learning_from_feedback(memory_manager, patterns_manager):
    # Add multiple feedback entries
    for i in range(3):
        memory_manager.add_entry(f'feedback_{i}', {
            'feedback': {'what_enjoyed': ['tummy time']}
        })
    
    # Extract patterns
    summary = memory_manager.get_summary()
    themes = summary['feedback_themes']
    
    # Verify learning
    assert 'tummy time' in themes['enjoyed']
    assert themes['enjoyed']['tummy time'] >= 3
```

## Test Data and Fixtures

### Sample Data
- **Sample Plans**: Realistic baby development plans
- **Mock Emails**: Various feedback formats and edge cases
- **Test Patterns**: Different developmental stages and preferences

### Test Fixtures
```python
@pytest.fixture
def memory_manager(mock_memory_file):
    """Create MemoryManager instance with test configuration"""
    manager = MemoryManager()
    manager._memory_cache = {}
    yield manager

@pytest.fixture
def sample_feedback_emails():
    """Sample feedback emails for testing"""
    return [
        {
            'subject': 'Baby Feedback',
            'body': 'feedback Baby loved tummy time'
        }
    ]
```

## Verification Metrics

### Coverage Goals
- **Unit Tests**: 90%+ code coverage
- **Integration Tests**: 80%+ workflow coverage
- **Critical Paths**: 100% coverage for feedback/memory pipeline

### Quality Metrics
- **Test Reliability**: All tests pass consistently
- **Performance**: Tests complete within reasonable time
- **Maintainability**: Clear, documented test cases

## Continuous Integration

### Pre-commit Hooks
```bash
# Run quick tests before commits
make quick-test

# Run unit tests and linting
make dev-test
```

### CI Pipeline
```bash
# Full CI test suite
make test-ci

# Generate test reports
make test-report
```

## Testing Best Practices

### 1. Test Organization
- Group related tests in classes
- Use descriptive test names
- Follow Arrange-Act-Assert pattern

### 2. Mock Usage
- Mock external services (email, file system)
- Use realistic test data
- Avoid over-mocking

### 3. Test Data Management
- Use fixtures for reusable test data
- Clean up test artifacts
- Isolate test environments

### 4. Error Testing
- Test error conditions and edge cases
- Verify graceful error handling
- Test recovery scenarios

## Debugging Tests

### Common Issues
1. **Import Errors**: Ensure PYTHONPATH includes project root
2. **Mock Failures**: Check mock configuration and call expectations
3. **Fixture Issues**: Verify fixture setup and teardown

### Debugging Commands
```bash
# Run with verbose output
pytest tests/ -v -s

# Run specific test with debugging
pytest tests/unit/test_memory_manager.py::TestMemoryManager::test_memory_manager_initialization -v -s

# Stop on first failure
pytest tests/ -x

# Show local variables on failure
pytest tests/ --tb=long
```

## Performance Testing

### Memory Performance
```bash
# Test with large datasets
make test-performance

# Test memory search performance
python3 -m pytest tests/ -k "search" --benchmark-only
```

### Email Processing Performance
```bash
# Test email processing throughput
python3 -m pytest tests/ -k "email" --benchmark-only
```

## Security Testing

### Security Checks
```bash
# Run security tests
make test-security

# Check for vulnerabilities
bandit -r daily_plans/
safety check
```

## Documentation Testing

### Docstring Tests
```bash
# Run doctests
make test-docs

# Test documentation examples
python3 -m doctest daily_plans/*.py
```

## Troubleshooting

### Test Failures
1. **Check Test Output**: Look for specific error messages
2. **Verify Environment**: Ensure test dependencies are installed
3. **Check Mocks**: Verify mock configuration matches actual usage
4. **Test Data**: Ensure test data is valid and consistent

### Common Solutions
- Update test fixtures if system changes
- Adjust mock expectations for new functionality
- Clean test environment between runs
- Verify test isolation

## Contributing Tests

### Adding New Tests
1. Follow existing test patterns
2. Use appropriate fixtures
3. Add comprehensive coverage
4. Document test scenarios

### Test Review Checklist
- [ ] Test covers happy path
- [ ] Test covers error conditions
- [ ] Test uses appropriate mocks
- [ ] Test is isolated and repeatable
- [ ] Test has clear documentation

This testing system provides comprehensive verification of the ZeroClaw Baby Planner's functionality, ensuring reliable feedback processing and memory system operation.
