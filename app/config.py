"""
Configurações da aplicação usando Pydantic BaseSettings.

Carrega variáveis de ambiente do arquivo .env e define valores padrão.
"""

from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configurações centralizadas da aplicação.
    
    Todas as configurações podem ser sobrescritas via variáveis de ambiente
    ou arquivo .env na raiz do projeto.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # =========================================================================
    # Aplicação
    # =========================================================================
    APP_NAME: str = "Transpetro Biofouling Monitor API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = Field(default="development", description="development, staging, production")
    API_V1_PREFIX: str = "/api/v1"
    
    # =========================================================================
    # Banco de Dados
    # =========================================================================
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/biofouling",
        description="URL de conexão com PostgreSQL (async)"
    )
    DATABASE_SYNC_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/biofouling",
        description="URL de conexão síncrona para Alembic"
    )
    DATABASE_POOL_SIZE: int = Field(default=20, ge=5, le=100)
    DATABASE_MAX_OVERFLOW: int = Field(default=40, ge=10, le=200)
    DATABASE_POOL_TIMEOUT: int = Field(default=30, ge=10, le=120)
    DATABASE_POOL_RECYCLE: int = Field(default=3600, description="Reciclar conexões após N segundos")
    
    # =========================================================================
    # Redis
    # =========================================================================
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="URL de conexão com Redis"
    )
    REDIS_CACHE_TTL: int = Field(default=300, description="TTL padrão do cache em segundos")
    REDIS_MAX_CONNECTIONS: int = Field(default=50, ge=10, le=200)
    
    # =========================================================================
    # Celery
    # =========================================================================
    CELERY_BROKER_URL: str = Field(
        default="redis://localhost:6379/1",
        description="URL do broker Celery"
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://localhost:6379/2",
        description="URL do backend de resultados Celery"
    )
    CELERY_TASK_ALWAYS_EAGER: bool = Field(
        default=False,
        description="Executar tasks síncronamente (para testes)"
    )
    
    # =========================================================================
    # Autenticação JWT
    # =========================================================================
    SECRET_KEY: str = Field(
        default="super-secret-key-change-in-production-2024",
        description="Chave secreta para JWT"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, ge=5, le=1440)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, ge=1, le=30)
    
    # =========================================================================
    # CORS
    # =========================================================================
    CORS_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:8080",
            "https://app.transpetro.com.br"
        ],
        description="Origens permitidas para CORS"
    )
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # =========================================================================
    # APIs Externas
    # =========================================================================
    WEATHER_API_KEY: str = Field(default="", description="API Key para dados meteorológicos")
    WEATHER_API_URL: str = Field(
        default="https://api.openweathermap.org/data/2.5",
        description="URL base da API de clima"
    )
    OCEANOGRAPHIC_API_URL: str = Field(
        default="",
        description="URL da API oceanográfica"
    )
    
    # =========================================================================
    # Constantes de Negócio
    # =========================================================================
    DEFAULT_CLEANING_COST_BRL: float = Field(
        default=85000.0,
        description="Custo padrão de limpeza em R$"
    )
    DEFAULT_FUEL_PRICE_PER_TON: float = Field(
        default=4200.0,
        description="Preço padrão do combustível por tonelada em R$"
    )
    DEFAULT_DOWNTIME_COST_PER_DAY: float = Field(
        default=120000.0,
        description="Custo de parada por dia em R$"
    )
    DEFAULT_DOWNTIME_DAYS: int = Field(
        default=3,
        description="Dias de parada para limpeza"
    )
    CRITICAL_INDEX_THRESHOLD: float = Field(
        default=75.0,
        description="Limiar de índice para nível crítico"
    )
    WARNING_INDEX_THRESHOLD: float = Field(
        default=55.0,
        description="Limiar de índice para nível de alerta"
    )
    CRITICAL_COST_PER_DAY: float = Field(
        default=15000.0,
        description="Custo adicional diário por navio em estado crítico"
    )
    
    # =========================================================================
    # Cache TTLs (em segundos)
    # =========================================================================
    CACHE_TTL_SHIPS_LIST: int = Field(default=300, description="5 minutos")
    CACHE_TTL_SHIP_DETAIL: int = Field(default=120, description="2 minutos")
    CACHE_TTL_SHIP_TIMELINE: int = Field(default=3600, description="1 hora")
    CACHE_TTL_FLEET_SUMMARY: int = Field(default=600, description="10 minutos")
    CACHE_TTL_PREDICTIONS: int = Field(default=3600, description="1 hora")
    CACHE_TTL_ROI: int = Field(default=1800, description="30 minutos")
    CACHE_TTL_TRACK: int = Field(default=21600, description="6 horas")
    CACHE_TTL_TRENDS: int = Field(default=3600, description="1 hora")
    CACHE_TTL_BENCHMARKING: int = Field(default=7200, description="2 horas")
    
    # =========================================================================
    # Logging
    # =========================================================================
    LOG_LEVEL: str = Field(default="INFO", description="Nível de log")
    LOG_FORMAT: str = Field(default="json", description="Formato do log: json ou console")
    LOG_FILE: str = Field(default="", description="Arquivo de log (vazio = stdout)")
    
    # =========================================================================
    # Relatórios
    # =========================================================================
    REPORTS_STORAGE_PATH: str = Field(
        default="/tmp/reports",
        description="Caminho para armazenar relatórios gerados"
    )
    REPORTS_EXPIRY_DAYS: int = Field(
        default=7,
        description="Dias para expirar relatórios"
    )
    
    # =========================================================================
    # Validadores
    # =========================================================================
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL deve ser um de: {valid_levels}")
        return v.upper()


@lru_cache()
def get_settings() -> Settings:
    """
    Retorna instância cacheada das configurações.
    
    Returns:
        Settings: Configurações da aplicação
    """
    return Settings()


# Instância global para importação conveniente
settings = get_settings()
