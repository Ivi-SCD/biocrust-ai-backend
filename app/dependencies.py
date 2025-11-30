"""
Injeção de dependências para FastAPI.

Define funções de dependência para database sessions, cache, serviços, etc.
"""

from typing import AsyncGenerator, Optional

import redis.asyncio as redis
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import async_session_maker
from app.repositories.ship_repository import ShipRepository
from app.repositories.ais_repository import AISRepository
from app.repositories.event_repository import EventRepository
from app.repositories.alert_repository import AlertRepository
from app.repositories.inspection_repository import InspectionRepository
from app.repositories.biofouling_repository import BiofoulingRepository
from app.services.ship_service import ShipService
from app.services.biofouling_service import BiofoulingService
from app.services.ais_service import AISService
from app.services.alert_service import AlertService
from app.services.cache_service import CacheService
from app.services.report_service import ReportService
from app.schemas.common import TokenPayload

# Security
security = HTTPBearer(auto_error=False)

# Redis connection pool
_redis_pool: Optional[redis.ConnectionPool] = None


async def get_redis_pool() -> redis.ConnectionPool:
    """
    Retorna pool de conexões Redis.
    
    Returns:
        ConnectionPool: Pool de conexões Redis
    """
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = redis.ConnectionPool.from_url(
            settings.REDIS_URL,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            decode_responses=True
        )
    return _redis_pool


async def get_redis() -> AsyncGenerator[redis.Redis, None]:
    """
    Dependency que fornece conexão Redis.
    
    Yields:
        Redis: Cliente Redis assíncrono
    """
    pool = await get_redis_pool()
    client = redis.Redis(connection_pool=pool)
    try:
        yield client
    finally:
        await client.close()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency que fornece sessão de banco de dados.
    
    Yields:
        AsyncSession: Sessão assíncrona do SQLAlchemy
    """
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_cache_service(
    redis_client: redis.Redis = Depends(get_redis)
) -> CacheService:
    """
    Dependency para serviço de cache.
    
    Args:
        redis_client: Cliente Redis injetado
        
    Returns:
        CacheService: Serviço de cache
    """
    return CacheService(redis_client)


# =========================================================================
# Repositories
# =========================================================================

async def get_ship_repository(
    db: AsyncSession = Depends(get_db)
) -> ShipRepository:
    """Dependency para repositório de navios."""
    return ShipRepository(db)


async def get_ais_repository(
    db: AsyncSession = Depends(get_db)
) -> AISRepository:
    """Dependency para repositório de dados AIS."""
    return AISRepository(db)


async def get_event_repository(
    db: AsyncSession = Depends(get_db)
) -> EventRepository:
    """Dependency para repositório de eventos de navegação."""
    return EventRepository(db)


async def get_alert_repository(
    db: AsyncSession = Depends(get_db)
) -> AlertRepository:
    """Dependency para repositório de alertas."""
    return AlertRepository(db)


async def get_inspection_repository(
    db: AsyncSession = Depends(get_db)
) -> InspectionRepository:
    """Dependency para repositório de inspeções."""
    return InspectionRepository(db)


async def get_biofouling_repository(
    db: AsyncSession = Depends(get_db)
) -> BiofoulingRepository:
    """Dependency para repositório de índices de bioincrustação."""
    return BiofoulingRepository(db)


# =========================================================================
# Services
# =========================================================================

async def get_ship_service(
    ship_repo: ShipRepository = Depends(get_ship_repository),
    ais_repo: AISRepository = Depends(get_ais_repository),
    biofouling_repo: BiofoulingRepository = Depends(get_biofouling_repository),
    alert_repo: AlertRepository = Depends(get_alert_repository),
    inspection_repo: InspectionRepository = Depends(get_inspection_repository),
    cache_service: CacheService = Depends(get_cache_service)
) -> ShipService:
    """Dependency para serviço de navios."""
    return ShipService(
        ship_repo=ship_repo,
        ais_repo=ais_repo,
        biofouling_repo=biofouling_repo,
        alert_repo=alert_repo,
        inspection_repo=inspection_repo,
        cache_service=cache_service
    )


async def get_biofouling_service(
    ship_repo: ShipRepository = Depends(get_ship_repository),
    biofouling_repo: BiofoulingRepository = Depends(get_biofouling_repository),
    event_repo: EventRepository = Depends(get_event_repository),
    cache_service: CacheService = Depends(get_cache_service)
) -> BiofoulingService:
    """Dependency para serviço de bioincrustação."""
    return BiofoulingService(
        ship_repo=ship_repo,
        biofouling_repo=biofouling_repo,
        event_repo=event_repo,
        cache_service=cache_service
    )


async def get_ais_service(
    ais_repo: AISRepository = Depends(get_ais_repository),
    ship_repo: ShipRepository = Depends(get_ship_repository),
    cache_service: CacheService = Depends(get_cache_service)
) -> AISService:
    """Dependency para serviço de dados AIS."""
    return AISService(
        ais_repo=ais_repo,
        ship_repo=ship_repo,
        cache_service=cache_service
    )


async def get_alert_service(
    alert_repo: AlertRepository = Depends(get_alert_repository),
    ship_repo: ShipRepository = Depends(get_ship_repository),
    biofouling_repo: BiofoulingRepository = Depends(get_biofouling_repository)
) -> AlertService:
    """Dependency para serviço de alertas."""
    return AlertService(
        alert_repo=alert_repo,
        ship_repo=ship_repo,
        biofouling_repo=biofouling_repo
    )


async def get_report_service(
    ship_repo: ShipRepository = Depends(get_ship_repository),
    biofouling_repo: BiofoulingRepository = Depends(get_biofouling_repository),
    alert_repo: AlertRepository = Depends(get_alert_repository)
) -> ReportService:
    """Dependency para serviço de relatórios."""
    return ReportService(
        ship_repo=ship_repo,
        biofouling_repo=biofouling_repo,
        alert_repo=alert_repo
    )


# =========================================================================
# Authentication
# =========================================================================

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[TokenPayload]:
    """
    Dependency para obter usuário atual via JWT.
    
    Args:
        credentials: Credenciais do header Authorization
        
    Returns:
        TokenPayload: Dados do token ou None se não autenticado
        
    Raises:
        HTTPException: Se token inválido
    """
    if credentials is None:
        return None
    
    token = credentials.credentials
    
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(
            sub=payload.get("sub"),
            exp=payload.get("exp"),
            user_id=payload.get("user_id"),
            role=payload.get("role", "user")
        )
        return token_data
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"}
        )


async def require_auth(
    user: Optional[TokenPayload] = Depends(get_current_user)
) -> TokenPayload:
    """
    Dependency que requer autenticação.
    
    Args:
        user: Usuário atual (opcional)
        
    Returns:
        TokenPayload: Dados do usuário autenticado
        
    Raises:
        HTTPException: Se não autenticado
    """
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticação necessária",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user


async def require_admin(
    user: TokenPayload = Depends(require_auth)
) -> TokenPayload:
    """
    Dependency que requer role de admin.
    
    Args:
        user: Usuário autenticado
        
    Returns:
        TokenPayload: Dados do usuário admin
        
    Raises:
        HTTPException: Se não for admin
    """
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissão de administrador necessária"
        )
    return user
