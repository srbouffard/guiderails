# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- **BREAKING CHANGE**: Renamed CLI tool from `guiderun` to `guiderails` for consistency with the project name
  - The CLI binary is now invoked as `guiderails` instead of `guiderun`
  - Updated all documentation, examples, and CI workflows to use `guiderails`
  - This aligns the CLI name with the project name for better discoverability and reduced confusion
  - Migration: Replace all `guiderun` commands with `guiderails` in your scripts and workflows

## [0.1.0] - 2024-01-XX

### Added
- Initial release of GuideRails
- Markdown-based tutorial execution and validation
- Interactive guided mode with step-by-step execution
- Non-interactive CI mode for automated validation
- Multiple validation modes: exit code, contains, regex, exact match
- File generation from code blocks with `.gr-file`
- Output and exit code capture with variables
- Variable substitution with `${VAR}` syntax
- Web URL support with meta tag discovery
- Configurable verbosity levels and output toggles
- GitHub Actions integration examples
- Comprehensive test suite with 69 tests
