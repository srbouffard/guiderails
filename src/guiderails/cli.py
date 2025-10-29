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
        # Display step header
        console.print()
        step_header = f"Step {step_num}/{len(self.tutorial.steps)}: {step.title}"
        console.print(f"[bold blue]{step_header}[/bold blue]")

        if step.step_id:
            console.print(f"[dim]ID: {step.step_id}[/dim]")

        # Display step content (explanation)
        if step.content.strip():
            console.print()
            console.print(Markdown(step.content.strip()))

        # Check if step has executable code blocks
        if not step.code_blocks:
            console.print("[dim]No executable code blocks in this step[/dim]")
            return True

        # In guided mode, ask user to proceed
        if self.guided:
            console.print()
            prompt = f"[cyan]Execute {len(step.code_blocks)} code block(s)?[/cyan]"
            if not Confirm.ask(prompt, default=True):
                console.print("[yellow]Skipped by user[/yellow]")
                return True

        # Execute code blocks
        step_passed = True
        for block_idx, code_block in enumerate(step.code_blocks, start=1):
            block_passed = self._run_code_block(step_num, block_idx, code_block)
            if not block_passed:
                step_passed = False
                if not code_block.continue_on_error:
                    break

        return step_passed

    def _run_code_block(self, step_num: int, block_num: int, code_block: CodeBlock) -> bool:
        """Run a single code block.

        Args:
            step_num: Step number (1-indexed)
            block_num: Code block number within step (1-indexed)
            code_block: The code block to run

        Returns:
            True if validation passed, False otherwise
        """
        console.print()
        console.print(f"[bold]Code Block {block_num}:[/bold]")

        # Display code
        syntax = Syntax(code_block.code, code_block.language, theme="monokai", line_numbers=False)
        console.print(Panel(syntax, border_style="green"))

        # Display execution parameters
        console.print(f"[dim]Validation: {code_block.mode} = {code_block.expected}[/dim]")
        if code_block.timeout != 30:
            console.print(f"[dim]Timeout: {code_block.timeout}s[/dim]")
        if code_block.working_dir:
            console.print(f"[dim]Working dir: {code_block.working_dir}[/dim]")

        # Execute
        console.print()
        if self.guided:
            console.print("[cyan]Executing...[/cyan]")
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

        if not self.guided or True:  # Always execute in both modes
            result, validation_passed, validation_message = self.executor.execute_and_validate(
                code_block
            )

        # Display output
        if result.stdout:
            console.print("[bold]Output:[/bold]")
            console.print(result.stdout)

        if result.stderr:
            console.print("[bold yellow]Error Output:[/bold yellow]")
            console.print(result.stderr)

        # Display validation result
        console.print()
        if validation_passed:
            console.print(f"[bold green]✓ PASSED[/bold green]: {validation_message}")
            return True
        else:
            console.print(f"[bold red]✗ FAILED[/bold red]: {validation_message}")
            if code_block.continue_on_error:
                msg = "[yellow]Continuing despite failure (continue-on-error=true)[/yellow]"
                console.print(msg)
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
