"""Command-line interface for GuideRails."""

import os
import sys
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm
from rich.syntax import Syntax

from .config import OutputConfig
from .executor import Executor, VariableStore
from .parser import CodeBlock, FileBlock, MarkdownParser, Step, Tutorial

console = Console()


class GuideRunner:
    """Runs tutorials in guided or CI mode."""

    def __init__(
        self,
        tutorial: Tutorial,
        working_dir: Optional[str] = None,
        guided: bool = True,
        variables: Optional[VariableStore] = None,
        output_config: Optional[OutputConfig] = None,
    ):
        """Initialize the runner.

        Args:
            tutorial: The tutorial to run
            working_dir: Base working directory for execution
            guided: Whether to run in guided (interactive) mode
            variables: Variable store for substitution
            output_config: Output configuration for verbosity and toggles
        """
        self.tutorial = tutorial
        self.working_dir = working_dir or os.getcwd()
        self.guided = guided
        self.variables = variables or VariableStore()
        self.executor = Executor(base_working_dir=self.working_dir, variable_store=self.variables)
        self.failed_steps = []
        self.output_config = output_config or OutputConfig()

    def run(self) -> bool:
        """Run the tutorial.

        Returns:
            True if all steps passed, False otherwise
        """
        # Display tutorial header (skip in quiet mode)
        if self.output_config.show_step_banners:
            console.print()
            console.print(
                Panel.fit(
                    f"[bold cyan]{self.tutorial.title}[/bold cyan]\n"
                    f"[dim]Source: {self.tutorial.source}[/dim]\n"
                    f"[dim]Steps: {len(self.tutorial.steps)}[/dim]",
                    title="GuideRails Tutorial",
                    border_style="cyan",
                )
            )
            console.print()

        if not self.tutorial.steps:
            console.print("[yellow]Warning: No steps found in tutorial[/yellow]")
            return True

        all_passed = True

        for idx, step in enumerate(self.tutorial.steps, start=1):
            step_passed = self._run_step(idx, step)
            if not step_passed:
                all_passed = False
                self.failed_steps.append((idx, step))

                if not step.code_blocks or not any(cb.continue_on_error for cb in step.code_blocks):
                    if not self.guided:
                        # In CI mode, stop on first failure
                        break

        # Display summary
        self._display_summary(all_passed)

        return all_passed

    def _run_step(self, step_num: int, step: Step) -> bool:
        """Run a single step.

        Args:
            step_num: Step number (1-indexed)
            step: The step to run

        Returns:
            True if step passed, False otherwise
        """
        # Get terminal width for full-width boxes
        width = console.width

        # Display step header with clear separation (always show, even in quiet)
        if self.output_config.show_step_banners:
            console.print()
            console.print("─" * width)
            console.print()
            step_header = f"Step {step_num}/{len(self.tutorial.steps)}: {step.title}"
            console.print(Panel.fit(f"[bold blue]{step_header}[/bold blue]", border_style="blue"))

            if step.step_id:
                console.print(f"[dim]ID: {step.step_id}[/dim]")
        else:
            # In quiet mode, just show step title
            console.print()
            step_header = f"Step {step_num}/{len(self.tutorial.steps)}: {step.title}"
            console.print(f"[bold blue]{step_header}[/bold blue]")

        # Check if step has executable blocks (code or file)
        has_blocks = len(step.code_blocks) > 0 or len(step.file_blocks) > 0
        if not has_blocks:
            if self.output_config.show_step_banners:
                console.print()
                console.print("[dim]No executable code blocks in this step[/dim]")
            return True

        # Display step content with inline code blocks in a box (skip in quiet mode)
        if self.output_config.show_step_banners:
            console.print()
            title = "[bold green]Step Content[/bold green]"
            # Account for "╭─ " prefix and " ╮" suffix when calculating dash count
            title_len = len("Step Content") + 3  # " " on each side + "─"
            console.print("╭─ " + title + " " + "─" * (width - title_len - 3) + "╮")
            self._display_step_content_with_blocks(step)
            console.print("╰" + "─" * (width - 2) + "╯")

        # In guided mode, ask for confirmation
        if self.guided:
            console.print()
            if self.output_config.show_step_banners:
                title = "[bold cyan]Confirmation[/bold cyan]"
                title_len = len("Confirmation") + 3
                console.print("╭─ " + title + " " + "─" * (width - title_len - 3) + "╮")
                total_blocks = len(step.code_blocks) + len(step.file_blocks)
                prompt_text = f"[cyan]▶ Execute the above {total_blocks} block(s)?[/cyan]"
                self._print_box_line(prompt_text, width)
                console.print("╰" + "─" * (width - 2) + "╯")
                console.print()

            if not Confirm.ask("Execute?", default=True):
                console.print()
                if self.output_config.show_step_banners:
                    title = "[bold yellow]Status[/bold yellow]"
                    title_len = len("Status") + 3
                    console.print("╭─ " + title + " " + "─" * (width - title_len - 3) + "╮")
                    self._print_box_line("[yellow]⊗ Skipped by user[/yellow]", width)
                    console.print("╰" + "─" * (width - 2) + "╯")
                else:
                    console.print("[yellow]⊗ Skipped by user[/yellow]")
                console.print()
                return True

        # Execute code blocks and display results
        console.print()
        step_passed = self._execute_and_display_results(step)

        return step_passed

    def _print_box_line(self, text: str, width: int):
        """Print a line inside a box with proper padding to reach the right border.

        Args:
            text: The text to print (may contain Rich markup)
            width: Terminal width
        """
        # Strip Rich markup to calculate actual text length
        import re

        plain_text = re.sub(r"\[/?[^\]]+\]", "", text)
        text_len = len(plain_text)
        # Account for "│  " prefix (3 chars) and " │" suffix (2 chars)
        padding = width - text_len - 5
        console.print(f"│  {text}{' ' * max(0, padding)} │")

    def _display_step_content_with_blocks(self, step: Step):
        """Display step content with code blocks shown inline.

        This reconstructs the visual flow of the tutorial by displaying
        content and code blocks as they appear in the original markdown.

        Args:
            step: The step to display
        """
        width = console.width

        # Use content_parts if available for proper interleaving
        if step.content_parts:
            code_block_idx = 0
            file_block_idx = 0
            for part in step.content_parts:
                if isinstance(part, CodeBlock):
                    # This is a code block - display it with formatting in guided mode
                    if self.guided:
                        code_block_idx += 1
                        self._display_code_block_inline(code_block_idx, part, "Code")
                elif isinstance(part, FileBlock):
                    # This is a file block - display it with formatting in guided mode
                    if self.guided:
                        file_block_idx += 1
                        self._display_file_block_inline(file_block_idx, part)
                elif isinstance(part, str) and part.strip():
                    # This is content text - display with proper padding
                    lines = part.strip().split("\n")
                    for line in lines:
                        self._print_box_line(line, width)
                    # Add spacing after content block
                    self._print_box_line("", width)
        elif step.content.strip():
            # Fallback to old behavior if content_parts not available
            lines = step.content.strip().split("\n")
            for line in lines:
                self._print_box_line(line, width)
            self._print_box_line("", width)

            if self.guided:
                # Display file blocks first
                for block_idx, file_block in enumerate(step.file_blocks, start=1):
                    self._display_file_block_inline(block_idx, file_block)

                # Then code blocks
                for block_idx, code_block in enumerate(step.code_blocks, start=1):
                    self._display_code_block_inline(block_idx, code_block, "Code")

    def _display_code_block_inline(
        self, block_num: int, code_block: CodeBlock, label: str = "Code"
    ):
        """Display a code block inline with clear formatting for guided mode.

        Args:
            block_num: Code block number within step (1-indexed)
            code_block: The code block to display
            label: Label for the block type (e.g., "Code", "File")
        """
        width = console.width

        # Check if substitution will occur at runtime
        substituted_code = self.variables.substitute(code_block.code)
        has_substitution = substituted_code != code_block.code

        self._print_box_line(f"[dim]→ {label} Block {block_num} (will execute):[/dim]", width)
        self._print_box_line("", width)

        # Display code with simple border - adjust inner width to terminal
        if self.output_config.show_commands:
            inner_width = width - 8  # Account for "│  ┌" prefix and "┐ │" suffix
            self._print_box_line("┌" + "─" * inner_width + "┐", width)

            # Always display original code to match tutorial text
            for line in code_block.code.split("\n"):
                # Pad code line to inner width
                plain_line = line
                line_padding = inner_width - len(plain_line) - 2  # -2 for "│ "
                padded_code = f"│ [cyan]{line}[/cyan]{' ' * max(0, line_padding)} │"
                self._print_box_line(padded_code, width)
            self._print_box_line("└" + "─" * inner_width + "┘", width)

        if has_substitution and self.output_config.show_substituted:
            self._print_box_line(
                "[dim](variable substitution will be applied at runtime)[/dim]", width
            )
            # In verbose mode, show the substituted command
            if self.output_config.show_previews:
                self._print_box_line("[dim]After substitution:[/dim]", width)
                inner_width = width - 8
                self._print_box_line("┌" + "─" * inner_width + "┐", width)
                for line in substituted_code.split("\n"):
                    plain_line = line
                    line_padding = inner_width - len(plain_line) - 2
                    padded_code = f"│ [yellow]{line}[/yellow]{' ' * max(0, line_padding)} │"
                    self._print_box_line(padded_code, width)
                self._print_box_line("└" + "─" * inner_width + "┘", width)

        # Display execution parameters compactly (in verbose+ mode or if show_expected is on)
        if self.output_config.show_expected or self.output_config.show_previews:
            params = []
            if self.output_config.show_expected:
                params.append(f"mode={code_block.mode}")
                params.append(f"expect={code_block.expected}")
            if code_block.timeout != 30:
                params.append(f"timeout={code_block.timeout}s")
            if code_block.working_dir and self.output_config.show_previews:
                params.append(f"workdir={code_block.working_dir}")
            if code_block.out_var:
                params.append(f"out-var={code_block.out_var}")
            if code_block.out_file:
                params.append(f"out-file={code_block.out_file}")
            if code_block.code_var:
                params.append(f"code-var={code_block.code_var}")
            if params:
                self._print_box_line(f"[dim][{', '.join(params)}][/dim]", width)
        self._print_box_line("", width)

    def _display_file_block_inline(self, block_num: int, file_block: FileBlock):
        """Display a file block inline with clear formatting for guided mode.

        Args:
            block_num: File block number within step (1-indexed)
            file_block: The file block to display
        """
        width = console.width

        # Check if substitution will occur when file is written
        has_substitution = False
        if file_block.template == "shell":
            substituted = self.variables.substitute(file_block.code)
            has_substitution = substituted != file_block.code

        self._print_box_line(f"[dim]→ File Block {block_num} (will write to file):[/dim]", width)
        self._print_box_line("", width)

        # Display code with simple border - adjust inner width to terminal
        inner_width = width - 8  # Account for "│  ┌" prefix and "┐ │" suffix
        self._print_box_line("┌" + "─" * inner_width + "┐", width)
        # Always display original content to match tutorial text
        for line in file_block.code.split("\n"):
            # Pad code line to inner width
            plain_line = line
            line_padding = inner_width - len(plain_line) - 2  # -2 for "│ "
            padded_code = f"│ [green]{line}[/green]{' ' * max(0, line_padding)} │"
            self._print_box_line(padded_code, width)
        self._print_box_line("└" + "─" * inner_width + "┘", width)

        if has_substitution:
            self._print_box_line(
                "[dim](variable substitution will be applied when writing)[/dim]", width
            )

        # Display file parameters
        params = [f"path={file_block.path}", f"mode={file_block.mode}"]
        if file_block.executable:
            params.append("executable=true")
        if file_block.template != "none":
            params.append(f"template={file_block.template}")
        if file_block.once:
            params.append("once=true")
        self._print_box_line(f"[dim][{', '.join(params)}][/dim]", width)
        self._print_box_line("", width)

    def _execute_and_display_results(self, step: Step) -> bool:
        """Execute file blocks and code blocks in order, then display results in a box.

        Args:
            step: The step containing blocks to execute

        Returns:
            True if all blocks passed, False otherwise
        """
        width = console.width
        step_passed = True

        # In quiet mode, simpler output
        if not self.output_config.show_step_banners:
            console.print()
        else:
            title = "[bold green]Execution Results[/bold green]"
            title_len = len("Execution Results") + 3
            console.print("╭─ " + title + " " + "─" * (width - title_len - 3) + "╮")

        # Execute blocks in the order they appear in content_parts
        file_block_num = 0
        code_block_num = 0
        total_blocks = len(step.file_blocks) + len(step.code_blocks)
        current_block = 0

        for part in step.content_parts:
            if isinstance(part, FileBlock):
                file_block_num += 1
                current_block += 1

                if self.output_config.show_step_banners:
                    self._print_box_line(
                        f"[bold magenta]File Block {file_block_num}:[/bold magenta]", width
                    )
                    self._print_box_line("", width)

                # Write file
                success, message = self.executor.write_file(part)

                # Display result
                if self.output_config.show_step_banners:
                    self._print_box_line("", width)
                    if success:
                        msg = f"[bold green]✓ SUCCESS[/bold green]: {message}"
                        self._print_box_line(msg, width)
                    else:
                        msg = f"[bold red]✗ FAILED[/bold red]: {message}"
                        self._print_box_line(msg, width)
                        step_passed = False
                else:
                    # Quiet mode
                    if success:
                        console.print(f"[bold green]✓[/bold green] File: {part.path}")
                    else:
                        console.print(f"[bold red]✗ FAILED[/bold red]: {message}")
                        step_passed = False

                if self.output_config.show_step_banners and current_block < total_blocks:
                    self._print_box_line("", width)
                    self._print_box_line("─" * (width - 5), width)
                    self._print_box_line("", width)

            elif isinstance(part, CodeBlock):
                code_block_num += 1
                current_block += 1

                if self.output_config.show_step_banners:
                    msg = f"[bold cyan]Code Block {code_block_num}:[/bold cyan]"
                    self._print_box_line(msg, width)
                    self._print_box_line("", width)
                elif self.output_config.show_commands:
                    # In quiet mode with show_commands, show the command
                    console.print(f"[cyan]$[/cyan] {part.code}")

                # Execute
                result, validation_passed, validation_message = self.executor.execute_and_validate(
                    part
                )

                # Display output
                if result.stdout:
                    if self.output_config.show_step_banners:
                        self._print_box_line("[bold]Output:[/bold]", width)
                        for line in result.stdout.split("\n"):
                            if line:
                                # Add extra indent for output
                                self._print_box_line(f"  {line}", width)
                    else:
                        # Quiet mode - just show output directly
                        console.print(result.stdout.rstrip())

                if result.stderr:
                    if self.output_config.show_step_banners:
                        self._print_box_line("", width)
                        self._print_box_line("[bold yellow]Error Output:[/bold yellow]", width)
                        for line in result.stderr.split("\n"):
                            if line:
                                self._print_box_line(f"  {line}", width)
                    else:
                        # Quiet mode - show stderr
                        console.print(f"[yellow]{result.stderr.rstrip()}[/yellow]")

                # Display capture info if variables were set
                if part.out_var and self.output_config.show_captured:
                    captured = self.variables.get(part.out_var)
                    if self.output_config.show_step_banners:
                        self._print_box_line("", width)
                        msg = (
                            f"[dim]Captured to variable {part.out_var}: "
                            f"{len(captured)} chars[/dim]"
                        )
                        self._print_box_line(msg, width)
                    else:
                        console.print(f"[dim]→ {part.out_var}[/dim]")

                if part.code_var and self.output_config.show_captured:
                    exit_code = self.variables.get(part.code_var)
                    if self.output_config.show_step_banners:
                        self._print_box_line(
                            f"[dim]Captured exit code to {part.code_var}: {exit_code}[/dim]", width
                        )
                    else:
                        console.print(f"[dim]→ {part.code_var}={exit_code}[/dim]")

                # Display validation result (always show failures)
                if self.output_config.show_step_banners:
                    self._print_box_line("", width)
                    if validation_passed:
                        self._print_box_line(
                            f"[bold green]✓ PASSED[/bold green]: {validation_message}", width
                        )
                    else:
                        self._print_box_line(
                            f"[bold red]✗ FAILED[/bold red]: {validation_message}", width
                        )
                        if part.continue_on_error:
                            msg = (
                                "[yellow]Continuing despite failure "
                                "(continue-on-error=true)[/yellow]"
                            )
                            self._print_box_line(msg, width)
                        else:
                            step_passed = False
                else:
                    # Quiet mode - show pass/fail
                    if validation_passed:
                        console.print("[bold green]✓ PASSED[/bold green]")
                    else:
                        console.print(f"[bold red]✗ FAILED[/bold red]: {validation_message}")
                        if part.continue_on_error:
                            console.print("[yellow]Continuing despite failure[/yellow]")
                        else:
                            step_passed = False

                if not validation_passed and not part.continue_on_error:
                    break

                if self.output_config.show_step_banners and current_block < total_blocks:
                    self._print_box_line("", width)
                    self._print_box_line("─" * (width - 5), width)
                    self._print_box_line("", width)

        if self.output_config.show_step_banners:
            self._print_box_line("", width)
            # Update border color based on results
            if not step_passed:
                console.print("╰" + "─" * (width - 2) + "╯ [red]✗ Failed[/red]")
            else:
                console.print("╰" + "─" * (width - 2) + "╯ [green]✓ Passed[/green]")
        else:
            console.print()

        return step_passed

    def _display_code_block(self, block_num: int, code_block: CodeBlock):
        """Display a code block without executing it.

        Args:
            block_num: Code block number within step (1-indexed)
            code_block: The code block to display
        """
        console.print(f"[bold]Block {block_num}:[/bold]")

        # Display code with syntax highlighting
        syntax = Syntax(code_block.code, code_block.language, theme="monokai", line_numbers=False)
        console.print(Panel(syntax, border_style="cyan"))

        # Display execution parameters
        params = []
        params.append(f"Validation: {code_block.mode} = {code_block.expected}")
        if code_block.timeout != 30:
            params.append(f"Timeout: {code_block.timeout}s")
        if code_block.working_dir:
            params.append(f"Working dir: {code_block.working_dir}")
        console.print(f"[dim]{' | '.join(params)}[/dim]")
        console.print()

    def _run_code_block(self, step_num: int, block_num: int, code_block: CodeBlock) -> bool:
        """Run a single code block.

        Args:
            step_num: Step number (1-indexed)
            block_num: Code block number within step (1-indexed)
            code_block: The code block to run

        Returns:
            True if validation passed, False otherwise
        """
        # In CI mode, display the code block first
        if not self.guided:
            console.print()
            console.print(f"[bold]Code Block {block_num}:[/bold]")

            # Display code
            syntax = Syntax(
                code_block.code, code_block.language, theme="monokai", line_numbers=False
            )
            console.print(Panel(syntax, border_style="green"))

            # Display execution parameters
            console.print(f"[dim]Validation: {code_block.mode} = {code_block.expected}[/dim]")
            if code_block.timeout != 30:
                console.print(f"[dim]Timeout: {code_block.timeout}s[/dim]")
            if code_block.working_dir:
                console.print(f"[dim]Working dir: {code_block.working_dir}[/dim]")
            console.print()

        # In guided mode, just show we're executing this specific block
        if self.guided:
            console.print(f"[cyan]▶ Executing Block {block_num}...[/cyan]")

        # Execute
        if self.guided:
            result, validation_passed, validation_message = self.executor.execute_and_validate(
                code_block
            )
        else:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True,
            ) as progress:
                progress.add_task(description="Executing...", total=None)
                result, validation_passed, validation_message = self.executor.execute_and_validate(
                    code_block
                )

        # Display output
        if result.stdout:
            console.print()
            console.print("[bold]Output:[/bold]")
            console.print(result.stdout)

        if result.stderr:
            console.print()
            console.print("[bold yellow]Error Output:[/bold yellow]")
            console.print(result.stderr)

        # Display validation result
        console.print()
        if validation_passed:
            console.print(f"[bold green]✓ PASSED[/bold green]: {validation_message}")
            console.print()
            return True
        else:
            console.print(f"[bold red]✗ FAILED[/bold red]: {validation_message}")
            if code_block.continue_on_error:
                msg = "[yellow]Continuing despite failure (continue-on-error=true)[/yellow]"
                console.print(msg)
            console.print()
            return False

    def _display_summary(self, all_passed: bool):
        """Display execution summary."""
        console.print()
        console.print("=" * 60)
        console.print()

        if all_passed:
            console.print(
                Panel.fit("[bold green]✓ All steps passed![/bold green]", border_style="green")
            )
        else:
            failed_count = len(self.failed_steps)
            console.print(
                Panel.fit(
                    f"[bold red]✗ {failed_count} step(s) failed[/bold red]", border_style="red"
                )
            )

            if self.failed_steps:
                console.print()
                console.print("[bold]Failed steps:[/bold]")
                for step_num, step in self.failed_steps:
                    console.print(f"  - Step {step_num}: {step.title}")


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """GuideRails: Tutorials-as-Code framework."""
    pass


