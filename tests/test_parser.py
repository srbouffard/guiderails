"""Tests for the Markdown parser."""

import pytest
from guiderails.parser import MarkdownParser, Tutorial, Step, CodeBlock


def test_parse_simple_tutorial():
    """Test parsing a simple tutorial."""
    markdown = """# Test Tutorial

## Step 1 {.gr-step #step1}

This is step 1.

```bash {.gr-run data-mode=exit data-exp=0}
echo "hello"
```

## Step 2 {.gr-step}

This is step 2.

```bash {.gr-run data-mode=contains data-exp="world"}
echo "hello world"
```
"""

    parser = MarkdownParser()
    tutorial = parser.parse_markdown(markdown, source="test.md")

    assert tutorial.title == "Test Tutorial"
    assert len(tutorial.steps) == 2

    # Check first step
    step1 = tutorial.steps[0]
    assert step1.title == "Step 1"
    assert step1.step_id == "step1"
    assert len(step1.code_blocks) == 1
    assert step1.code_blocks[0].code == 'echo "hello"'
    assert step1.code_blocks[0].mode == "exit"
    assert step1.code_blocks[0].expected == "0"

    # Check second step
    step2 = tutorial.steps[1]
    assert step2.title == "Step 2"
    assert step2.step_id is None
    assert len(step2.code_blocks) == 1
    assert step2.code_blocks[0].code == 'echo "hello world"'
    assert step2.code_blocks[0].mode == "contains"
    assert step2.code_blocks[0].expected == "world"


def test_parse_multiple_code_blocks():
    """Test parsing multiple code blocks in a step."""
    markdown = """# Tutorial

## Step {.gr-step}

First block:

```bash {.gr-run}
echo "first"
```

Second block:

```bash {.gr-run data-mode=regex data-exp="second"}
echo "second"
```
"""

    parser = MarkdownParser()
    tutorial = parser.parse_markdown(markdown)

    assert len(tutorial.steps) == 1
    assert len(tutorial.steps[0].code_blocks) == 2
    assert tutorial.steps[0].code_blocks[0].code == 'echo "first"'
    assert tutorial.steps[0].code_blocks[1].code == 'echo "second"'
    assert tutorial.steps[0].code_blocks[1].mode == "regex"


def test_parse_without_gr_run():
    """Test that code blocks without .gr-run are ignored."""
    markdown = """# Tutorial

## Step {.gr-step}

This code block should be ignored:

```bash
echo "not executable"
```

This one should be included:

```bash {.gr-run}
echo "executable"
```
"""

    parser = MarkdownParser()
    tutorial = parser.parse_markdown(markdown)

    assert len(tutorial.steps) == 1
    assert len(tutorial.steps[0].code_blocks) == 1
    assert tutorial.steps[0].code_blocks[0].code == 'echo "executable"'


def test_parse_different_languages():
    """Test parsing code blocks with different languages."""
    markdown = """# Tutorial

## Step {.gr-step}

```python {.gr-run}
print("hello")
```

```javascript {.gr-run}
console.log("world")
```
"""

    parser = MarkdownParser()
    tutorial = parser.parse_markdown(markdown)

    assert len(tutorial.steps[0].code_blocks) == 2
    assert tutorial.steps[0].code_blocks[0].language == "python"
    assert tutorial.steps[0].code_blocks[1].language == "javascript"


def test_parse_custom_timeout():
    """Test parsing custom timeout."""
    markdown = """# Tutorial

## Step {.gr-step}

```bash {.gr-run data-timeout=60}
sleep 1
```
"""

    parser = MarkdownParser()
    tutorial = parser.parse_markdown(markdown)

    assert tutorial.steps[0].code_blocks[0].timeout == 60


def test_parse_continue_on_error():
    """Test parsing continue-on-error flag."""
    markdown = """# Tutorial

## Step {.gr-step}

```bash {.gr-run data-continue-on-error=true}
false
```
"""

    parser = MarkdownParser()
    tutorial = parser.parse_markdown(markdown)

    assert tutorial.steps[0].code_blocks[0].continue_on_error is True


def test_parse_working_dir():
    """Test parsing working directory."""
    markdown = """# Tutorial

## Step {.gr-step}

```bash {.gr-run data-workdir=/tmp}
pwd
```
"""

    parser = MarkdownParser()
    tutorial = parser.parse_markdown(markdown)

    assert tutorial.steps[0].code_blocks[0].working_dir == "/tmp"


def test_empty_tutorial():
    """Test parsing an empty tutorial."""
    markdown = """# Empty Tutorial

No steps here.
"""

    parser = MarkdownParser()
    tutorial = parser.parse_markdown(markdown)

    assert tutorial.title == "Empty Tutorial"
    assert len(tutorial.steps) == 0


def test_parse_attributes():
    """Test parsing various attribute formats."""
    parser = MarkdownParser()

    # Test with classes and id
    attrs = parser._parse_attributes("{.gr-step .another-class #myid}")
    assert "gr-step" in attrs["classes"]
    assert "another-class" in attrs["classes"]
    assert attrs["id"] == "myid"

    # Test with data attributes
    attrs = parser._parse_attributes("{.gr-run data-mode=exit data-exp=0}")
    assert "gr-run" in attrs["classes"]
    assert attrs["data"]["mode"] == "exit"
    assert attrs["data"]["exp"] == "0"

    # Test with quoted values
    attrs = parser._parse_attributes('{.gr-run data-exp="hello world"}')
    assert attrs["data"]["exp"] == "hello world"


def test_parse_exact_mode():
    """Test parsing exact match mode."""
    markdown = """# Tutorial

## Step {.gr-step}

```bash {.gr-run data-mode=exact data-exp="hello"}
echo "hello"
```
"""

    parser = MarkdownParser()
    tutorial = parser.parse_markdown(markdown)

    block = tutorial.steps[0].code_blocks[0]
    assert block.mode == "exact"
    assert block.expected == "hello"
