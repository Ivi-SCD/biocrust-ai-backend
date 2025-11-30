"""
Schemas comuns reutilizáveis.
"""

from datetime import datetime
from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

# TypeVar para respostas paginadas genéricas
T = TypeVar("T")


class BaseSchema(BaseModel):
    """Base schema com configuração comum."""
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class PaginationParams(BaseModel):
    """Parâmetros de paginação."""
    
    limit: int = Field(default=50, ge=1, le=500, description="Limite de itens por página")
    offset: int = Field(default=0, ge=0, description="Offset para paginação")


class PaginatedResponse(BaseModel, Generic[T]):
    """Resposta paginada genérica."""
    
    total: int = Field(..., description="Total de itens")
    items: List[T] = Field(..., description="Lista de itens")
    limit: int = Field(..., description="Limite aplicado")
    offset: int = Field(..., description="Offset aplicado")
    
    @property
    def has_more(self) -> bool:
        """Verifica se há mais itens."""
        return self.offset + len(self.items) < self.total


class TokenPayload(BaseModel):
    """Payload do token JWT."""
    
    sub: Optional[str] = None
    exp: Optional[int] = None
    user_id: Optional[str] = None
    role: str = "user"


class HealthCheck(BaseModel):
    """Resposta de health check."""
    
    status: str = Field(default="healthy", description="Status da aplicação")
    version: str = Field(..., description="Versão da aplicação")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    database: str = Field(default="healthy", description="Status do banco de dados")
    redis: str = Field(default="healthy", description="Status do Redis")
    celery: str = Field(default="healthy", description="Status do Celery")


class ErrorResponse(BaseModel):
    """Resposta de erro padronizada."""
    
    error: str = Field(..., description="Tipo do erro")
    message: str = Field(..., description="Mensagem de erro")
    details: Optional[Any] = Field(default=None, description="Detalhes adicionais")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = Field(default=None, description="ID da requisição")


class DateRangeParams(BaseModel):
    """Parâmetros de range de data."""
    
    start_date: Optional[datetime] = Field(default=None, description="Data inicial")
    end_date: Optional[datetime] = Field(default=None, description="Data final")


class SortParams(BaseModel):
    """Parâmetros de ordenação."""
    
    sort_by: Optional[str] = Field(default=None, description="Campo para ordenação")
    order: str = Field(default="desc", pattern="^(asc|desc)$", description="Ordem: asc ou desc")


class MessageResponse(BaseModel):
    """Resposta simples com mensagem."""
    
    message: str = Field(..., description="Mensagem")
    success: bool = Field(default=True, description="Se operação foi bem sucedida")
