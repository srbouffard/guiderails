"""Tests for the command executor and validator."""

from guiderails.executor import ExecutionResult, Executor, Validator
from guiderails.parser import CodeBlock


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


def test_variable_store():
    """Test variable store set/get/substitute."""
    from guiderails.executor import VariableStore

    store = VariableStore()
    store.set("NAME", "World")
    store.set("COUNT", "42")

    assert store.get("NAME") == "World"
    assert store.get("COUNT") == "42"
    assert store.get("MISSING") == ""

    text = "Hello ${NAME}, count is ${COUNT}"
    result = store.substitute(text)
    assert result == "Hello World, count is 42"


def test_variable_store_with_initial_vars():
    """Test variable store with initial variables."""
    from guiderails.executor import VariableStore

    store = VariableStore({"ENV": "prod", "PORT": "8080"})
    assert store.get("ENV") == "prod"
    assert store.get("PORT") == "8080"


def test_variable_substitution_no_match():
    """Test that substitution leaves unmatched variables unchanged."""
    from guiderails.executor import VariableStore

    store = VariableStore({"NAME": "Test"})
    text = "Hello ${NAME}, value is ${MISSING}"
    result = store.substitute(text)
    assert result == "Hello Test, value is ${MISSING}"


def test_path_sandbox_relative_path():
    """Test path sandbox validates relative paths."""
    import tempfile

    from guiderails.executor import PathSandbox

    with tempfile.TemporaryDirectory() as tmpdir:
        is_valid, resolved, error = PathSandbox.validate_path("test.txt", tmpdir, False)
        assert is_valid is True
        assert "test.txt" in resolved
        assert error == ""


def test_path_sandbox_rejects_absolute_path():
    """Test path sandbox rejects absolute paths by default."""
    import tempfile

    from guiderails.executor import PathSandbox

    with tempfile.TemporaryDirectory() as tmpdir:
        is_valid, resolved, error = PathSandbox.validate_path("/etc/passwd", tmpdir, False)
        assert is_valid is False
        assert "Absolute paths are not allowed" in error


def test_path_sandbox_allows_absolute_with_flag():
    """Test path sandbox allows absolute paths when flag is set."""
    import tempfile

    from guiderails.executor import PathSandbox

    with tempfile.TemporaryDirectory() as tmpdir:
        is_valid, resolved, error = PathSandbox.validate_path("/tmp/test.txt", tmpdir, True)
        assert is_valid is True


def test_path_sandbox_rejects_traversal():
    """Test path sandbox rejects path traversal."""
    import tempfile

    from guiderails.executor import PathSandbox

    with tempfile.TemporaryDirectory() as tmpdir:
        is_valid, resolved, error = PathSandbox.validate_path("../../../etc/passwd", tmpdir, False)
        assert is_valid is False
        assert "traversal" in error.lower()


def test_write_file_basic(tmp_path):
    """Test writing a file with FileBlock."""
    from guiderails.parser import FileBlock

    executor = Executor(base_working_dir=str(tmp_path))
    file_block = FileBlock(
        code="Hello, World!",
        path="test.txt",
        mode="write",
        executable=False,
    )

    success, message = executor.write_file(file_block)

    assert success is True
    assert "Wrote" in message

    # Verify file was created
    test_file = tmp_path / "test.txt"
    assert test_file.exists()
    assert test_file.read_text() == "Hello, World!\n"


def test_write_file_with_subdirectory(tmp_path):
    """Test writing a file in a subdirectory."""
    from guiderails.parser import FileBlock

    executor = Executor(base_working_dir=str(tmp_path))
    file_block = FileBlock(
        code="Content",
        path="subdir/file.txt",
        mode="write",
    )

    success, message = executor.write_file(file_block)

    assert success is True
    test_file = tmp_path / "subdir" / "file.txt"
    assert test_file.exists()
    assert test_file.read_text() == "Content\n"


def test_write_file_append_mode(tmp_path):
    """Test appending to a file."""
    from guiderails.parser import FileBlock

    # Create initial file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Line 1\n")

    executor = Executor(base_working_dir=str(tmp_path))
    file_block = FileBlock(
        code="Line 2",
        path="test.txt",
        mode="append",
    )

    success, message = executor.write_file(file_block)

    assert success is True
    content = test_file.read_text()
    assert "Line 1" in content
    assert "Line 2" in content


