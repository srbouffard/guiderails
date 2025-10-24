"""Init command: Initialize a sample tutorial."""

import sys
from pathlib import Path
import yaml


SAMPLE_TUTORIAL = {
    'title': 'Getting Started with guiderails',
    'description': 'A sample tutorial demonstrating the basics of guiderails.',
    'steps': [
        {
            'name': 'Check Python version',
            'description': 'Verify that Python 3.12+ is installed.',
            'command': 'python --version',
            'expected': 'Python 3.12 or higher'
        },
        {
            'name': 'Create a hello world script',
            'description': 'Create a simple Python script that prints "Hello, guiderails!"',
            'command': 'echo "print(\'Hello, guiderails!\')" > hello.py',
        },
        {
            'name': 'Run the script',
            'description': 'Execute the hello world script.',
            'command': 'python hello.py',
            'expected': 'Hello, guiderails!'
        },
        {
            'name': 'Clean up',
            'description': 'Remove the temporary script.',
            'command': 'rm hello.py',
        }
    ]
}


def run(args):
    """Run the init command."""
    # Determine output directory
    if args.output:
        output_dir = Path(args.output)
    else:
        output_dir = Path("tutorials")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create tutorial file
    tutorial_name = args.name
    if not tutorial_name.endswith('.yaml'):
        tutorial_name += '.yaml'
    
    tutorial_path = output_dir / tutorial_name
    
    if tutorial_path.exists():
        response = input(f"File {tutorial_path} already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("Cancelled.")
            return 0
    
    # Customize sample if not getting-started
    if args.name != 'getting-started':
        tutorial_data = SAMPLE_TUTORIAL.copy()
        tutorial_data['title'] = args.name.replace('-', ' ').replace('_', ' ').title()
        tutorial_data['description'] = f'A sample tutorial for {tutorial_data["title"]}.'
    else:
        tutorial_data = SAMPLE_TUTORIAL
    
    # Write tutorial
    with open(tutorial_path, 'w') as f:
        yaml.dump(tutorial_data, f, default_flow_style=False, sort_keys=False)
    
    print(f"✓ Created tutorial: {tutorial_path}")
    print(f"\nNext steps:")
    print(f"  1. Edit the tutorial: {tutorial_path}")
    print(f"  2. Render to Markdown: guiderun render {tutorial_path}")
    print(f"  3. Execute the tutorial: guiderun exec {tutorial_path}")
    print(f"  4. Generate CI workflow: guiderun workflow {tutorial_path}")
    
    return 0
