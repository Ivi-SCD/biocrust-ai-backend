"""
Aplicação FastAPI principal.

Inicializa e configura a API de monitoramento de bioincrustação.
"""

from contextlib import asynccontextmanager
from datetime import datetime

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from app.config import settings
from app.api.v1.router import api_router
from app.db.session import init_db, close_db
from app.schemas.common import HealthCheck, ErrorResponse

# Configurar logging estruturado
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer() if settings.LOG_FORMAT == "json" else structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerenciador de ciclo de vida da aplicação.
    
    Executa:
    - Startup: inicialização de banco, cache, etc.
    - Shutdown: limpeza de recursos
    """
    # Startup
    logger.info(
        "application_startup",
        app_name=settings.APP_NAME,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT
    )
    
    try:
        # Inicializar banco de dados
        await init_db()
        logger.info("database_initialized")
    except Exception as e:
        logger.error("database_initialization_failed", error=str(e))
    
    yield
    
    # Shutdown
    logger.info("application_shutdown")
    await close_db()


# Criar aplicação FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    description="""
    ## API de Monitoramento de Bioincrustação
    
    Sistema para monitoramento e previsão de bioincrustação em navios da frota Transpetro.
    
    ### Funcionalidades
    
    - **Navios**: Gestão e visualização de navios da frota
    - **Bioincrustação**: Cálculo de índice usando modelo físico-estatístico
    - **Previsões**: Previsão temporal de degradação
    - **ROI**: Cálculo de retorno de investimento em manutenção
    - **Alertas**: Sistema de alertas contextuais inteligentes
    - **AIS**: Ingestão e análise de dados de rastreamento
    - **Analytics**: Análises avançadas e tendências
    - **Relatórios**: Geração de relatórios executivos
    
    ### Níveis NORMAM
    
    - **Nível 0**: Limpo - Sem bioincrustação visível
    - **Nível 1**: Microincrustação - Biofilme/limo
    - **Nível 2**: Macroincrustação leve - 1-15% cobertura
    - **Nível 3**: Macroincrustação moderada - 16-40% cobertura
    - **Nível 4**: Macroincrustação pesada - >40% cobertura
    """,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Prometheus metrics
Instrumentator().instrument(app).expose(app, endpoint="/metrics")


# =========================================================================
# Middleware de logging
# =========================================================================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware para logging de requisições."""
    start_time = datetime.utcnow()
    
    # Log da requisição
    logger.info(
        "request_started",
        method=request.method,
        path=request.url.path,
        client_ip=request.client.host if request.client else None
    )
    
    response = await call_next(request)
    
    # Calcular duração
    duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
    
    # Log da resposta
    logger.info(
        "request_completed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=round(duration_ms, 2)
    )
    
    # Adicionar header de tempo de resposta
    response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
    
    return response


# =========================================================================
# Exception handlers
# =========================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handler global de exceções."""
    logger.error(
        "unhandled_exception",
        path=request.url.path,
        error=str(exc),
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="internal_server_error",
            message="Ocorreu um erro interno no servidor",
            details=str(exc) if settings.DEBUG else None
        ).model_dump(mode="json")
    )


# =========================================================================
# Endpoints de health e info
# =========================================================================

@app.get(
    "/",
    tags=["Root"],
    summary="Informações da API"
)
async def root():
    """Retorna informações básicas da API."""
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/health"
    }


@app.get(
    "/health",
    response_model=HealthCheck,
    tags=["Health"],
    summary="Health Check"
)
async def health_check():
    """
    Verifica saúde da aplicação.
    
    Retorna status de:
    - Aplicação
    - Banco de dados
    - Redis
    - Celery
    """
    return HealthCheck(
        status="healthy",
        version=settings.VERSION,
        timestamp=datetime.utcnow(),
        database="healthy",  # TODO: verificar conexão real
        redis="healthy",     # TODO: verificar conexão real
        celery="healthy"     # TODO: verificar workers
    )


# =========================================================================
# Incluir routers
# =========================================================================

app.include_router(
    api_router,
    prefix=settings.API_V1_PREFIX
)


# =========================================================================
# Entry point para desenvolvimento
# =========================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