def test_write_file_executable(tmp_path):
    """Test making a file executable."""
    import stat

    from guiderails.parser import FileBlock

    executor = Executor(base_working_dir=str(tmp_path))
    file_block = FileBlock(
        code="#!/bin/bash\necho test",
        path="script.sh",
        mode="write",
        executable=True,
    )

    success, message = executor.write_file(file_block)

    assert success is True
    test_file = tmp_path / "script.sh"
    assert test_file.exists()

    # Check executable bit
    file_stat = test_file.stat()
    assert file_stat.st_mode & stat.S_IXUSR


def test_write_file_with_template(tmp_path):
    """Test writing a file with variable substitution."""
    from guiderails.executor import VariableStore
    from guiderails.parser import FileBlock

    store = VariableStore({"NAME": "Alice", "AGE": "30"})
    executor = Executor(base_working_dir=str(tmp_path), variable_store=store)

    file_block = FileBlock(
        code="Hello ${NAME}, age ${AGE}",
        path="output.txt",
        mode="write",
        template="shell",
    )

    success, message = executor.write_file(file_block)

    assert success is True
    test_file = tmp_path / "output.txt"
    assert test_file.read_text() == "Hello Alice, age 30\n"


def test_write_file_once_flag(tmp_path):
    """Test once flag skips existing files."""
    from guiderails.parser import FileBlock

    # Create existing file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Original\n")

    executor = Executor(base_working_dir=str(tmp_path))
    file_block = FileBlock(
        code="New Content",
        path="test.txt",
        mode="write",
        once=True,
    )

    success, message = executor.write_file(file_block)

    assert success is True
    assert "already exists" in message
    assert test_file.read_text() == "Original\n"


def test_write_file_rejects_unsafe_path(tmp_path):
    """Test that unsafe paths are rejected."""
    from guiderails.parser import FileBlock

    executor = Executor(base_working_dir=str(tmp_path))
    file_block = FileBlock(
        code="Content",
        path="../../../etc/passwd",
        mode="write",
    )

    success, message = executor.write_file(file_block)

    assert success is False
    assert "not allowed" in message.lower()


def test_execute_with_output_capture(tmp_path):
    """Test capturing output to a variable."""
    executor = Executor(base_working_dir=str(tmp_path))
    code_block = CodeBlock(
        code='echo "Hello World"',
        out_var="GREETING",
    )

    result = executor.execute_code_block(code_block)

    assert result.success is True
    assert executor.variables.get("GREETING") == "Hello World"


def test_execute_with_exit_code_capture(tmp_path):
    """Test capturing exit code to a variable."""
    executor = Executor(base_working_dir=str(tmp_path))
    code_block = CodeBlock(
        code="exit 42",
        code_var="EXIT_STATUS",
    )

    result = executor.execute_code_block(code_block)

    assert result.exit_code == 42
    assert executor.variables.get("EXIT_STATUS") == "42"


def test_execute_with_output_file(tmp_path):
    """Test writing output to a file."""
    executor = Executor(base_working_dir=str(tmp_path))
    code_block = CodeBlock(
        code='echo "Test output"',
        out_file="output.txt",
    )

    result = executor.execute_code_block(code_block)

    assert result.success is True
    output_file = tmp_path / "output.txt"
    assert output_file.exists()
    assert "Test output" in output_file.read_text()


def test_execute_with_variable_substitution(tmp_path):
    """Test variable substitution in command execution."""
    from guiderails.executor import VariableStore

    store = VariableStore({"NAME": "Alice"})
    executor = Executor(base_working_dir=str(tmp_path), variable_store=store)

    code_block = CodeBlock(code='echo "Hello ${NAME}"')

    result = executor.execute_code_block(code_block)

    assert result.success is True
    assert "Hello Alice" in result.stdout


def test_execute_with_all_captures(tmp_path):
    """Test multiple capture options at once."""
    from guiderails.executor import VariableStore

    store = VariableStore()
    executor = Executor(base_working_dir=str(tmp_path), variable_store=store)

    code_block = CodeBlock(
        code='echo "Output"; exit 5',
        out_var="OUT",
        code_var="CODE",
        out_file="result.txt",
    )

    executor.execute_code_block(code_block)

    assert store.get("OUT") == "Output"
    assert store.get("CODE") == "5"
    assert (tmp_path / "result.txt").exists()
