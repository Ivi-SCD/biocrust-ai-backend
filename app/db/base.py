"""
Base class para modelos SQLAlchemy.

Define a classe base com campos comuns e mixins úteis.
"""

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    Classe base para todos os modelos SQLAlchemy.
    
    Todos os modelos herdam desta classe e ganham:
    - Tipagem automática
    - Representação string útil
    - Conversão para dicionário
    """
    
    def __repr__(self) -> str:
        """Representação string do modelo."""
        class_name = self.__class__.__name__
        attrs = ", ".join(
            f"{k}={v!r}"
            for k, v in self.__dict__.items()
            if not k.startswith("_")
        )
        return f"{class_name}({attrs})"
    
    def to_dict(self) -> dict[str, Any]:
        """
        Converte modelo para dicionário.
        
        Returns:
            dict: Dicionário com atributos do modelo
        """
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }


class TimestampMixin:
    """
    Mixin que adiciona campos de timestamp.
    
    Adiciona:
    - created_at: Data de criação (automático)
    - updated_at: Data de última atualização (automático)
    """
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )


class UUIDMixin:
    """
    Mixin que adiciona campo UUID como primary key.
    """
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid4()),
        nullable=False
    )
