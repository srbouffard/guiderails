"""GuideRails: Tutorials-as-Code framework for executable Markdown tutorials."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("guiderails")
except PackageNotFoundError:
    # Package not installed, likely in development
    __version__ = "0.0.0"
