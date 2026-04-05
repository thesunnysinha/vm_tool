"""VM Tool: A comprehensive tool for setting up and managing virtual machines."""


def __getattr__(name):
    if name == "Config":
        from vm_tool.config import Config

        return Config
    if name in ("SetupRunner", "SetupRunnerConfig", "SSHConfig"):
        from vm_tool import runner

        return getattr(runner, name)
    raise AttributeError(f"module 'vm_tool' has no attribute {name!r}")


__all__ = [
    "Config",
    "SetupRunner",
    "SetupRunnerConfig",
    "SSHConfig",
]
