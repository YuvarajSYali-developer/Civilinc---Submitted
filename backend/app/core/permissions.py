"""
CivilInc RBAC Permission Matrix
Role-Based Access Control with granular permissions.
"""
from enum import Enum
from typing import Dict, Set


class Role(str, Enum):
    COMMISSIONER = "commissioner"
    ENGINEER = "engineer"
    COORDINATOR = "coordinator"
    CITIZEN = "citizen"


class Permission(str, Enum):
    # ─── User Management ────────────────────────────────────────────────────────
    USER_VIEW_ALL = "user:view_all"
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_VIEW_OWN = "user:view_own"
    USER_UPDATE_OWN = "user:update_own"

    # ─── Department Management ──────────────────────────────────────────────────
    DEPT_VIEW_ALL = "department:view_all"
    DEPT_CREATE = "department:create"
    DEPT_UPDATE = "department:update"
    DEPT_DELETE = "department:delete"
    DEPT_VIEW_OWN = "department:view_own"

    # ─── Project Management ─────────────────────────────────────────────────────
    PROJECT_VIEW_ALL = "project:view_all"
    PROJECT_CREATE = "project:create"
    PROJECT_UPDATE_ANY = "project:update_any"
    PROJECT_UPDATE_OWN = "project:update_own"
    PROJECT_DELETE = "project:delete"
    PROJECT_VIEW_PUBLIC = "project:view_public"
    PROJECT_ASSIGN = "project:assign"
    PROJECT_APPROVE = "project:approve"

    # ─── Complaint Management ───────────────────────────────────────────────────
    COMPLAINT_VIEW_ALL = "complaint:view_all"
    COMPLAINT_CREATE = "complaint:create"
    COMPLAINT_UPDATE_ANY = "complaint:update_any"
    COMPLAINT_UPDATE_OWN = "complaint:update_own"
    COMPLAINT_DELETE = "complaint:delete"
    COMPLAINT_ASSIGN = "complaint:assign"
    COMPLAINT_CLOSE = "complaint:close"
    COMPLAINT_VIEW_OWN = "complaint:view_own"
    COMPLAINT_ESCALATE = "complaint:escalate"

    # ─── Forum ──────────────────────────────────────────────────────────────────
    FORUM_VIEW = "forum:view"
    FORUM_CREATE_THREAD = "forum:create_thread"
    FORUM_COMMENT = "forum:comment"
    FORUM_MODERATE = "forum:moderate"
    FORUM_DELETE_ANY = "forum:delete_any"
    FORUM_PIN_THREAD = "forum:pin_thread"

    # ─── Analytics & Reports ────────────────────────────────────────────────────
    ANALYTICS_VIEW_CITYWIDE = "analytics:view_citywide"
    ANALYTICS_VIEW_DEPARTMENT = "analytics:view_department"
    ANALYTICS_EXPORT = "analytics:export"
    REPORT_GENERATE = "report:generate"
    REPORT_VIEW_ALL = "report:view_all"

    # ─── AI Services ────────────────────────────────────────────────────────────
    AI_PREDICT = "ai:predict"
    AI_VIEW_INSIGHTS = "ai:view_insights"
    AI_OVERRIDE = "ai:override"
    AI_RETRAIN = "ai:retrain"

    # ─── GIS ────────────────────────────────────────────────────────────────────
    GIS_VIEW_ALL_LAYERS = "gis:view_all_layers"
    GIS_VIEW_PUBLIC = "gis:view_public"
    GIS_EDIT_LAYERS = "gis:edit_layers"

    # ─── Notifications ──────────────────────────────────────────────────────────
    NOTIFICATION_VIEW_OWN = "notification:view_own"
    NOTIFICATION_BROADCAST = "notification:broadcast"

    # ─── Audit ──────────────────────────────────────────────────────────────────
    AUDIT_VIEW_ALL = "audit:view_all"
    AUDIT_VIEW_DEPARTMENT = "audit:view_department"

    # ─── Budget ─────────────────────────────────────────────────────────────────
    BUDGET_VIEW_ALL = "budget:view_all"
    BUDGET_VIEW_OWN = "budget:view_own"
    BUDGET_CREATE = "budget:create"
    BUDGET_APPROVE = "budget:approve"
    BUDGET_UPDATE = "budget:update"


