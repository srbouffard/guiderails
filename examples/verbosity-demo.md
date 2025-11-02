# Verbosity Levels Demo

This tutorial demonstrates how different verbosity levels affect GuideRails output.

## Step 1: Simple Command {.gr-step #step1}

Let's run a simple command:

```bash {.gr-run data-mode=exit data-exp=0}
echo "Hello, GuideRails!"
```

## Step 2: Variable Capture and Substitution {.gr-step #step2}

First, capture a value:

```bash {.gr-run data-mode=exit data-exp=0 data-out-var=MY_VALUE}
echo -n "World"
```

Then use it in another command:

```bash {.gr-run data-mode=contains data-exp="Hello, World"}
echo "Hello, ${MY_VALUE}"
```

## Step 3: Working Directory {.gr-step #step3}

Create and work in a temporary directory:

```bash {.gr-run data-mode=exit data-exp=0 data-workdir=/tmp}
mkdir -p guiderails-verbosity-demo && echo "Created directory"
```

## Step 4: Expected Value Check {.gr-step #step4}

Validate output contains expected text:

```bash {.gr-run data-mode=contains data-exp="success"}
echo "Operation completed with success"
```

## Step 5: Cleanup {.gr-step #step5}

Remove the demo directory:

```bash {.gr-run data-mode=exit data-exp=0 data-workdir=/tmp}
rm -rf guiderails-verbosity-demo && echo "Cleaned up"
```

## How to Test Different Verbosity Levels

Run this tutorial with different verbosity settings to see the differences:

### Quiet Mode
Minimal output, shows only essentials:
```bash
guiderun exec --ci --quiet examples/verbosity-demo.md
```

### Normal Mode (Default)
Balanced output with step banners and content:
```bash
guiderun exec --ci --verbosity=normal examples/verbosity-demo.md
```

### Verbose Mode
Detailed output with previews and timing:
```bash
guiderun exec --ci --verbose examples/verbosity-demo.md
```

### Debug Mode
Maximum detail with internal diagnostics:
```bash
guiderun exec --ci --debug examples/verbosity-demo.md
```

### Custom Toggle Examples

Quiet mode without showing commands:
```bash
guiderun exec --ci --quiet --no-show-commands examples/verbosity-demo.md
```

Normal mode with expected values shown:
```bash
guiderun exec --ci --show-expected examples/verbosity-demo.md
```
