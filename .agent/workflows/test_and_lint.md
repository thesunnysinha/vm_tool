---
description: Run tests and linting for vm_tool
---

This workflow runs the project's tests and linting checks using the configured Makefile and Python tools.

1. Install dependencies (if needed) and run tests

   ```bash
   pip install -e ".[dev]"
   pytest
   ```

2. Run linting checks
   ```bash
   flake8 vm_tool
   black --check vm_tool
   ```
