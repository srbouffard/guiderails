"""Command-line interface for GuideRails."""

import os
import sys
from typing import Optional

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm
from rich.syntax import Syntax

from .executor import Executor
from .parser import CodeBlock, MarkdownParser, Step, Tutorial

console = Console()


class GuideRunner:
    """Runs tutorials in guided or CI mode."""

    def __init__(self, tutorial: Tutorial, working_dir: Optional[str] = None, guided: bool = True):
        """Initialize the runner.

        Args:
            tutorial: The tutorial to run
            working_dir: Base working directory for execution
            guided: Whether to run in guided (interactive) mode
        """
        self.tutorial = tutorial
        self.working_dir = working_dir or os.getcwd()
        self.guided = guided
        self.executor = Executor(base_working_dir=self.working_dir)
        self.failed_steps = []

    def run(self) -> bool:
        """Run the tutorial.

        Returns:
            True if all steps passed, False otherwise
        """
        # Display tutorial header
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
        # Display step header with clear separation
        console.print()
        console.print("─" * 80)
        console.print()
        step_header = f"Step {step_num}/{len(self.tutorial.steps)}: {step.title}"
        console.print(Panel.fit(f"[bold blue]{step_header}[/bold blue]", border_style="blue"))

        if step.step_id:
            console.print(f"[dim]ID: {step.step_id}[/dim]")

        # Check if step has executable code blocks
        if not step.code_blocks:
            console.print()
            console.print("[dim]No executable code blocks in this step[/dim]")
            return True

        # Display step content with inline code blocks in a box
        console.print()
        console.print("╭─ [bold green]Step Content[/bold green] " + "─" * 60 + "╮")
        console.print("│")
        self._display_step_content_with_blocks(step)
        console.print("│")
        console.print("╰" + "─" * 78 + "╯")

        # In guided mode, ask for confirmation
        if self.guided:
            console.print()
            console.print("╭─ [bold cyan]Confirmation[/bold cyan] " + "─" * 59 + "╮")
            console.print("│")
            num_blocks = len(step.code_blocks)
            console.print(f"│  [cyan]▶ Execute the above {num_blocks} code block(s)?[/cyan]")
            console.print("│")
            console.print("╰" + "─" * 78 + "╯")
            console.print()
            
            if not Confirm.ask("", default=True):
                console.print()
                console.print("╭─ [bold yellow]Status[/bold yellow] " + "─" * 64 + "╮")
                console.print("│  [yellow]⊗ Skipped by user[/yellow]")
                console.print("╰" + "─" * 78 + "╯")
                console.print()
                return True

        # Execute code blocks and display results
        console.print()
        step_passed = self._execute_and_display_results(step)

        return step_passed

    def _display_step_content_with_blocks(self, step: Step):
        """Display step content with code blocks shown inline.

        This reconstructs the visual flow of the tutorial by displaying
        content and code blocks as they appear in the original markdown.

        Args:
            step: The step to display
        """
        # Use content_parts if available for proper interleaving
        if step.content_parts:
            for part in step.content_parts:
                if isinstance(part, CodeBlock):
                    # This is a code block - display it with formatting in guided mode
                    if self.guided:
                        block_idx = step.code_blocks.index(part) + 1
                        self._display_code_block_inline(block_idx, part)
                elif isinstance(part, str) and part.strip():
                    # This is content text - display as markdown with indent
                    for line in Markdown(part.strip()).renderable.split('\n') if hasattr(Markdown(part.strip()), 'renderable') else []:
                        console.print(f"│  {line}")
                    # Simpler approach - just print with indent
                    console.print("│")
                    lines = part.strip().split('\n')
                    for line in lines:
                        console.print(f"│  {line}")
                    console.print("│")
        elif step.content.strip():
            # Fallback to old behavior if content_parts not available
            console.print("│")
            lines = step.content.strip().split('\n')
            for line in lines:
                console.print(f"│  {line}")
            console.print("│")
            
            if step.code_blocks and self.guided:
                for block_idx, code_block in enumerate(step.code_blocks, start=1):
                    self._display_code_block_inline(block_idx, code_block)

    def _display_code_block_inline(self, block_num: int, code_block: CodeBlock):
        """Display a code block inline with clear formatting for guided mode.

        Args:
            block_num: Code block number within step (1-indexed)
            code_block: The code block to display
        """
        console.print(f"│  [dim]→ Code Block {block_num} (will execute):[/dim]")
        console.print("│")
        
        # Display code with simple border
        console.print("│  ┌" + "─" * 70 + "┐")
        for line in code_block.code.split('\n'):
            console.print(f"│  │ [cyan]{line}[/cyan]")
        console.print("│  └" + "─" * 70 + "┘")
        
        # Display execution parameters compactly
        params = [f"mode={code_block.mode}", f"expect={code_block.expected}"]
        if code_block.timeout != 30:
            params.append(f"timeout={code_block.timeout}s")
        if code_block.working_dir:
            params.append(f"workdir={code_block.working_dir}")
        console.print(f"│  [dim][{', '.join(params)}][/dim]")
        console.print("│")

    def _execute_and_display_results(self, step: Step) -> bool:
        """Execute code blocks and display results in a box.

        Args:
            step: The step containing code blocks to execute

        Returns:
            True if all blocks passed, False otherwise
        """
        step_passed = True
        border_color = "green"
        
        console.print("╭─ [bold green]Execution Results[/bold green] " + "─" * 52 + "╮")
        console.print("│")

        for block_idx, code_block in enumerate(step.code_blocks, start=1):
            console.print(f"│  [bold cyan]Block {block_idx}:[/bold cyan]")
            console.print("│")

            # Execute
            result, validation_passed, validation_message = self.executor.execute_and_validate(
                code_block
            )

            # Display output
            if result.stdout:
                console.print("│  [bold]Output:[/bold]")
                for line in result.stdout.split('\n'):
                    if line:
                        console.print(f"│    {line}")

            if result.stderr:
                console.print("│")
                console.print("│  [bold yellow]Error Output:[/bold yellow]")
                for line in result.stderr.split('\n'):
                    if line:
                        console.print(f"│    {line}")

            # Display validation result
            console.print("│")
            if validation_passed:
                console.print(f"│  [bold green]✓ PASSED[/bold green]: {validation_message}")
            else:
                console.print(f"│  [bold red]✗ FAILED[/bold red]: {validation_message}")
                if code_block.continue_on_error:
                    console.print(
                        "│  [yellow]Continuing despite failure (continue-on-error=true)[/yellow]"
                    )
                step_passed = False
                border_color = "red"

            if not validation_passed and not code_block.continue_on_error:
                break

            if block_idx < len(step.code_blocks):
                console.print("│")
                console.print("│  " + "─" * 74)
                console.print("│")

        console.print("│")
        
        # Update border color based on results
        if not step_passed:
            console.print("╰" + "─" * 78 + "╯ [red]✗ Failed[/red]")
        else:
            console.print("╰" + "─" * 78 + "╯ [green]✓ Passed[/green]")

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
def exec(tutorial: str, guided: bool, ci: bool, working_dir: Optional[str]):
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

    # Parse tutorial
    parser = MarkdownParser()

    try:
        console.print(f"[cyan]Loading tutorial from: {tutorial}[/cyan]")

        if tutorial.startswith("http://") or tutorial.startswith("https://"):
            # URL
            parsed_tutorial = parser.parse_url(tutorial)
        else:
            # Local file
            parsed_tutorial = parser.parse_file(tutorial)

        console.print(f"[green]✓ Loaded: {parsed_tutorial.title}[/green]")

    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error loading tutorial: {e}[/red]")
        sys.exit(1)

    # Run tutorial
    runner = GuideRunner(parsed_tutorial, working_dir=working_dir, guided=is_guided)

    success = runner.run()

    sys.exit(0 if success else 1)


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
