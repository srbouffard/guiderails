"""Command executor and output validator for GuideRails."""

import os
import re
import subprocess
from dataclasses import dataclass
from typing import Optional, Tuple

from .parser import CodeBlock


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

    def __init__(self, base_working_dir: Optional[str] = None):
        """Initialize executor.

        Args:
            base_working_dir: Base directory for command execution
        """
        self.base_working_dir = base_working_dir or os.getcwd()
        self.validator = Validator()

    def execute_code_block(self, code_block: CodeBlock) -> ExecutionResult:
        """Execute a code block and return the result.

        Args:
            code_block: The code block to execute

        Returns:
            ExecutionResult with execution details
        """
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
                code_block.code,
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
