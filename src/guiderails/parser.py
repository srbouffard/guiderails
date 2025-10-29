"""Markdown parser for GuideRails tutorials."""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup


@dataclass
class CodeBlock:
    """Represents a code block with execution metadata."""

    code: str
    language: str = "bash"
    mode: str = "exit"  # exit, contains, regex, exact
    expected: str = "0"  # Expected value based on mode
    timeout: int = 30
    working_dir: Optional[str] = None
    continue_on_error: bool = False
    line_number: int = 0


@dataclass
class Step:
    """Represents a tutorial step with heading and code blocks."""

    title: str
    content: str
    step_id: Optional[str] = None
    code_blocks: List[CodeBlock] = field(default_factory=list)
    line_number: int = 0
    content_parts: List[Any] = field(default_factory=list)  # Ordered list of strings and CodeBlocks


@dataclass
class Tutorial:
    """Represents a complete tutorial."""

    title: str
    source: str
    steps: List[Step] = field(default_factory=list)


class MarkdownParser:
    """Parser for Markdown tutorials with GuideRails annotations."""

    # Pattern to match attribute lists like {.gr-step #step1}
    ATTR_PATTERN = re.compile(r"\{([^}]+)\}")
    # Pattern to match class attributes
    CLASS_PATTERN = re.compile(r"\.([a-zA-Z0-9_-]+)")
    # Pattern to match id attributes
    ID_PATTERN = re.compile(r"#([a-zA-Z0-9_-]+)")
    # Pattern to match data attributes (with or without quotes)
    DATA_PATTERN = re.compile(r'data-([a-zA-Z0-9_-]+)=(?:(["\'])([^\2]+?)\2|([^\s}]+))')

    def parse_file(self, filepath: str) -> Tutorial:
        """Parse a Markdown file from filesystem."""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Tutorial file not found: {filepath}")

        content = path.read_text(encoding="utf-8")
        return self.parse_markdown(content, source=filepath)

    def parse_url(self, url: str) -> Tutorial:
        """Parse a Markdown tutorial from a URL.

        If the URL is an HTML page, look for <meta name="guiderails:source">
        to find the raw Markdown file URL.
        """
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "")

        # If it's HTML, look for meta tag
        if "text/html" in content_type:
            soup = BeautifulSoup(response.text, "html.parser")
            meta_tag = soup.find("meta", attrs={"name": "guiderails:source"})

            if meta_tag and meta_tag.get("content"):
                raw_url = meta_tag["content"]
                # Fetch the actual Markdown file
                md_response = requests.get(raw_url, timeout=30)
                md_response.raise_for_status()
                content = md_response.text
                return self.parse_markdown(content, source=raw_url)
            else:
                raise ValueError(
                    f"HTML page at {url} does not contain <meta name='guiderails:source'> tag"
                )
        else:
            # Assume it's Markdown
            content = response.text
            return self.parse_markdown(content, source=url)

    def parse_markdown(self, content: str, source: str = "<string>") -> Tutorial:
        """Parse Markdown content into a Tutorial object."""
        lines = content.split("\n")
        tutorial = Tutorial(title="", source=source)
        current_step = None
        in_code_block = False
        code_block_content = []
        code_block_attrs = {}
        code_block_lang = "bash"
        code_block_start_line = 0
        current_content_buffer = []  # Buffer for content before next code block

        for line_num, line in enumerate(lines, start=1):
            # Check for code block start/end
            if line.strip().startswith("```"):
                if not in_code_block:
                    # Starting a code block - flush content buffer first
                    if current_step and current_content_buffer:
                        content_text = "\n".join(current_content_buffer)
                        if content_text.strip():
                            current_step.content_parts.append(content_text)
                        current_content_buffer = []
                    
                    in_code_block = True
                    code_block_content = []
                    code_block_start_line = line_num

                    # Extract language and attributes
                    parts = line.strip()[3:].strip()
                    if parts:
                        # Split on whitespace to separate language from attributes
                        tokens = parts.split(None, 1)
                        code_block_lang = tokens[0] if tokens else "bash"

                        # Check for attributes
                        if len(tokens) > 1 and "{" in tokens[1]:
                            code_block_attrs = self._parse_attributes(tokens[1])
                        else:
                            code_block_attrs = {}
                    else:
                        code_block_lang = "bash"
                        code_block_attrs = {}
                else:
                    # Ending a code block
                    in_code_block = False

                    # Only process if it has .gr-run class
                    if "gr-run" in code_block_attrs.get("classes", []):
                        code = "\n".join(code_block_content)
                        code_block = self._create_code_block(
                            code, code_block_lang, code_block_attrs, code_block_start_line
                        )

                        if current_step:
                            current_step.code_blocks.append(code_block)
                            current_step.content_parts.append(code_block)

                    code_block_content = []
                    code_block_attrs = {}
                    code_block_lang = "bash"
                continue

            # If inside code block, collect content
            if in_code_block:
                code_block_content.append(line)
                continue

            # Check for headings with .gr-step
            if line.strip().startswith("#"):
                # Check next line for attributes (Markdown extended syntax)
                attrs = {}
                heading_text = line.strip().lstrip("#").strip()

                # Check if attributes are on the same line
                if "{" in line:
                    # Split heading and attributes
                    parts = line.split("{", 1)
                    heading_text = parts[0].strip().lstrip("#").strip()
                    attrs = self._parse_attributes("{" + parts[1])
                # Check if next line has attributes
                elif line_num < len(lines):
                    next_line = lines[line_num] if line_num < len(lines) else ""
                    if next_line.strip().startswith("{"):
                        attrs = self._parse_attributes(next_line.strip())

                # If this heading has .gr-step, start a new step
                if "gr-step" in attrs.get("classes", []):
                    # Save previous step with any remaining content
                    if current_step:
                        if current_content_buffer:
                            content_text = "\n".join(current_content_buffer)
                            if content_text.strip():
                                current_step.content_parts.append(content_text)
                            current_content_buffer = []
                        tutorial.steps.append(current_step)

                    current_step = Step(
                        title=heading_text,
                        content="",
                        step_id=attrs.get("id"),
                        line_number=line_num,
                    )
                elif not tutorial.title and line.strip().startswith("# "):
                    # Use first H1 as tutorial title
                    tutorial.title = heading_text
            elif current_step:
                # Add content to current step
                current_step.content += line + "\n"
                current_content_buffer.append(line)

        # Add final step with any remaining content
        if current_step:
            if current_content_buffer:
                content_text = "\n".join(current_content_buffer)
                if content_text.strip():
                    current_step.content_parts.append(content_text)
            tutorial.steps.append(current_step)

        if not tutorial.title:
            tutorial.title = "Untitled Tutorial"

        return tutorial

    def _parse_attributes(self, attr_string: str) -> Dict[str, Any]:
        """Parse attribute list like {.gr-step #step1 data-mode=exit}."""
        attrs = {"classes": [], "id": None, "data": {}}

        # Find all class attributes
        for match in self.CLASS_PATTERN.finditer(attr_string):
            attrs["classes"].append(match.group(1))

        # Find id attribute
        id_match = self.ID_PATTERN.search(attr_string)
        if id_match:
            attrs["id"] = id_match.group(1)

        # Find data attributes
        for match in self.DATA_PATTERN.finditer(attr_string):
            key = match.group(1)
            # Group 3 is quoted value, group 4 is unquoted value
            value = match.group(3) if match.group(3) is not None else match.group(4)
            attrs["data"][key] = value

        return attrs

    def _create_code_block(
        self, code: str, language: str, attrs: Dict[str, Any], line_number: int
    ) -> CodeBlock:
        """Create a CodeBlock from parsed attributes."""
        data = attrs.get("data", {})

        return CodeBlock(
            code=code.strip(),
            language=language,
            mode=data.get("mode", "exit"),
            expected=data.get("exp", data.get("expected", "0")),
            timeout=int(data.get("timeout", 30)),
            working_dir=data.get("workdir"),
            continue_on_error=data.get("continue-on-error", "").lower() == "true",
            line_number=line_number,
        )
