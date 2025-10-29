# GuideRails

**Tutorials-as-Code**: Execute and validate Markdown tutorials to prevent documentation drift.

GuideRails enables you to write interactive, executable tutorials in Markdown that can be:
- ✅ Validated automatically in CI/CD pipelines
- 🚀 Run interactively in guided mode for step-by-step execution
- 📝 Authored with minimal, unobtrusive markup
- 🌐 Executed from local files or web URLs

## Features

- **Markdown-first**: Write tutorials in plain Markdown with minimal annotations
- **Interactive mode**: Step-by-step guided execution with user prompts
- **CI mode**: Automated validation for continuous integration
- **Flexible validation**: Support for exit codes, output matching, regex, and exact comparisons
- **Web support**: Load tutorials from URLs with meta tag discovery
- **Developer-friendly**: Simple attribute syntax for marking executable steps

## Installation

```bash
pip install guiderails
```

Or install from source:

```bash
git clone https://github.com/srbouffard/guiderails.git
cd guiderails
pip install -e .
```

## Quick Start

### 1. Write a Tutorial

Create a Markdown file with GuideRails annotations:

```markdown
# My First Tutorial

## Step 1: Setup {.gr-step #step1}

Let's create a test directory:

\```bash {.gr-run data-mode=exit data-exp=0}
mkdir -p /tmp/test
\```

## Step 2: Verify {.gr-step #step2}

Check that it was created:

\```bash {.gr-run data-mode=contains data-exp="/tmp/test"}
ls -d /tmp/test
\```
```

### 2. Run Interactively

```bash
guiderun exec --guided tutorial.md
```

### 3. Validate in CI

```bash
guiderun exec --ci tutorial.md
```

## Authoring Convention

### Marking Steps

Mark tutorial steps by adding `{.gr-step}` to headings:

```markdown
## Setup Environment {.gr-step #setup}
```

Optional: Add an ID with `#step-id` for reference.

### Marking Executable Code

Mark code blocks for execution with `{.gr-run}`:

```markdown
\```bash {.gr-run data-mode=exit data-exp=0}
echo "Hello, World!"
\```
```

### Validation Modes

GuideRails supports four validation modes:

#### 1. Exit Code (default)
```markdown
\```bash {.gr-run data-mode=exit data-exp=0}
test -f myfile.txt
\```
```

#### 2. Contains
```markdown
\```bash {.gr-run data-mode=contains data-exp="success"}
./my-script.sh
\```
```

#### 3. Regex
```markdown
\```bash {.gr-run data-mode=regex data-exp="Error: [0-9]+"}
./check-status.sh
\```
```

#### 4. Exact Match
```markdown
\```bash {.gr-run data-mode=exact data-exp="Hello, World!"}
echo "Hello, World!"
\```
```

### Additional Options

- **Timeout**: `data-timeout=60` (seconds, default: 30)
- **Working Directory**: `data-workdir=/tmp`
- **Continue on Error**: `data-continue-on-error=true`

Example:

```markdown
\```bash {.gr-run data-mode=exit data-exp=0 data-timeout=60 data-workdir=/tmp}
long-running-command
\```
```

## CLI Usage

### Commands

#### `guiderun exec`

Execute a tutorial:

```bash
guiderun exec [OPTIONS] TUTORIAL
```

**Options:**
- `--guided`: Run in interactive mode (shows each step, prompts for execution)
- `--ci`: Run in CI mode (non-interactive, fails fast)
- `--working-dir, -w PATH`: Set base working directory for execution

**Tutorial Sources:**
- Local file: `./tutorial.md`
- Direct URL: `https://example.com/tutorial.md`
- HTML page with meta tag: `https://example.com/tutorial.html`

### Examples

Run locally with interaction:
```bash
guiderun exec --guided examples/getting-started.md
```

Validate in CI:
```bash
guiderun exec --ci examples/getting-started.md
```

Run from URL:
```bash
guiderun exec --guided https://example.com/tutorial.md
```

From HTML with meta tag:
```bash
guiderun exec --guided https://example.com/tutorial.html
```

The HTML page should include:
```html
<meta name="guiderails:source" content="https://example.com/raw/tutorial.md">
```

## CI Integration

### GitHub Actions

Create `.github/workflows/validate-tutorials.yml`:

```yaml
name: Validate Tutorials

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  validate:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install GuideRails
      run: pip install guiderails
    
    - name: Validate tutorials
      run: |
        guiderun exec --ci docs/tutorial.md
```

## Examples

See the [examples](examples/) directory for sample tutorials:

- [getting-started.md](examples/getting-started.md) - Basic GuideRails tutorial
- [tutorial-page.html](examples/tutorial-page.html) - HTML page with meta tag

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/srbouffard/guiderails.git
cd guiderails

# Install in development mode
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest tests/ -v
```

### Code Formatting

```bash
black src/ tests/
ruff check src/
```

## Roadmap

- [ ] Support for reStructuredText (reST) tutorials
- [ ] Environment variable support
- [ ] Parallel execution of independent steps
- [ ] Step dependencies and conditional execution
- [ ] Plugin system for custom validators
- [ ] Web UI for tutorial execution and monitoring

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details.

## Acknowledgments

Inspired by the need for validated, executable documentation that stays in sync with code.
