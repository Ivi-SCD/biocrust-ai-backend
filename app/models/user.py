"""
Modelo de Usuário.

Autenticação e autorização de usuários do sistema.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDMixin, TimestampMixin


class UserRole(str, Enum):
    """Papéis de usuário no sistema."""
    ADMIN = "admin"
    MANAGER = "manager"
    OPERATOR = "operator"
    VIEWER = "viewer"


class User(Base, UUIDMixin, TimestampMixin):
    """
    Usuário do sistema.
    
    Armazena dados de autenticação e autorização.
    
    Attributes:
        id: UUID único do usuário
        email: E-mail (login)
        hashed_password: Senha criptografada
        full_name: Nome completo
        role: Papel no sistema
        is_active: Se está ativo
        last_login: Último login
    """
    
    __tablename__ = "users"
    
    # Autenticação
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    
    # Perfil
    full_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    
    # Autorização
    role: Mapped[str] = mapped_column(
        String(20),
        default=UserRole.VIEWER.value,
        nullable=False
    )
    
    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    
    # Tracking
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
