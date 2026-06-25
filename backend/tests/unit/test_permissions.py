"""Unit tests for RBAC permission matrix."""
from app.core.permissions import Role, Permission, has_permission, get_permissions


def test_commissioner_has_all_critical_permissions():
    assert has_permission(Role.COMMISSIONER, Permission.ANALYTICS_VIEW_CITYWIDE)
    assert has_permission(Role.COMMISSIONER, Permission.AUDIT_VIEW_ALL)
    assert has_permission(Role.COMMISSIONER, Permission.BUDGET_APPROVE)
    assert has_permission(Role.COMMISSIONER, Permission.USER_DELETE)


def test_citizen_restricted_permissions():
    assert has_permission(Role.CITIZEN, Permission.COMPLAINT_CREATE)
    assert has_permission(Role.CITIZEN, Permission.COMPLAINT_VIEW_OWN)
    assert not has_permission(Role.CITIZEN, Permission.COMPLAINT_VIEW_ALL)
    assert not has_permission(Role.CITIZEN, Permission.ANALYTICS_VIEW_CITYWIDE)
    assert not has_permission(Role.CITIZEN, Permission.USER_DELETE)
    assert not has_permission(Role.CITIZEN, Permission.AUDIT_VIEW_ALL)


def test_engineer_has_operational_permissions():
    assert has_permission(Role.ENGINEER, Permission.COMPLAINT_CLOSE)
    assert has_permission(Role.ENGINEER, Permission.PROJECT_CREATE)
    assert has_permission(Role.ENGINEER, Permission.AI_OVERRIDE)
    assert not has_permission(Role.ENGINEER, Permission.USER_DELETE)
    assert not has_permission(Role.ENGINEER, Permission.BUDGET_APPROVE)


def test_coordinator_limited_scope():
    assert has_permission(Role.COORDINATOR, Permission.COMPLAINT_ASSIGN)
    assert not has_permission(Role.COORDINATOR, Permission.PROJECT_DELETE)
    assert not has_permission(Role.COORDINATOR, Permission.AI_RETRAIN)


def test_get_permissions_returns_set():
    perms = get_permissions(Role.COMMISSIONER)
    assert isinstance(perms, set)
    assert len(perms) > 20
