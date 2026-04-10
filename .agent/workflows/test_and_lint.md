---
description: Run tests and linting for vm_tool
---

This workflow runs the project's tests and linting checks using Poetry.

1. Install dependencies (if needed) and run tests

   ```bash
   poetry install --with dev
   poetry run pytest
   ```

2. Run linting checks
   ```bash
   poetry run flake8 vm_tool
   poetry run black --check vm_tool
   ```
