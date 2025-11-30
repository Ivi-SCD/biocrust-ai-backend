"""
Configuração global de testes.

Define fixtures compartilhadas para todos os testes.
"""

import asyncio
from datetime import datetime, timedelta
from typing import AsyncGenerator, Generator
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.config import settings
from app.db.base import Base
from app.dependencies import get_db


# URL do banco de teste (SQLite em memória para testes rápidos)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Cria event loop para a sessão de testes."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    """Cria engine de banco de dados para testes."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Cria sessão de banco de dados para testes."""
    async_session_maker = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    
    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="function")
def client(db_session: AsyncSession) -> TestClient:
    """Cria cliente de teste síncrono."""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Cria cliente de teste assíncrono."""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


# =========================================================================
# Fixtures de dados de exemplo
# =========================================================================

@pytest.fixture
def sample_ship_data():
    """Dados de exemplo para navio."""
    return {
        "id": str(uuid4()),
        "name": "TEST SHIP",
        "ship_class": "Aframax",
        "ship_type": "Petroleiro",
        "gross_tonnage": 105000,
        "length_m": 250,
        "beam_m": 44,
        "draft_m": 14.5
    }


@pytest.fixture
def sample_event_data():
    """Dados de exemplo para evento de navegação."""
    return {
        "ship_name": "TEST SHIP",
        "start_date": datetime.utcnow().isoformat(),
        "end_date": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
        "distance_nm": 282,
        "duration_hours": 24,
        "speed": 11.75,
        "displacement": 128703.71,
        "aft_draft": 14.9,
        "fwd_draft": 14.0,
        "trim": 0.9,
        "beaufort_scale": 5,
        "latitude": -23.5,
        "longitude": -45.2
    }


@pytest.fixture
def sample_ais_position_data():
    """Dados de exemplo para posição AIS."""
    return {
        "ship_name": "TEST SHIP",
        "timestamp": datetime.utcnow().isoformat(),
        "latitude": -23.5,
        "longitude": -45.2,
        "speed": 11.5,
        "heading": 58.0
    }


@pytest.fixture
def sample_cleaning_strategy():
    """Dados de exemplo para estratégia de limpeza."""
    return {
        "name": "clean_now",
        "cleaning_date": (datetime.utcnow().date() + timedelta(days=5)).isoformat(),
        "cleaning_cost_brl": 85000
    }
