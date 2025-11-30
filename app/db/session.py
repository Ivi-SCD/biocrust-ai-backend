"""
Configuração de sessão do banco de dados.

Define engine e session maker para operações assíncronas.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import settings

# Engine assíncrono para PostgreSQL
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    pool_recycle=settings.DATABASE_POOL_RECYCLE,
    pool_pre_ping=True,  # Verificar conexão antes de usar
)

# Engine para testes (sem pool)
test_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    poolclass=NullPool,
)

# Session maker assíncrono
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_async_session() -> AsyncSession:
    """
    Cria nova sessão assíncrona.
    
    Returns:
        AsyncSession: Nova sessão de banco de dados
    """
    async with async_session_maker() as session:
        return session


async def init_db() -> None:
    """
    Inicializa o banco de dados.
    
    Cria todas as tabelas definidas nos modelos.
    Deve ser chamado no startup da aplicação.
    """
    from app.db.base import Base
    # Import all models to register them
    from app.models import (
        ship, ais_position, navigation_event,
        fuel_consumption, inspection, biofouling_index,
        alert, user, report
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """
    Fecha conexões do banco de dados.
    
    Deve ser chamado no shutdown da aplicação.
    """
    await engine.dispose()
