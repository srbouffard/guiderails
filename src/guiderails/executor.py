"""Command executor and output validator for GuideRails."""

import os
import re
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

from .parser import CodeBlock, FileBlock


class VariableStore:
    """Stores and manages variables for substitution."""

    def __init__(self, initial_vars: Optional[Dict[str, str]] = None):
        """Initialize variable store.

        Args:
            initial_vars: Optional initial variables (e.g., from CLI --var)
        """
        self.variables: Dict[str, str] = initial_vars or {}

    def set(self, name: str, value: str):
        """Set a variable value."""
        self.variables[name] = value

    def get(self, name: str, default: str = "") -> str:
        """Get a variable value."""
        return self.variables.get(name, default)

    def substitute(self, text: str) -> str:
        """Substitute ${VAR} patterns in text with variable values.

        Args:
            text: Text containing ${VAR} patterns

        Returns:
            Text with substitutions applied
        """
        # Pattern to match ${VAR_NAME}
        pattern = re.compile(r'\$\{([a-zA-Z_][a-zA-Z0-9_]*)\}')

        def replace_var(match):
            var_name = match.group(1)
            return self.variables.get(var_name, match.group(0))  # Return original if not found

        return pattern.sub(replace_var, text)


class PathSandbox:
    """Validates paths to ensure they stay within the working directory."""

    @staticmethod
    def validate_path(path: str, base_dir: str, allow_outside: bool = False) -> Tuple[bool, str, str]:
        """Validate a file path for safety.

        Args:
            path: Path to validate (should be relative)
            base_dir: Base working directory
            allow_outside: Whether to allow paths outside the sandbox

        Returns:
            Tuple of (is_valid, resolved_path, error_message)
        """
        # Reject absolute paths by default
        if os.path.isabs(path) and not allow_outside:
            return False, "", "Absolute paths are not allowed for safety reasons"

        # If absolute path is allowed, use it directly
        if os.path.isabs(path):
            resolved = os.path.abspath(path)
        else:
            # Resolve relative to base directory
            resolved = os.path.abspath(os.path.join(base_dir, path))

        # Check if resolved path stays within base_dir (unless allow_outside)
        if not allow_outside:
            base_abs = os.path.abspath(base_dir)
            try:
                # Check if resolved path is under base_dir
                os.path.relpath(resolved, base_abs)
                if not resolved.startswith(base_abs + os.sep) and resolved != base_abs:
                    return False, "", f"Path traversal outside working directory not allowed: {path}"
            except ValueError:
                # Different drives on Windows
                return False, "", f"Path is on a different drive: {path}"

        return True, resolved, ""


@dataclass
class ExecutionResult:
    """Result of executing a code block."""

    success: bool
    exit_code: int
    stdout: str
    stderr: str
    error_message: Optional[str] = None


class Validator:
    """Validates command output against expected results."""

    @staticmethod
    def validate(result: ExecutionResult, code_block: CodeBlock) -> Tuple[bool, str]:
        """Validate execution result against code block expectations.

        Returns:
            Tuple of (success, message)
        """
        mode = code_block.mode
        expected = code_block.expected

        if mode == "exit":
            # Validate exit code
            expected_code = int(expected)
            if result.exit_code == expected_code:
                return True, f"Exit code matched: {expected_code}"
            else:
                return False, f"Exit code {result.exit_code} != expected {expected_code}"

        elif mode == "contains":
            # Check if output contains expected string
            output = result.stdout + result.stderr
            if expected in output:
                return True, f"Output contains: '{expected}'"
            else:
                return False, f"Output does not contain: '{expected}'"

        elif mode == "regex":
            # Match output against regex pattern
            output = result.stdout + result.stderr
            try:
                if re.search(expected, output, re.MULTILINE):
                    return True, f"Output matches regex: {expected}"
                else:
                    return False, f"Output does not match regex: {expected}"
            except re.error as e:
                return False, f"Invalid regex pattern: {e}"

        elif mode == "exact":
            # Exact match of output
            output = (result.stdout + result.stderr).strip()
            expected_stripped = expected.strip()
            if output == expected_stripped:
                return True, "Output matches exactly"
            else:
                msg = (
                    f"Output does not match exactly.\n"
                    f"Expected:\n{expected_stripped}\n"
                    f"Got:\n{output}"
                )
                return False, msg

        else:
            return False, f"Unknown validation mode: {mode}"


