"""Tests for the command executor and validator."""

import pytest
from guiderails.parser import CodeBlock
from guiderails.executor import Executor, Validator, ExecutionResult


def test_execute_simple_command():
    """Test executing a simple command."""
    executor = Executor()
    code_block = CodeBlock(code="echo 'hello'", language="bash")

    result = executor.execute_code_block(code_block)

    assert result.success is True
    assert result.exit_code == 0
    assert "hello" in result.stdout


def test_execute_failing_command():
    """Test executing a failing command."""
    executor = Executor()
    code_block = CodeBlock(code="exit 1", language="bash")

    result = executor.execute_code_block(code_block)

    assert result.success is False
    assert result.exit_code == 1


def test_validate_exit_code_success():
    """Test validating exit code - success case."""
    validator = Validator()
    result = ExecutionResult(success=True, exit_code=0, stdout="", stderr="")
    code_block = CodeBlock(code="", mode="exit", expected="0")

    success, message = validator.validate(result, code_block)

    assert success is True
    assert "matched" in message.lower()


def test_validate_exit_code_failure():
    """Test validating exit code - failure case."""
    validator = Validator()
    result = ExecutionResult(success=False, exit_code=1, stdout="", stderr="")
    code_block = CodeBlock(code="", mode="exit", expected="0")

    success, message = validator.validate(result, code_block)

    assert success is False
    assert "1 != expected 0" in message


def test_validate_contains_success():
    """Test validating contains mode - success case."""
    validator = Validator()
    result = ExecutionResult(success=True, exit_code=0, stdout="hello world", stderr="")
    code_block = CodeBlock(code="", mode="contains", expected="world")

    success, message = validator.validate(result, code_block)

    assert success is True
    assert "contains" in message.lower()


def test_validate_contains_failure():
    """Test validating contains mode - failure case."""
    validator = Validator()
    result = ExecutionResult(success=True, exit_code=0, stdout="hello", stderr="")
    code_block = CodeBlock(code="", mode="contains", expected="world")

    success, message = validator.validate(result, code_block)

    assert success is False
    assert "does not contain" in message.lower()


def test_validate_regex_success():
    """Test validating regex mode - success case."""
    validator = Validator()
    result = ExecutionResult(success=True, exit_code=0, stdout="hello world 123", stderr="")
    code_block = CodeBlock(code="", mode="regex", expected=r"\d+")

    success, message = validator.validate(result, code_block)

    assert success is True
    assert "matches regex" in message.lower()


def test_validate_regex_failure():
    """Test validating regex mode - failure case."""
    validator = Validator()
    result = ExecutionResult(success=True, exit_code=0, stdout="hello world", stderr="")
    code_block = CodeBlock(code="", mode="regex", expected=r"\d+")

    success, message = validator.validate(result, code_block)

    assert success is False
    assert "does not match" in message.lower()


def test_validate_exact_success():
    """Test validating exact mode - success case."""
    validator = Validator()
    result = ExecutionResult(success=True, exit_code=0, stdout="hello", stderr="")
    code_block = CodeBlock(code="", mode="exact", expected="hello")

    success, message = validator.validate(result, code_block)

    assert success is True


def test_validate_exact_failure():
    """Test validating exact mode - failure case."""
    validator = Validator()
    result = ExecutionResult(success=True, exit_code=0, stdout="hello world", stderr="")
    code_block = CodeBlock(code="", mode="exact", expected="hello")

    success, message = validator.validate(result, code_block)

    assert success is False


def test_execute_with_timeout():
    """Test that timeout works."""
    executor = Executor()
    code_block = CodeBlock(code="sleep 10", language="bash", timeout=1)

    result = executor.execute_code_block(code_block)

    assert result.success is False
    assert result.error_message is not None
    assert "timed out" in result.error_message.lower()


def test_execute_with_working_dir(tmp_path):
    """Test executing with a specific working directory."""
    # Create a test directory
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    executor = Executor(base_working_dir=str(tmp_path))
    code_block = CodeBlock(code="pwd", language="bash", working_dir="test")

    result = executor.execute_code_block(code_block)

    assert result.success is True
    assert str(test_dir) in result.stdout


def test_execute_with_nonexistent_working_dir():
    """Test executing with a non-existent working directory."""
    executor = Executor()
    code_block = CodeBlock(code="pwd", language="bash", working_dir="/nonexistent/directory")

    result = executor.execute_code_block(code_block)

    assert result.success is False
    assert result.error_message is not None
    assert "does not exist" in result.error_message.lower()


def test_execute_and_validate():
    """Test the combined execute and validate method."""
    executor = Executor()
    code_block = CodeBlock(code="echo 'test'", language="bash", mode="contains", expected="test")

    result, validation_success, validation_message = executor.execute_and_validate(code_block)

    assert result.success is True
    assert validation_success is True
    assert "contains" in validation_message.lower()


def test_validate_checks_stderr():
    """Test that validator checks both stdout and stderr."""
    validator = Validator()
    result = ExecutionResult(success=False, exit_code=1, stdout="", stderr="error: file not found")
    code_block = CodeBlock(code="", mode="contains", expected="error")

    success, message = validator.validate(result, code_block)

    assert success is True


def test_validate_unknown_mode():
    """Test that unknown validation mode returns error."""
    validator = Validator()
    result = ExecutionResult(success=True, exit_code=0, stdout="test", stderr="")
    code_block = CodeBlock(code="", mode="unknown", expected="test")

    success, message = validator.validate(result, code_block)

    assert success is False
    assert "unknown" in message.lower()
