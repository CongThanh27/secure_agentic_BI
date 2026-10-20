from typing import TypedDict

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import RolePermission


class RolePermissions(TypedDict):
    role_name: str
    allowed_catalogs: list[str]
    allowed_tables: list[str]
    denied_tables: list[str]
    can_export_file: bool
    max_row_limit: int
    can_execute_ddl: bool
    can_access_pii: bool
    created_at: str
    updated_by: str


def _split_policy_values(value: str) -> list[str]:
    return [item.strip() for item in value.split(";") if item.strip()]


def get_role_permissions(
    db_session: Session, role_name: str
) -> RolePermissions:
    """Load and normalize the RBAC policy for a role."""
    permission = db_session.scalars(
        select(RolePermission)
        .where(RolePermission.role_name == role_name)
        .order_by(RolePermission.id)
    ).first()
    if permission is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{role_name}' is not authorized",
        )

    return {
        "role_name": permission.role_name,
        "allowed_catalogs": _split_policy_values(permission.allowed_catalogs),
        "allowed_tables": _split_policy_values(permission.allowed_tables),
        "denied_tables": _split_policy_values(permission.denied_tables),
        "can_export_file": permission.can_export_file,
        "max_row_limit": permission.max_row_limit,
        "can_execute_ddl": permission.can_execute_ddl,
        "can_access_pii": permission.can_access_pii,
        "created_at": permission.created_at.isoformat(),
        "updated_by": permission.updated_by,
    }
