"""
Serviço de Cache com Redis.
"""

import json
from datetime import timedelta
from typing import Any, Optional, TypeVar, Type

import redis.asyncio as redis
import structlog

from app.config import settings

logger = structlog.get_logger()

T = TypeVar("T")


class CacheService:
    """
    Serviço de cache usando Redis.
    
    Fornece métodos para cache de resultados com TTL configurável.
    """
    
    def __init__(self, redis_client: redis.Redis):
        """
        Inicializa o serviço de cache.
        
        Args:
            redis_client: Cliente Redis assíncrono
        """
        self.redis = redis_client
        self.default_ttl = settings.REDIS_CACHE_TTL
    
    def _make_key(self, prefix: str, *args) -> str:
        """
        Cria chave de cache.
        
        Args:
            prefix: Prefixo da chave
            *args: Argumentos adicionais para compor a chave
            
        Returns:
            Chave de cache formatada
        """
        key_parts = [prefix] + [str(arg) for arg in args if arg is not None]
        return ":".join(key_parts)
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Busca valor do cache.
        
        Args:
            key: Chave do cache
            
        Returns:
            Valor deserializado ou None
        """
        try:
            data = await self.redis.get(key)
            if data is None:
                return None
            return json.loads(data)
        except Exception as e:
            logger.warning("cache_get_error", key=key, error=str(e))
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Define valor no cache.
        
        Args:
            key: Chave do cache
            value: Valor a armazenar
            ttl: TTL em segundos (opcional)
            
        Returns:
            True se sucesso
        """
        try:
            ttl = ttl or self.default_ttl
            serialized = json.dumps(value, default=str)
            await self.redis.set(key, serialized, ex=ttl)
            return True
        except Exception as e:
            logger.warning("cache_set_error", key=key, error=str(e))
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Remove valor do cache.
        
        Args:
            key: Chave do cache
            
        Returns:
            True se removido
        """
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.warning("cache_delete_error", key=key, error=str(e))
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """
        Remove valores que correspondem ao padrão.
        
        Args:
            pattern: Padrão de chaves (ex: "ships:*")
            
        Returns:
            Número de chaves removidas
        """
        try:
            keys = []
            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                await self.redis.delete(*keys)
            
            return len(keys)
        except Exception as e:
            logger.warning("cache_delete_pattern_error", pattern=pattern, error=str(e))
            return 0
    
    async def exists(self, key: str) -> bool:
        """
        Verifica se chave existe.
        
        Args:
            key: Chave do cache
            
        Returns:
            True se existe
        """
        try:
            return await self.redis.exists(key) > 0
        except Exception as e:
            logger.warning("cache_exists_error", key=key, error=str(e))
            return False
    
    async def get_or_set(
        self,
        key: str,
        factory,
        ttl: Optional[int] = None
    ) -> Any:
        """
        Busca do cache ou executa factory e armazena.
        
        Args:
            key: Chave do cache
            factory: Função assíncrona para gerar valor
            ttl: TTL em segundos
            
        Returns:
            Valor do cache ou gerado pela factory
        """
        cached = await self.get(key)
        if cached is not None:
            return cached
        
        value = await factory()
        await self.set(key, value, ttl)
        return value
    
    # =========================================================================
    # Métodos específicos para domínios
    # =========================================================================
    
    async def get_ships_list(self, filters_hash: str) -> Optional[dict]:
        """Cache de lista de navios."""
        key = self._make_key("ships", "list", filters_hash)
        return await self.get(key)
    
    async def set_ships_list(
        self,
        filters_hash: str,
        data: dict
    ) -> bool:
        """Cache de lista de navios."""
        key = self._make_key("ships", "list", filters_hash)
        return await self.set(key, data, settings.CACHE_TTL_SHIPS_LIST)
    
    async def get_ship_detail(self, ship_id: str) -> Optional[dict]:
        """Cache de detalhes do navio."""
        key = self._make_key("ships", "detail", ship_id)
        return await self.get(key)
    
    async def set_ship_detail(self, ship_id: str, data: dict) -> bool:
        """Cache de detalhes do navio."""
        key = self._make_key("ships", "detail", ship_id)
        return await self.set(key, data, settings.CACHE_TTL_SHIP_DETAIL)
    
    async def invalidate_ship(self, ship_id: str) -> None:
        """Invalida todos os caches de um navio."""
        await self.delete_pattern(f"ships:*{ship_id}*")
        await self.delete_pattern("ships:list:*")
        await self.delete_pattern("fleet:*")
    
    async def get_fleet_summary(self) -> Optional[dict]:
        """Cache de resumo da frota."""
        key = self._make_key("fleet", "summary")
        return await self.get(key)
    
    async def set_fleet_summary(self, data: dict) -> bool:
        """Cache de resumo da frota."""
        key = self._make_key("fleet", "summary")
        return await self.set(key, data, settings.CACHE_TTL_FLEET_SUMMARY)
    
    async def get_ship_timeline(
        self,
        ship_id: str,
        params_hash: str
    ) -> Optional[dict]:
        """Cache de timeline do navio."""
        key = self._make_key("ships", "timeline", ship_id, params_hash)
        return await self.get(key)
    
    async def set_ship_timeline(
        self,
        ship_id: str,
        params_hash: str,
        data: dict
    ) -> bool:
        """Cache de timeline do navio."""
        key = self._make_key("ships", "timeline", ship_id, params_hash)
        return await self.set(key, data, settings.CACHE_TTL_SHIP_TIMELINE)
    
    async def get_predictions(
        self,
        ship_id: str,
        params_hash: str
    ) -> Optional[dict]:
        """Cache de previsões."""
        key = self._make_key("predictions", ship_id, params_hash)
        return await self.get(key)
    
    async def set_predictions(
        self,
        ship_id: str,
        params_hash: str,
        data: dict
    ) -> bool:
        """Cache de previsões."""
        key = self._make_key("predictions", ship_id, params_hash)
        return await self.set(key, data, settings.CACHE_TTL_PREDICTIONS)
    
    async def get_roi(
        self,
        ship_id: str,
        params_hash: str
    ) -> Optional[dict]:
        """Cache de ROI."""
        key = self._make_key("roi", ship_id, params_hash)
        return await self.get(key)
    
    async def set_roi(
        self,
        ship_id: str,
        params_hash: str,
        data: dict
    ) -> bool:
        """Cache de ROI."""
        key = self._make_key("roi", ship_id, params_hash)
        return await self.set(key, data, settings.CACHE_TTL_ROI)
    
    async def get_track(
        self,
        ship_id: str,
        params_hash: str
    ) -> Optional[dict]:
        """Cache de trajetória."""
        key = self._make_key("track", ship_id, params_hash)
        return await self.get(key)
    
    async def set_track(
        self,
        ship_id: str,
        params_hash: str,
        data: dict
    ) -> bool:
        """Cache de trajetória."""
        key = self._make_key("track", ship_id, params_hash)
        return await self.set(key, data, settings.CACHE_TTL_TRACK)
