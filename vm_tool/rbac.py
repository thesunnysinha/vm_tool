"""Role-Based Access Control (RBAC) system."""

import logging
from typing import Dict, Set, Optional, List
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class Permission(Enum):
    """System permissions."""

    DEPLOY = "deploy"
    ROLLBACK = "rollback"
    VIEW_HISTORY = "view_history"
    MANAGE_CONFIG = "manage_config"
    MANAGE_SECRETS = "manage_secrets"
    MANAGE_USERS = "manage_users"
    VIEW_METRICS = "view_metrics"
    MANAGE_BACKUPS = "manage_backups"


class Role(Enum):
    """Predefined roles."""

    ADMIN = "admin"
    DEPLOYER = "deployer"
    VIEWER = "viewer"
    OPERATOR = "operator"


@dataclass
class User:
    """User with roles and permissions."""

    username: str
    roles: Set[Role]
    custom_permissions: Set[Permission]


class RBAC:
    """Role-Based Access Control manager."""

    # Default role permissions
    ROLE_PERMISSIONS = {
        Role.ADMIN: {
            Permission.DEPLOY,
            Permission.ROLLBACK,
            Permission.VIEW_HISTORY,
            Permission.MANAGE_CONFIG,
            Permission.MANAGE_SECRETS,
            Permission.MANAGE_USERS,
            Permission.VIEW_METRICS,
            Permission.MANAGE_BACKUPS,
        },
        Role.DEPLOYER: {
            Permission.DEPLOY,
            Permission.ROLLBACK,
            Permission.VIEW_HISTORY,
            Permission.VIEW_METRICS,
        },
        Role.OPERATOR: {
            Permission.DEPLOY,
            Permission.VIEW_HISTORY,
            Permission.VIEW_METRICS,
            Permission.MANAGE_BACKUPS,
        },
        Role.VIEWER: {Permission.VIEW_HISTORY, Permission.VIEW_METRICS},
    }

    def __init__(self):
        self.users: Dict[str, User] = {}

    def add_user(self, username: str, roles: List[Role]):
        """Add a user with roles."""
        self.users[username] = User(
            username=username, roles=set(roles), custom_permissions=set()
        )
        logger.info(f"User added: {username} with roles {[r.value for r in roles]}")

    def grant_permission(self, username: str, permission: Permission):
        """Grant custom permission to user."""
        if username in self.users:
            self.users[username].custom_permissions.add(permission)
            logger.info(f"Granted {permission.value} to {username}")

    def revoke_permission(self, username: str, permission: Permission):
        """Revoke custom permission from user."""
        if username in self.users:
            self.users[username].custom_permissions.discard(permission)
            logger.info(f"Revoked {permission.value} from {username}")

    def has_permission(self, username: str, permission: Permission) -> bool:
        """Check if user has permission."""
        if username not in self.users:
            return False

        user = self.users[username]

        # Check custom permissions
        if permission in user.custom_permissions:
            return True

        # Check role permissions
        for role in user.roles:
            if permission in self.ROLE_PERMISSIONS.get(role, set()):
                return True

        return False

    def require_permission(self, username: str, permission: Permission):
        """Require permission or raise exception."""
        if not self.has_permission(username, permission):
            from vm_tool.audit import get_audit_logger, AuditEventType

            audit = get_audit_logger()
            audit.log_event(
                AuditEventType.PERMISSION_DENIED,
                user=username,
                action=permission.value,
                resource="system",
                success=False,
            )

            raise PermissionError(
                f"User {username} does not have permission: {permission.value}"
            )


# Global RBAC instance
_rbac = None


def get_rbac() -> RBAC:
    """Get global RBAC instance."""
    global _rbac
    if _rbac is None:
        _rbac = RBAC()
    return _rbac
