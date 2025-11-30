# =========================================================================
# Dockerfile para API de Bioincrustação
# =========================================================================

# Imagem base
FROM python:3.11-slim

# Metadados
LABEL maintainer="Transpetro Tech Team"
LABEL description="API de Monitoramento de Bioincrustação"

# Variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar arquivos de dependências
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copiar modelo de bioincrustação existente (já copiado para o diretório backend)
COPY modelo_bioincrustacao_fisico.py /app/

# Copiar código da aplicação
COPY app/ /app/app/

# Criar diretórios necessários
RUN mkdir -p /tmp/reports

# Usuário não-root para segurança
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app /tmp/reports
USER appuser

# Porta da aplicação
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Comando padrão
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