# ─── Role → Permission Mapping ──────────────────────────────────────────────────
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.COMMISSIONER: {
        # Full visibility
        Permission.USER_VIEW_ALL, Permission.USER_CREATE, Permission.USER_UPDATE,
        Permission.USER_DELETE, Permission.USER_VIEW_OWN, Permission.USER_UPDATE_OWN,
        Permission.DEPT_VIEW_ALL, Permission.DEPT_CREATE, Permission.DEPT_UPDATE,
        Permission.DEPT_DELETE,
        Permission.PROJECT_VIEW_ALL, Permission.PROJECT_CREATE,
        Permission.PROJECT_UPDATE_ANY, Permission.PROJECT_DELETE,
        Permission.PROJECT_ASSIGN, Permission.PROJECT_APPROVE,
        Permission.COMPLAINT_VIEW_ALL, Permission.COMPLAINT_UPDATE_ANY,
        Permission.COMPLAINT_ASSIGN, Permission.COMPLAINT_CLOSE,
        Permission.COMPLAINT_ESCALATE,
        Permission.FORUM_VIEW, Permission.FORUM_MODERATE, Permission.FORUM_DELETE_ANY,
        Permission.FORUM_PIN_THREAD, Permission.FORUM_CREATE_THREAD, Permission.FORUM_COMMENT,
        Permission.ANALYTICS_VIEW_CITYWIDE, Permission.ANALYTICS_VIEW_DEPARTMENT,
        Permission.ANALYTICS_EXPORT, Permission.REPORT_GENERATE, Permission.REPORT_VIEW_ALL,
        Permission.AI_PREDICT, Permission.AI_VIEW_INSIGHTS, Permission.AI_OVERRIDE,
        Permission.AI_RETRAIN,
        Permission.GIS_VIEW_ALL_LAYERS, Permission.GIS_EDIT_LAYERS,
        Permission.NOTIFICATION_VIEW_OWN, Permission.NOTIFICATION_BROADCAST,
        Permission.AUDIT_VIEW_ALL,
        Permission.BUDGET_VIEW_ALL, Permission.BUDGET_CREATE, Permission.BUDGET_APPROVE,
        Permission.BUDGET_UPDATE,
    },
    Role.ENGINEER: {
        Permission.USER_VIEW_OWN, Permission.USER_UPDATE_OWN,
        Permission.DEPT_VIEW_OWN, Permission.DEPT_VIEW_ALL,
        Permission.PROJECT_VIEW_ALL, Permission.PROJECT_CREATE,
        Permission.PROJECT_UPDATE_OWN, Permission.PROJECT_ASSIGN,
        Permission.COMPLAINT_VIEW_ALL, Permission.COMPLAINT_UPDATE_ANY,
        Permission.COMPLAINT_ASSIGN, Permission.COMPLAINT_CLOSE,
        Permission.COMPLAINT_ESCALATE,
        Permission.FORUM_VIEW, Permission.FORUM_CREATE_THREAD, Permission.FORUM_COMMENT,
        Permission.ANALYTICS_VIEW_DEPARTMENT, Permission.ANALYTICS_EXPORT,
        Permission.REPORT_GENERATE,
        Permission.AI_PREDICT, Permission.AI_VIEW_INSIGHTS, Permission.AI_OVERRIDE,
        Permission.GIS_VIEW_ALL_LAYERS,
        Permission.NOTIFICATION_VIEW_OWN,
        Permission.AUDIT_VIEW_DEPARTMENT,
        Permission.BUDGET_VIEW_OWN, Permission.BUDGET_UPDATE,
    },
    Role.COORDINATOR: {
        Permission.USER_VIEW_OWN, Permission.USER_UPDATE_OWN,
        Permission.DEPT_VIEW_OWN,
        Permission.PROJECT_VIEW_ALL, Permission.PROJECT_UPDATE_OWN,
        Permission.COMPLAINT_VIEW_ALL, Permission.COMPLAINT_UPDATE_ANY,
        Permission.COMPLAINT_ASSIGN, Permission.COMPLAINT_CLOSE,
        Permission.FORUM_VIEW, Permission.FORUM_CREATE_THREAD, Permission.FORUM_COMMENT,
        Permission.ANALYTICS_VIEW_DEPARTMENT,
        Permission.AI_PREDICT, Permission.AI_VIEW_INSIGHTS,
        Permission.GIS_VIEW_ALL_LAYERS,
        Permission.NOTIFICATION_VIEW_OWN,
        Permission.BUDGET_VIEW_OWN,
    },
    Role.CITIZEN: {
        Permission.USER_VIEW_OWN, Permission.USER_UPDATE_OWN,
        Permission.PROJECT_VIEW_PUBLIC,
        Permission.COMPLAINT_CREATE, Permission.COMPLAINT_VIEW_OWN,
        Permission.COMPLAINT_UPDATE_OWN,
        Permission.FORUM_VIEW, Permission.FORUM_CREATE_THREAD, Permission.FORUM_COMMENT,
        Permission.GIS_VIEW_PUBLIC,
        Permission.NOTIFICATION_VIEW_OWN,
    },
}


def has_permission(role: Role, permission: Permission) -> bool:
    """Check if a role has a specific permission."""
    return permission in ROLE_PERMISSIONS.get(role, set())


def get_permissions(role: Role) -> Set[Permission]:
    """Get all permissions for a role."""
    return ROLE_PERMISSIONS.get(role, set())
