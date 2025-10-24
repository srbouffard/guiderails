# guiderails

**Write. Generate. Run.**

Generate readable tutorials from YAML and validate them in CI. Write once, generate Markdown documentation, and run tutorials in CI to ensure they stay up-to-date.

## Quick Start

### Installation

```bash
pip install -e .
```

### Create a Sample Tutorial

```bash
guiderun init my-tutorial
```

This creates `tutorials/my-tutorial.yaml` with a sample tutorial structure.

### Render Tutorial to Markdown

```bash
guiderun render tutorials/getting-started.yaml
```

Or save to a file:

```bash
guiderun render tutorials/getting-started.yaml -o docs/getting-started.md
```

### Execute Tutorial Steps

Run all steps in a tutorial:

```bash
guiderun exec tutorials/getting-started.yaml
```

Run a specific step:

```bash
guiderun exec tutorials/getting-started.yaml --step 2
```

Run in CI mode (exit on first failure):

```bash
guiderun exec tutorials/getting-started.yaml --ci
```

### Generate GitHub Actions Workflow

```bash
guiderun workflow tutorials/getting-started.yaml -o .github/workflows/validate-getting-started.yml
```

## Tutorial Format

Tutorials are defined in YAML with the following structure:

```yaml
title: My Tutorial Title
description: A brief description of what this tutorial covers.
steps:
  - name: Step name
    description: What this step does
    command: echo "bash command to execute"
    expected: Expected output or result
```

## Commands

- `guiderun init [name]` - Create a sample tutorial
- `guiderun render <tutorial.yaml>` - Convert tutorial to Markdown
- `guiderun exec <tutorial.yaml>` - Execute tutorial steps
- `guiderun workflow <tutorial.yaml>` - Generate GitHub Actions workflow

## License

MIT