@cli.command()
@click.argument("tutorial", type=str)
@click.option("--guided", is_flag=True, help="Run in interactive/guided mode")
@click.option("--ci", is_flag=True, help="Run in CI mode (non-interactive)")
@click.option("--working-dir", "-w", type=click.Path(), help="Base working directory for execution")
# Verbosity options
@click.option(
    "--verbosity",
    type=click.Choice(["quiet", "normal", "verbose", "debug"], case_sensitive=False),
    help="Set verbosity level (quiet, normal, verbose, debug)",
)
@click.option("--quiet", "-q", is_flag=True, help="Quiet mode (alias for --verbosity=quiet)")
@click.option("--verbose", "-v", count=True, help="Increase verbosity (-v, -vv, -vvv)")
@click.option("--debug", is_flag=True, help="Debug mode (alias for --verbosity=debug)")
# Output toggles
@click.option("--show-commands/--no-show-commands", default=None, help="Show/hide commands")
@click.option(
    "--show-substituted/--no-show-substituted",
    default=None,
    help="Show/hide substituted commands",
)
@click.option("--show-expected/--no-show-expected", default=None, help="Show/hide expected values")
@click.option("--show-captured/--no-show-captured", default=None, help="Show/hide captured output")
@click.option("--timestamps/--no-timestamps", default=None, help="Show/hide timestamps")
@click.option("--step-banners/--no-step-banners", default=None, help="Show/hide step banners")
@click.option("--previews/--no-previews", default=None, help="Show/hide command previews")
# Output format
@click.option(
    "--output",
    type=click.Choice(["text", "jsonl"], case_sensitive=False),
    default="text",
    help="Output format (text or jsonl)",
)
def exec(
    tutorial: str,
    guided: bool,
    ci: bool,
    working_dir: Optional[str],
    # Verbosity options
    verbosity: Optional[str],
    quiet: bool,
    verbose: int,
    debug: bool,
    # Output toggles
    show_commands: Optional[bool],
    show_substituted: Optional[bool],
    show_expected: Optional[bool],
    show_captured: Optional[bool],
    timestamps: Optional[bool],
    step_banners: Optional[bool],
    previews: Optional[bool],
    # Output format
    output: str,
):
    """Execute a Markdown tutorial.

    TUTORIAL can be:
    - A local file path (e.g., ./tutorial.md)
    - A URL to a Markdown file
    - A URL to an HTML page with <meta name="guiderails:source"> tag
    """
    # Determine mode
    if guided and ci:
        console.print("[red]Error: Cannot specify both --guided and --ci[/red]")
        sys.exit(1)

    # Default to guided if neither specified
    is_guided = guided or not ci

    # Create output configuration from CLI args and environment
    output_config = OutputConfig.from_cli_and_env(
        verbosity=verbosity,
        quiet=quiet,
        verbose_count=verbose,
        debug=debug,
        is_ci=ci,
        output_format=output,
        show_commands=show_commands,
        show_substituted=show_substituted,
        show_expected=show_expected,
        show_captured=show_captured,
        show_timestamps=timestamps,
        show_step_banners=step_banners,
        show_previews=previews,
    )

    # Parse tutorial
    parser = MarkdownParser()

    try:
        # Show loading message only in normal+ verbosity
        if output_config.should_show_at_level(output_config.verbosity):
            console.print(f"[cyan]Loading tutorial from: {tutorial}[/cyan]")

        if tutorial.startswith("http://") or tutorial.startswith("https://"):
            # URL
            parsed_tutorial = parser.parse_url(tutorial)
        else:
            # Local file
            parsed_tutorial = parser.parse_file(tutorial)

        if output_config.should_show_at_level(output_config.verbosity):
            console.print(f"[green]✓ Loaded: {parsed_tutorial.title}[/green]")

    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error loading tutorial: {e}[/red]")
        sys.exit(1)

    # Run tutorial
    runner = GuideRunner(
        parsed_tutorial,
        working_dir=working_dir,
        guided=is_guided,
        output_config=output_config,
    )

    success = runner.run()

    sys.exit(0 if success else 1)


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