class Executor:
    """Executes code blocks and validates output."""

    def __init__(
        self,
        base_working_dir: Optional[str] = None,
        variable_store: Optional[VariableStore] = None,
        allow_outside: bool = False,
    ):
        """Initialize executor.

        Args:
            base_working_dir: Base directory for command execution
            variable_store: Variable store for substitution (created if not provided)
            allow_outside: Whether to allow file operations outside the working directory
        """
        self.base_working_dir = base_working_dir or os.getcwd()
        self.validator = Validator()
        self.variables = variable_store or VariableStore()
        self.allow_outside = allow_outside

    def write_file(self, file_block: FileBlock) -> Tuple[bool, str]:
        """Write a file from a FileBlock.

        Args:
            file_block: The file block to write

        Returns:
            Tuple of (success, message)
        """
        # Validate path
        is_valid, resolved_path, error = PathSandbox.validate_path(
            file_block.path, self.base_working_dir, self.allow_outside
        )
        if not is_valid:
            return False, error

        # Check if file exists and once=true
        if file_block.once and os.path.exists(resolved_path):
            return True, f"File already exists, skipping (once=true): {file_block.path}"

        # Apply template substitution if needed
        content = file_block.code
        if file_block.template == "shell":
            content = self.variables.substitute(content)

        # Ensure parent directory exists
        parent_dir = os.path.dirname(resolved_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

        try:
            # Write file
            mode = "a" if file_block.mode == "append" else "w"
            with open(resolved_path, mode, encoding="utf-8") as f:
                f.write(content)
                if not content.endswith("\n"):
                    f.write("\n")

            # Make executable if requested
            if file_block.executable:
                current_permissions = os.stat(resolved_path).st_mode
                os.chmod(resolved_path, current_permissions | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

            size = os.path.getsize(resolved_path)
            return True, f"Wrote {size} bytes to {file_block.path}"

        except Exception as e:
            return False, f"Failed to write file: {str(e)}"

    def execute_code_block(self, code_block: CodeBlock) -> ExecutionResult:
        """Execute a code block and return the result.

        Args:
            code_block: The code block to execute

        Returns:
            ExecutionResult with execution details
        """
        # Apply variable substitution to the command
        command = self.variables.substitute(code_block.code)

        # Determine working directory
        if code_block.working_dir:
            # If absolute, use it; otherwise, relative to base
            if os.path.isabs(code_block.working_dir):
                working_dir = code_block.working_dir
            else:
                working_dir = os.path.join(self.base_working_dir, code_block.working_dir)
        else:
            working_dir = self.base_working_dir

        # Ensure working directory exists
        if not os.path.exists(working_dir):
            return ExecutionResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr="",
                error_message=f"Working directory does not exist: {working_dir}",
            )

        try:
            # Execute command
            process = subprocess.run(
                command,
                shell=True,
                cwd=working_dir,
                capture_output=True,
                timeout=code_block.timeout,
                text=True,
            )

            result = ExecutionResult(
                success=process.returncode == 0,
                exit_code=process.returncode,
                stdout=process.stdout,
                stderr=process.stderr,
            )

            # Capture output to variable if requested
            if code_block.out_var:
                combined_output = process.stdout + process.stderr
                self.variables.set(code_block.out_var, combined_output.strip())

            # Capture output to file if requested
            if code_block.out_file:
                is_valid, resolved_path, error = PathSandbox.validate_path(
                    code_block.out_file, self.base_working_dir, self.allow_outside
                )
                if is_valid:
                    try:
                        parent_dir = os.path.dirname(resolved_path)
                        if parent_dir:
                            os.makedirs(parent_dir, exist_ok=True)
                        with open(resolved_path, "w", encoding="utf-8") as f:
                            f.write(process.stdout)
                    except Exception as e:
                        # Don't fail execution if file write fails, just note it
                        result.error_message = f"Warning: Failed to write output file: {str(e)}"

            # Capture exit code to variable if requested
            if code_block.code_var:
                self.variables.set(code_block.code_var, str(process.returncode))

            return result

        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr="",
                error_message=f"Command timed out after {code_block.timeout} seconds",
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr="",
                error_message=f"Execution error: {str(e)}",
            )

    def execute_and_validate(self, code_block: CodeBlock) -> Tuple[ExecutionResult, bool, str]:
        """Execute a code block and validate its output.

        Args:
            code_block: The code block to execute

        Returns:
            Tuple of (ExecutionResult, validation_success, validation_message)
        """
        result = self.execute_code_block(code_block)

        # If execution failed with error, validation fails
        if result.error_message:
            return result, False, result.error_message

        # Validate the result
        validation_success, validation_message = self.validator.validate(result, code_block)

        return result, validation_success, validation_message
