"""External integrations: notifications, webhooks, plugins, benchmarking."""

from vm_tool.integrations.notifications import EmailNotifier
from vm_tool.integrations.webhooks import WebhookSender
from vm_tool.integrations.plugins import Plugin, PluginManager
from vm_tool.integrations.benchmarking import PerformanceBenchmark

__all__ = [
    "EmailNotifier",
    "WebhookSender",
    "Plugin",
    "PluginManager",
    "PerformanceBenchmark",
]
