---
description: Push code using the custom automation script
---

This workflow uses the project's custom script to commit, bump version, and push changes. It ensures consistent versioning and environment management.

1. Run the custom push script
   ```bash
   # Replace arguments as needed
   python3 codePushToGithub.py --branch main --message "Update via Agent"
   ```
