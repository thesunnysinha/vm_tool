from vm_tool.runner import SetupRunner

runner = SetupRunner(
    github_username='your_github_username', # e.g. username
    github_token='your_github_token', # e.g. token
    github_project_url='your_github_project_url' # e.g. https://github.com/username/repo
)

runner.run_setup()