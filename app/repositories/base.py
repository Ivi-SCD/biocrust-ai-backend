"""
Repositório base com operações CRUD genéricas.
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar
from uuid import uuid4

from sqlalchemy import select, func, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Repositório base com operações CRUD genéricas.
    
    Attributes:
        model: Classe do modelo SQLAlchemy
        db: Sessão assíncrona do banco de dados
    """
    
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        """
        Inicializa o repositório.
        
        Args:
            model: Classe do modelo
            db: Sessão do banco de dados
        """
        self.model = model
        self.db = db
    
    async def get_by_id(self, id: str) -> Optional[ModelType]:
        """
        Busca entidade por ID.
        
        Args:
            id: UUID da entidade
            
        Returns:
            Entidade encontrada ou None
        """
        query = select(self.model).where(self.model.id == id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters
    ) -> List[ModelType]:
        """
        Lista todas as entidades com paginação.
        
        Args:
            skip: Offset para paginação
            limit: Limite de resultados
            **filters: Filtros adicionais
            
        Returns:
            Lista de entidades
        """
        query = select(self.model)
        
        # Aplicar filtros
        for key, value in filters.items():
            if hasattr(self.model, key) and value is not None:
                query = query.where(getattr(self.model, key) == value)
        
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def count(self, **filters) -> int:
        """
        Conta entidades com filtros opcionais.
        
        Args:
            **filters: Filtros para aplicar
            
        Returns:
            Número de entidades
        """
        query = select(func.count(self.model.id))
        
        for key, value in filters.items():
            if hasattr(self.model, key) and value is not None:
                query = query.where(getattr(self.model, key) == value)
        
        result = await self.db.execute(query)
        return result.scalar() or 0
    
    async def create(self, data: Dict[str, Any]) -> ModelType:
        """
        Cria nova entidade.
        
        Args:
            data: Dados para criação
            
        Returns:
            Entidade criada
        """
        if "id" not in data:
            data["id"] = str(uuid4())
        
        entity = self.model(**data)
        self.db.add(entity)
        await self.db.commit()
        await self.db.refresh(entity)
        return entity
    
    async def create_many(self, data_list: List[Dict[str, Any]]) -> List[ModelType]:
        """
        Cria múltiplas entidades.
        
        Args:
            data_list: Lista de dados para criação
            
        Returns:
            Lista de entidades criadas
        """
        entities = []
        for data in data_list:
            if "id" not in data:
                data["id"] = str(uuid4())
            entity = self.model(**data)
            self.db.add(entity)
            entities.append(entity)
        
        await self.db.commit()
        
        for entity in entities:
            await self.db.refresh(entity)
        
        return entities
    
    async def update(self, id: str, data: Dict[str, Any]) -> Optional[ModelType]:
        """
        Atualiza entidade existente.
        
        Args:
            id: UUID da entidade
            data: Dados para atualização
            
        Returns:
            Entidade atualizada ou None
        """
        entity = await self.get_by_id(id)
        if entity is None:
            return None
        
        for key, value in data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        
        await self.db.commit()
        await self.db.refresh(entity)
        return entity
    
    async def delete(self, id: str) -> bool:
        """
        Remove entidade.
        
        Args:
            id: UUID da entidade
            
        Returns:
            True se removido, False se não encontrado
        """
        entity = await self.get_by_id(id)
        if entity is None:
            return False
        
        await self.db.delete(entity)
        await self.db.commit()
        return True
    
    async def exists(self, id: str) -> bool:
        """
        Verifica se entidade existe.
        
        Args:
            id: UUID da entidade
            
        Returns:
            True se existe
        """
        query = select(func.count(self.model.id)).where(self.model.id == id)
        result = await self.db.execute(query)
        return (result.scalar() or 0) > 0
