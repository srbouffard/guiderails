"""Render command: Convert YAML tutorial to Markdown using Jinja."""

import sys
from pathlib import Path
import yaml
from jinja2 import Environment, FileSystemLoader, Template


def get_default_template():
    """Get the default tutorial template."""
    template_dir = Path(__file__).parent.parent.parent.parent / "templates"
    return template_dir / "tutorial.md.j2"


def run(args):
    """Run the render command."""
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
            template = Template("""# {{ title }}

{{ description }}

{% if steps %}
## Steps

{% for step in steps %}
### Step {{ loop.index }}: {{ step.name }}

{{ step.description }}

{% if step.command %}
```bash
{{ step.command }}
```
{% endif %}

{% if step.expected %}
**Expected output:**
{{ step.expected }}
{% endif %}

{% endfor %}
{% endif %}
""")
    
    # Render template
    rendered = template.render(**tutorial_data)
    
    # Output
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(rendered)
        print(f"Rendered to: {output_path}")
    else:
        print(rendered)
    
    return 0
