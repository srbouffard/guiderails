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
- **File generation**: Create files directly from code blocks with `.gr-file`
- **Output capture**: Store command output and exit codes in variables
- **Variable substitution**: Use `${VAR}` syntax for continuity across steps
- **Web support**: Load tutorials from URLs with meta tag discovery
- **Developer-friendly**: Simple attribute syntax for marking executable steps
- **Safe by default**: Sandboxed file operations within working directory

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

### File-Generating Blocks

Create files directly from your tutorial using `.gr-file` blocks:

```markdown
\```bash {.gr-file data-path="script.sh" data-mode=write data-exec=true}
#!/bin/bash
echo "Hello from GuideRails!"
\```
```

**Attributes:**
- `data-path`: Target file path (relative to working directory)
- `data-mode`: `write` (default, overwrite) or `append`
- `data-exec`: `true` to make file executable (chmod +x)
- `data-template`: `none` (default) or `shell` (enables ${VAR} substitution)
- `data-once`: `true` to skip if file already exists

**Example with variable substitution:**
```markdown
\```python {.gr-file data-path="config.py" data-template=shell}
VERSION = "${APP_VERSION}"
PORT = ${PORT}
\```
```

### Output and Exit Code Capture

Capture command output and exit codes for use in later steps:

```markdown
\```bash {.gr-run data-out-var=GREETING data-code-var=EXIT_STATUS}
echo "Hello, World!"
exit 0
\```
```

**Capture Options:**
- `data-out-var=VARNAME`: Store combined stdout/stderr in a variable
- `data-out-file=path`: Write stdout to a file
- `data-code-var=VARNAME`: Store exit code in a variable

### Variable Substitution

Use captured variables in subsequent blocks with `${VAR}` syntax:

```markdown
\```bash {.gr-run data-out-var=NAME}
echo -n "Alice"
\```

\```bash {.gr-run data-mode=contains data-exp="Hello, Alice"}
echo "Hello, ${NAME}"
\```
```

Variables are automatically substituted when:
- Running `.gr-run` code blocks (command is substituted before execution)
- Writing `.gr-file` blocks with `data-template=shell`

**Safety:** File paths are sandboxed to the working directory by default. Absolute paths and `..` traversal are rejected unless explicitly allowed with CLI flags.

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

**Basic Options:**
- `--guided`: Run in interactive mode (shows each step, prompts for execution)
- `--ci`: Run in CI mode (non-interactive, fails fast, defaults to quiet output)
- `--working-dir, -w PATH`: Set base working directory for execution

**Verbosity Options:**
- `--verbosity LEVEL`: Set verbosity level (`quiet`, `normal`, `verbose`, `debug`)
- `--quiet, -q`: Quiet mode (minimal output, alias for `--verbosity=quiet`)
- `--verbose, -v`: Increase verbosity (`-v` for verbose, `-vv` or `-vvv` for debug)
- `--debug`: Debug mode (maximum verbosity, alias for `--verbosity=debug`)

**Output Toggle Options:**
- `--show-commands / --no-show-commands`: Show/hide commands being executed
- `--show-substituted / --no-show-substituted`: Show/hide variable substitution hints
- `--show-expected / --no-show-expected`: Show/hide expected validation values
- `--show-captured / --no-show-captured`: Show/hide captured variable information
- `--timestamps / --no-timestamps`: Show/hide execution timestamps
- `--step-banners / --no-step-banners`: Show/hide step banners and boxes
- `--previews / --no-previews`: Show/hide command previews and extra details

**Output Format:**
- `--output FORMAT`: Output format (`text` or `jsonl`)

**Verbosity Level Behaviors:**

- **quiet**: Shows only step titles, commands (if `--show-commands`), command output, and PASS/FAIL status. Minimal decoration.
- **normal** (default): Adds step banners, content boxes, and basic execution results.
- **verbose**: Adds command previews, substitution details, timing information, and working directory.
- **debug**: Adds internal diagnostics, parser events, and variable table state.

**Tutorial Sources:**
- Local file: `./tutorial.md`
- Direct URL: `https://example.com/tutorial.md`
- HTML page with meta tag: `https://example.com/tutorial.html`

### Examples

Run locally with interaction:
```bash
guiderun exec --guided examples/getting-started.md
```

Validate in CI (defaults to quiet output):
```bash
guiderun exec --ci examples/getting-started.md
```

Run with verbose output:
```bash
guiderun exec --ci --verbose examples/getting-started.md
```

Run in quiet mode with no command display:
```bash
guiderun exec --ci --quiet --no-show-commands examples/getting-started.md
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

### Configuration

GuideRails supports configuration through multiple sources with the following precedence:

**1. Command-line flags** (highest priority)  
**2. Environment variables**  
**3. Configuration file** (`guiderails.yml`)  
**4. Built-in defaults** (lowest priority)

#### Environment Variables

```bash
# Verbosity level
export GUIDERAILS_VERBOSITY=quiet|normal|verbose|debug

# Output toggles
export GUIDERAILS_SHOW_COMMANDS=true|false
export GUIDERAILS_SHOW_SUBSTITUTED=true|false
export GUIDERAILS_SHOW_EXPECTED=true|false
export GUIDERAILS_SHOW_CAPTURED=true|false
export GUIDERAILS_TIMESTAMPS=true|false
export GUIDERAILS_STEP_BANNERS=true|false
export GUIDERAILS_PREVIEWS=true|false
```

#### Configuration File

Create a `guiderails.yml` file in your project root:

```yaml
# Verbosity level (quiet, normal, verbose, debug)
verbosity: normal

# Output toggles
show_commands: true
show_substituted: false
show_expected: true
show_captured: true
show_timestamps: false
show_step_banners: true
show_previews: false
```

GuideRails will search for `guiderails.yml` in the current directory and parent directories.

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
- [file-generation-and-capture.md](examples/file-generation-and-capture.md) - File generation, output capture, and variable substitution
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
