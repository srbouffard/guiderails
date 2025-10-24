"""Workflow command: Generate GitHub Actions workflow for a tutorial."""

import sys
from pathlib import Path
import yaml
from jinja2 import Template


def get_default_template():
    """Get the default workflow template."""
    template_dir = Path(__file__).parent.parent.parent.parent / "templates"
    return template_dir / "workflow.yml.j2"


def run(args):
    """Run the workflow command."""
    # Load tutorial YAML
    tutorial_path = Path(args.tutorial)
    if not tutorial_path.exists():
        print(f"Error: Tutorial file not found: {tutorial_path}", file=sys.stderr)
        return 1
    
    with open(tutorial_path, 'r') as f:
        tutorial_data = yaml.safe_load(f)
    
    # Load template
    if args.template:
        template_path = Path(args.template)
        if not template_path.exists():
            print(f"Error: Template file not found: {template_path}", file=sys.stderr)
            return 1
        with open(template_path, 'r') as f:
            template = Template(f.read())
    else:
        default_template = get_default_template()
        if default_template.exists():
            with open(default_template, 'r') as f:
                template = Template(f.read())
        else:
            # Fallback inline template
            template = Template("""name: {{ workflow_name }}

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  workflow_dispatch:

jobs:
  validate-tutorial:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install guiderails
        run: |
          pip install -e .
      
      - name: Execute tutorial
        run: |
          guiderun exec {{ tutorial_file }} --ci
""")
    
    # Prepare template variables
    tutorial_name = tutorial_data.get('title', 'Tutorial')
    tutorial_file = tutorial_path.name
    workflow_name = f"Validate {tutorial_name}"
    
    template_vars = {
        'workflow_name': workflow_name,
        'tutorial_name': tutorial_name,
        'tutorial_file': tutorial_file,
        'tutorial_path': str(tutorial_path),
        **tutorial_data
    }
    
    # Render template
    rendered = template.render(**template_vars)
    
    # Output
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(rendered)
        print(f"Generated workflow: {output_path}")
    else:
        print(rendered)
    
    return 0
