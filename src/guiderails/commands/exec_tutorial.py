"""Exec command: Execute tutorial steps locally or in CI."""

import sys
import subprocess
from pathlib import Path
import yaml


def run(args):
    """Run the exec command."""
    # Load tutorial YAML
    tutorial_path = Path(args.tutorial)
    if not tutorial_path.exists():
        print(f"Error: Tutorial file not found: {tutorial_path}", file=sys.stderr)
        return 1
    
    with open(tutorial_path, 'r') as f:
        tutorial_data = yaml.safe_load(f)
    
    title = tutorial_data.get('title', 'Tutorial')
    steps = tutorial_data.get('steps', [])
    
    if not steps:
        print("No steps to execute.", file=sys.stderr)
        return 1
    
    print(f"Executing tutorial: {title}")
    print("=" * 60)
    
    # Filter steps if specific step requested
    if args.step:
        if args.step < 1 or args.step > len(steps):
            print(f"Error: Step {args.step} out of range (1-{len(steps)})", file=sys.stderr)
            return 1
        steps_to_run = [steps[args.step - 1]]
        step_offset = args.step - 1
    else:
        steps_to_run = steps
        step_offset = 0
    
    # Execute steps
    failed = False
    for i, step in enumerate(steps_to_run):
        step_num = i + step_offset + 1
        step_name = step.get('name', f'Step {step_num}')
        command = step.get('command')
        
        print(f"\n[Step {step_num}] {step_name}")
        print("-" * 60)
        
        if not command:
            print("  (No command to execute)")
            continue
        
        print(f"  Command: {command}")
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.stdout:
                print(f"  Output:\n{result.stdout}")
            
            if result.stderr:
                print(f"  Stderr:\n{result.stderr}")
            
            if result.returncode != 0:
                print(f"  ✗ Failed with exit code {result.returncode}")
                failed = True
                if args.ci:
                    print("\nCI mode: Stopping on first failure")
                    return 1
            else:
                print(f"  ✓ Success")
        
        except subprocess.TimeoutExpired:
            print(f"  ✗ Timeout after 5 minutes")
            failed = True
            if args.ci:
                print("\nCI mode: Stopping on first failure")
                return 1
        
        except Exception as e:
            print(f"  ✗ Error: {e}")
            failed = True
            if args.ci:
                print("\nCI mode: Stopping on first failure")
                return 1
    
    print("\n" + "=" * 60)
    if failed:
        print("Tutorial execution completed with failures")
        return 1
    else:
        print("Tutorial execution completed successfully")
        return 0
