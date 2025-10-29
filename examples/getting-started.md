# Getting Started with GuideRails

Welcome to GuideRails! This tutorial demonstrates how to write executable tutorials using Markdown.

## Step 1: Create a Test Directory {.gr-step #step1}

Let's start by creating a test directory and navigating into it.

```bash {.gr-run data-mode=exit data-exp=0}
mkdir -p /tmp/guiderails-demo
```

This creates a directory where we'll do our work.

## Step 2: Create a Simple File {.gr-step #step2}

Now we'll create a file with some content.

```bash {.gr-run data-mode=exit data-exp=0}
echo "Hello from GuideRails!" > /tmp/guiderails-demo/hello.txt
```

Let's verify the file was created:

```bash {.gr-run data-mode=exit data-exp=0}
ls /tmp/guiderails-demo/hello.txt
```

## Step 3: Validate File Content {.gr-step #step3}

We can also validate that the file contains the expected text.

```bash {.gr-run data-mode=contains data-exp="Hello from GuideRails!"}
cat /tmp/guiderails-demo/hello.txt
```

## Step 4: Test Exit Codes {.gr-step #step4}

Let's demonstrate different validation modes. First, a successful command:

```bash {.gr-run data-mode=exit data-exp=0}
test -f /tmp/guiderails-demo/hello.txt
```

Now let's test that a non-existent file returns the expected error:

```bash {.gr-run data-mode=exit data-exp=1}
test -f /tmp/guiderails-demo/nonexistent.txt
```

## Step 5: Regex Validation {.gr-step #step5}

We can use regex patterns to validate output. Let's check the file with a regex:

```bash {.gr-run data-mode=regex data-exp="Hello.*GuideRails"}
cat /tmp/guiderails-demo/hello.txt
```

## Step 6: Cleanup {.gr-step #step6}

Finally, let's clean up our test directory.

```bash {.gr-run data-mode=exit data-exp=0}
rm -rf /tmp/guiderails-demo
```

## Conclusion

You've completed the GuideRails tutorial! You learned how to:

- Use `.gr-step` to mark tutorial steps
- Use `.gr-run` to mark executable code blocks
- Validate commands with different modes: exit codes, contains, regex
- Write tutorials that can be executed and validated automatically

For more information, check out the documentation!
