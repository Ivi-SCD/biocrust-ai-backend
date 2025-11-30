# 🚢 API de Monitoramento de Bioincrustação - Transpetro

Sistema de monitoramento e previsão de bioincrustação em navios da frota Transpetro, utilizando modelo físico-estatístico baseado em princípios de física naval.

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Arquitetura](#arquitetura)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Execução](#execução)
- [API Endpoints](#api-endpoints)
- [Modelo de Bioincrustação](#modelo-de-bioincrustação)
- [Testes](#testes)
- [Deployment](#deployment)

## 🎯 Visão Geral

### O Problema

Bioincrustação é o acúmulo de organismos marinhos (cracas, algas, limo) no casco de navios, causando:

- 🔺 Aumento de 20-30% no consumo de combustível
- 💰 Custos extras de R$ 15.000/dia por navio em estado crítico
- ⚠️ Não-conformidade com NORMAM 401
- 🌍 Emissões adicionais de CO₂

### A Solução

Esta API fornece:

1. **Processamento de dados AIS** em tempo real
2. **Cálculo de índice de bioincrustação** (0-100) usando modelo físico
3. **Previsões temporais** de degradação
4. **Cálculo de ROI** de estratégias de manutenção
5. **Alertas inteligentes** contextuais
6. **Analytics e relatórios** executivos

## 🏗️ Arquitetura

```
backend/
├── app/
│   ├── api/v1/          # Endpoints REST
│   ├── core/            # Lógica de negócio (biofouling, alerts)
│   ├── services/        # Camada de serviços
│   ├── repositories/    # Acesso a dados
│   ├── models/          # Modelos SQLAlchemy
│   ├── schemas/         # Schemas Pydantic
│   ├── tasks/           # Tasks Celery
│   └── db/              # Configuração de banco
├── tests/               # Testes automatizados
├── scripts/             # Scripts utilitários
└── docker-compose.yml   # Orquestração de containers
```

### Stack Tecnológico

| Componente | Tecnologia |
|------------|------------|
| Framework | FastAPI 0.104+ |
| Banco de Dados | PostgreSQL 15 + TimescaleDB |
| Cache | Redis 7 |
| Task Queue | Celery |
| ORM | SQLAlchemy 2.0 (async) |
| Validação | Pydantic v2 |

## 🚀 Instalação

### Pré-requisitos

- Python 3.11+
- Docker e Docker Compose
- Poetry ou pip

### Usando Docker (Recomendado)

```bash
# Clonar repositório
git clone <repo-url>
cd backend

# Copiar arquivo de ambiente
cp .env.example .env

# Subir containers
docker-compose up -d

# Verificar status
docker-compose ps
```

### Instalação Manual

```bash
# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
.\venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas configurações

# Inicializar banco de dados
python scripts/seed_database.py
```

## ⚙️ Configuração

### Variáveis de Ambiente

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/biofouling

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# JWT
SECRET_KEY=sua-chave-secreta

# Constantes de Negócio
DEFAULT_CLEANING_COST_BRL=85000
DEFAULT_FUEL_PRICE_PER_TON=4200
```

## 🏃 Execução

### Desenvolvimento

```bash
# API
uvicorn app.main:app --reload --port 8000

# Celery Worker
celery -A app.tasks worker --loglevel=info

# Celery Beat (scheduler)
celery -A app.tasks beat --loglevel=info
```

### Produção

```bash
docker-compose up -d
```

### URLs

- **API**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Flower (Celery)**: http://localhost:5555
- **Prometheus Metrics**: http://localhost:8000/metrics

## 📡 API Endpoints

### Ships

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/ships` | Listar navios |
| GET | `/api/v1/ships/{id}` | Detalhes do navio |
| GET | `/api/v1/ships/{id}/timeline` | Timeline de evolução |

### Biofouling

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/v1/biofouling/calculate` | Calcular índice |
| GET | `/api/v1/biofouling/fleet-summary` | Resumo da frota |

### Predictions

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/v1/predictions/forecast` | Gerar previsão |

### ROI

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/v1/roi/calculate` | Calcular ROI |

### Alerts

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/alerts` | Listar alertas |
| POST | `/api/v1/alerts/{id}/acknowledge` | Reconhecer alerta |
| GET | `/api/v1/alerts/rules` | Listar regras |

### AIS

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/v1/ais/ingest` | Ingerir dados AIS |
| GET | `/api/v1/ais/track/{id}` | Trajetória do navio |

## 🧪 Modelo de Bioincrustação

O modelo calcula um índice de 0-100 baseado em 4 componentes:

| Componente | Peso | Descrição |
|------------|------|-----------|
| Eficiência Hidrodinâmica | 40% | Degradação de performance |
| Exposição Ambiental | 30% | Tempo em águas tropicais |
| Temporal | 20% | Dias desde última limpeza |
| Operacional | 10% | Padrões de operação |

### Níveis NORMAM

| Nível | Índice | Status | Descrição |
|-------|--------|--------|-----------|
| 0 | 0-20 | OK | Limpo |
| 1 | 20-35 | OK | Microincrustação |
| 2 | 35-55 | Warning | Macroincrustação leve |
| 3 | 55-75 | Critical | Macroincrustação moderada |
| 4 | 75-100 | Critical | Macroincrustação pesada |

## 🧪 Testes

```bash
# Executar todos os testes
pytest

# Com coverage
pytest --cov=app --cov-report=html

# Apenas testes unitários
pytest tests/unit -v

# Apenas testes de integração
pytest tests/integration -v

# Testes de performance
pytest tests/ -m benchmark
```

### Cobertura Mínima: 80%

## 🚢 Deployment

### Docker Compose

```bash
docker-compose up -d
```

### Serviços Incluídos

- **api**: FastAPI (porta 8000)
- **db**: PostgreSQL + TimescaleDB (porta 5432)
- **redis**: Redis (porta 6379)
- **celery_worker**: Workers Celery
- **celery_beat**: Scheduler Celery
- **flower**: Monitor Celery (porta 5555)

## 📊 Métricas e Monitoramento

- **Prometheus**: `/metrics`
- **Health Check**: `/health`
- **Flower**: Monitoramento de tasks Celery

## 📝 Licença

Proprietário - Transpetro

## 👥 Contribuidores

Transpetro Tech Team
