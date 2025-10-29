# Advanced GuideRails Features

This tutorial demonstrates advanced features of GuideRails.

## Step 1: Working Directory Test {.gr-step #workdir-test}

We can specify a custom working directory for commands.

```bash {.gr-run data-mode=exit data-exp=0 data-workdir=/tmp}
pwd | grep "/tmp"
```

## Step 2: Timeout Configuration {.gr-step #timeout-test}

Commands with custom timeout values:

```bash {.gr-run data-mode=exit data-exp=0 data-timeout=5}
sleep 1 && echo "Completed within timeout"
```

## Step 3: Continue on Error {.gr-step #continue-test}

Even if this command fails, we'll continue to the next one:

```bash {.gr-run data-mode=exit data-exp=0 data-continue-on-error=true}
false
```

This should still execute:

```bash {.gr-run data-mode=exit data-exp=0}
echo "Still running after error"
```

## Step 4: Multiple Languages {.gr-step #lang-test}

Python example (executed via shell):

```bash {.gr-run data-mode=contains data-exp="Hello from Python"}
python3 -c "print('Hello from Python')"
```

Shell script with exact match:

```bash {.gr-run data-mode=exact data-exp="exact match"}
echo "exact match"
```

## Conclusion

You've explored advanced GuideRails features!
