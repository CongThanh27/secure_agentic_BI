from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class RolePermission(Base):
    __tablename__ = "agent_role_permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    role_name: Mapped[str] = mapped_column(String(60), nullable=False)
    allowed_catalogs: Mapped[str] = mapped_column(Text, nullable=False)
    allowed_tables: Mapped[str] = mapped_column(Text, nullable=False)
    denied_tables: Mapped[str] = mapped_column(Text, nullable=False)
    can_export_file: Mapped[bool] = mapped_column(Boolean, nullable=False)
    max_row_limit: Mapped[int] = mapped_column(Integer, nullable=False)
    can_execute_ddl: Mapped[bool] = mapped_column(Boolean, nullable=False)
    can_access_pii: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_by: Mapped[str] = mapped_column(String(120), nullable=False)
