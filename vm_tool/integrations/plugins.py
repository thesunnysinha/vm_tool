"""Plugin system for extensibility."""

import logging
from typing import Dict, Any, List
from pathlib import Path

logger = logging.getLogger(__name__)


class Plugin:
    """Base plugin class."""

    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version

    def on_deployment_start(self, context: Dict[str, Any]):
        """Called before deployment starts."""
        pass

    def on_deployment_success(self, context: Dict[str, Any]):
        """Called after successful deployment."""
        pass

    def on_deployment_failure(self, context: Dict[str, Any]):
        """Called after failed deployment."""
        pass


class PluginManager:
    """Manage plugins."""

    def __init__(self, plugin_dir: str = ".vm_tool/plugins"):
        self.plugin_dir = Path(plugin_dir)
        self.plugins: List[Plugin] = []

    def load_plugin(self, plugin_path: str):
        """Load a plugin from file."""
        raise NotImplementedError(
            "Plugin loading is not yet implemented. "
            "Use register_plugin() to register plugins programmatically."
        )

    def register_plugin(self, plugin: Plugin):
        """Register a plugin."""
        self.plugins.append(plugin)
        logger.info(f"Registered plugin: {plugin.name} v{plugin.version}")

    def trigger_hook(self, hook_name: str, context: Dict[str, Any]):
        """Trigger plugin hooks."""
        for plugin in self.plugins:
            try:
                hook = getattr(plugin, hook_name, None)
                if hook and callable(hook):
                    hook(context)
            except Exception as e:
                logger.error(f"Plugin {plugin.name} hook {hook_name} failed: {e}")
