# File Generation and Output Capture Tutorial

This tutorial demonstrates GuideRails' file generation and output capture features.

## Step 1: Create a Python Script Using .gr-file {.gr-step #create-script}

Let's write a Python script directly from our tutorial using the `.gr-file` block.

```python {.gr-file data-path="gr-demo/hello.py" data-mode=write data-exec=true}
#!/usr/bin/env python3
import sys

def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "World"
    print(f"Hello, {name}!")
    print(f"Welcome to GuideRails file generation!", file=sys.stderr)
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

This creates an executable Python script at `gr-demo/hello.py`.

## Step 2: Run Script and Capture Output {.gr-step #capture-output}

Now let's run the script and capture its output to a variable.

```bash {.gr-run data-mode=exit data-exp=0 data-out-var=GREETING}
python3 gr-demo/hello.py GuideRails
```

The output has been captured to the `GREETING` variable for later use.

## Step 3: Verify Captured Output {.gr-step #verify-capture}

Let's verify that the variable was captured correctly by echoing it.

```bash {.gr-run data-mode=contains data-exp="Hello, GuideRails!"}
echo "${GREETING}"
```

The `${GREETING}` variable was substituted with the captured output.

## Step 4: Capture Exit Code {.gr-step #capture-exit-code}

Let's capture the exit code of a command into a variable.

```bash {.gr-run data-mode=exit data-exp=0 data-code-var=EXIT_STATUS}
python3 gr-demo/hello.py TestUser
```

The exit code is now stored in `EXIT_STATUS`.

## Step 5: Use Captured Exit Code {.gr-step #use-exit-code}

We can use the captured exit code in subsequent commands.

```bash {.gr-run data-mode=exact data-exp="Exit code was: 0"}
echo "Exit code was: ${EXIT_STATUS}"
```

## Step 6: Write Configuration with Template {.gr-step #template-config}

Let's create a configuration file using variable substitution with `data-template=shell`.

First, capture some configuration values:

```bash {.gr-run data-mode=exit data-exp=0 data-out-var=APP_VERSION}
echo -n "1.0.0"
```

```bash {.gr-run data-mode=exit data-exp=0 data-out-var=APP_VERSION}
echo -n "1.0.0"
```

```bash {.gr-run data-mode=exit data-exp=0 data-out-var=APP_PORT}
echo -n "8080"
```

Now write a config file using those variables:

```ini {.gr-file data-path="gr-demo/config.ini" data-mode=write data-template=shell}
[app]
version = ${APP_VERSION}
port = ${APP_PORT}
```

The variables `${APP_VERSION}` and `${APP_PORT}` are substituted when the file is written.

## Step 7: Verify Configuration File {.gr-step #verify-config}

Let's check that the configuration file was created correctly.

```bash {.gr-run data-mode=contains data-exp="version = 1.0.0"}
cat gr-demo/config.ini
```

## Step 8: Append to Log File {.gr-step #append-log}

We can append to files using `data-mode=append`.

```bash {.gr-file data-path="gr-demo/log.txt" data-mode=write}
Log entry 1: Tutorial started
```

```bash {.gr-file data-path="gr-demo/log.txt" data-mode=append}
Log entry 2: Configuration created
```

```bash {.gr-file data-path="gr-demo/log.txt" data-mode=append}
Log entry 3: All steps completed
```

Verify the log file:

```bash {.gr-run data-mode=contains data-exp="Log entry 2"}
cat gr-demo/log.txt
```

## Step 9: Write Output to File {.gr-step #output-to-file}

We can also write command output directly to a file using `data-out-file`.

```bash {.gr-run data-mode=exit data-exp=0 data-out-file="gr-demo/system-info.txt"}
echo "System: $(uname -s)"
echo "User: $(whoami)"
echo "Date: $(date)"
```

Verify the file was created:

```bash {.gr-run data-mode=contains data-exp="System:"}
cat gr-demo/system-info.txt
```

## Step 10: Create Script Once {.gr-step #once-flag}

The `data-once=true` flag prevents overwriting existing files.

```bash {.gr-file data-path="gr-demo/protected.txt" data-mode=write data-once=true}
This is the original content
```

This will skip writing if the file exists:

```bash {.gr-file data-path="gr-demo/protected.txt" data-mode=write data-once=true}
This would overwrite, but won't because once=true
```

Verify original content is preserved:

```bash {.gr-run data-mode=contains data-exp="original content"}
cat gr-demo/protected.txt
```

## Step 11: Create Shell Script with Variables {.gr-step #shell-script-template}

Let's create a shell script that uses our captured variables.

```bash {.gr-file data-path="gr-demo/status.sh" data-mode=write data-exec=true data-template=shell}
#!/bin/bash
echo "=== Application Status ==="
echo "Version: ${APP_VERSION}"
echo "Port: ${APP_PORT}"
echo "Last Exit: ${EXIT_STATUS}"
echo "Greeting: ${GREETING}"
```

Run the generated script:

```bash {.gr-run data-mode=contains data-exp="Version: 1.0.0"}
bash gr-demo/status.sh
```

## Step 12: Cleanup {.gr-step #cleanup}

Finally, let's clean up the demo directory.

```bash {.gr-run data-mode=exit data-exp=0}
rm -rf gr-demo
```

## Summary

You've learned how to:
- Create files with `.gr-file` blocks
- Make files executable with `data-exec=true`
- Append to files with `data-mode=append`
- Capture command output to variables with `data-out-var`
- Capture exit codes with `data-code-var`
- Write output directly to files with `data-out-file`
- Use variable substitution with `${VAR}` syntax
- Apply templates to file content with `data-template=shell`
- Protect files from overwriting with `data-once=true`
- Chain operations by passing data between steps

These features enable sophisticated tutorial workflows with file generation, configuration management, and step continuity!
