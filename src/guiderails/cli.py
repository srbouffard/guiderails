"""CLI for guiderails - Write. Generate. Run."""

import argparse
import sys
from pathlib import Path

from guiderails.commands import render, exec_tutorial, workflow, init


def main():
    """Main entry point for the guiderun CLI."""
    parser = argparse.ArgumentParser(
        prog="guiderun",
        description="Write. Generate. Run. Create readable tutorials from YAML and validate them in CI."
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # render command
    render_parser = subparsers.add_parser(
        "render",
        help="Render YAML tutorial to Markdown using Jinja templates"
    )
    render_parser.add_argument(
        "tutorial",
        help="Path to tutorial YAML file"
    )
    render_parser.add_argument(
        "-o", "--output",
        help="Output Markdown file (default: stdout)"
    )
    render_parser.add_argument(
        "-t", "--template",
        help="Custom Jinja template file (default: built-in tutorial.md.j2)"
    )
    
    # exec command
    exec_parser = subparsers.add_parser(
        "exec",
        help="Execute tutorial steps locally or in CI"
    )
    exec_parser.add_argument(
        "tutorial",
        help="Path to tutorial YAML file"
    )
    exec_parser.add_argument(
        "--step",
        type=int,
        help="Run specific step number (default: all steps)"
    )
    exec_parser.add_argument(
        "--ci",
        action="store_true",
        help="Run in CI mode (exit on first failure)"
    )
    
    # workflow command
    workflow_parser = subparsers.add_parser(
        "workflow",
        help="Generate GitHub Actions workflow for a tutorial"
    )
    workflow_parser.add_argument(
        "tutorial",
        help="Path to tutorial YAML file"
    )
    workflow_parser.add_argument(
        "-o", "--output",
        help="Output workflow YAML file (default: stdout)"
    )
    workflow_parser.add_argument(
        "-t", "--template",
        help="Custom Jinja template file (default: built-in workflow.yml.j2)"
    )
    
    # init command
    init_parser = subparsers.add_parser(
        "init",
        help="Initialize a sample tutorial"
    )
    init_parser.add_argument(
        "name",
        nargs="?",
        default="getting-started",
        help="Name of the tutorial (default: getting-started)"
    )
    init_parser.add_argument(
        "-o", "--output",
        help="Output directory (default: tutorials/)"
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        if args.command == "render":
            return render.run(args)
        elif args.command == "exec":
            return exec_tutorial.run(args)
        elif args.command == "workflow":
            return workflow.run(args)
        elif args.command == "init":
            return init.run(args)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
