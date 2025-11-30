"""
Schemas para Navios.
"""

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ShipStatus(str, Enum):
    """Status de bioincrustação do navio."""
    OK = "ok"
    WARNING = "warning"
    CRITICAL = "critical"


class ShipClass(str, Enum):
    """Classes de navios da frota."""
    AFRAMAX = "Aframax"
    SUEZMAX = "Suezmax"
    MR2 = "MR2"
    GASEIROS_7K = "Gaseiros 7k"


class ShipBase(BaseModel):
    """Schema base para navios."""
    
    model_config = ConfigDict(from_attributes=True)
    
    name: str = Field(..., min_length=1, max_length=100, description="Nome do navio")
    ship_class: str = Field(..., alias="class", description="Classe do navio")
    ship_type: Optional[str] = Field(default=None, description="Tipo do navio")
    gross_tonnage: Optional[int] = Field(default=None, ge=0, description="Porte bruto")
    length_m: Optional[float] = Field(default=None, ge=0, description="Comprimento em metros")
    beam_m: Optional[float] = Field(default=None, ge=0, description="Boca em metros")
    draft_m: Optional[float] = Field(default=None, ge=0, description="Calado em metros")


class ShipCreate(ShipBase):
    """Schema para criação de navio."""
    pass


class ShipSpecifications(BaseModel):
    """Especificações técnicas do navio."""
    
    length_m: Optional[float] = Field(default=None, description="Comprimento em metros")
    beam_m: Optional[float] = Field(default=None, description="Boca em metros")
    draft_m: Optional[float] = Field(default=None, description="Calado em metros")
    gross_tonnage: Optional[int] = Field(default=None, description="Porte bruto")


class ShipPosition(BaseModel):
    """Posição atual do navio."""
    
    latitude: float = Field(..., ge=-90, le=90, description="Latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude")
    timestamp: datetime = Field(..., description="Timestamp da posição")
    speed: Optional[float] = Field(default=None, ge=0, description="Velocidade em nós")
    heading: Optional[float] = Field(default=None, ge=0, le=360, description="Rumo em graus")


class BiofoulingComponents(BaseModel):
    """Componentes do índice de bioincrustação."""
    
    efficiency: Optional[float] = Field(default=None, description="Componente de eficiência")
    environmental: Optional[float] = Field(default=None, description="Componente ambiental")
    temporal: Optional[float] = Field(default=None, description="Componente temporal")
    operational: Optional[float] = Field(default=None, description="Componente operacional")


class ShipCurrentStatus(BaseModel):
    """Status atual de bioincrustação."""
    
    model_config = ConfigDict(populate_by_name=True)
    
    biofouling_index: float = Field(..., ge=0, le=100, description="Índice de bioincrustação", validation_alias="index", serialization_alias="index")
    normam_level: int = Field(..., ge=0, le=4, description="Nível NORMAM")
    status: ShipStatus = Field(..., description="Status do navio")
    components: BiofoulingComponents = Field(..., description="Componentes do índice")
    calculated_at: datetime = Field(..., description="Data do cálculo")


class ShipResponse(BaseModel):
    """Schema de resposta para navio."""
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    
    id: str = Field(..., description="UUID do navio")
    name: str = Field(..., description="Nome do navio")
    ship_class: str = Field(..., alias="class", serialization_alias="class", description="Classe")
    current_index: Optional[float] = Field(default=None, description="Índice atual")
    normam_level: Optional[int] = Field(default=None, description="Nível NORMAM")
    status: Optional[ShipStatus] = Field(default=None, description="Status")
    last_position: Optional[ShipPosition] = Field(default=None, description="Última posição")
    last_inspection_date: Optional[date] = Field(default=None, description="Última inspeção")
    days_since_cleaning: Optional[int] = Field(default=None, description="Dias desde limpeza")
    components: Optional[BiofoulingComponents] = Field(default=None, description="Componentes")


class ShipListResponse(BaseModel):
    """Resposta para lista de navios."""
    
    total: int = Field(..., description="Total de navios")
    ships: List[ShipResponse] = Field(..., description="Lista de navios")


class RecentEvent(BaseModel):
    """Evento recente de navegação."""
    
    session_id: Optional[str] = Field(default=None, description="ID da sessão")
    start_date: datetime = Field(..., description="Data de início")
    distance_nm: Optional[float] = Field(default=None, description="Distância em NM")
    avg_speed: Optional[float] = Field(default=None, description="Velocidade média")
    fuel_consumed: Optional[float] = Field(default=None, description="Combustível consumido")
    index_calculated: Optional[float] = Field(default=None, description="Índice calculado")


class HistoricalIndex(BaseModel):
    """Índice histórico."""
    
    model_config = ConfigDict(populate_by_name=True)
    
    record_date: date = Field(..., description="Data", validation_alias="date", serialization_alias="date")
    index_value: float = Field(..., description="Valor do índice", validation_alias="index", serialization_alias="index")


class ShipAlert(BaseModel):
    """Alerta do navio (resumido)."""
    
    id: str = Field(..., description="UUID do alerta")
    alert_type: str = Field(..., description="Tipo do alerta", serialization_alias="type")
    message: str = Field(..., description="Mensagem")
    created_at: datetime = Field(..., description="Data de criação")


class ShipDetailResponse(BaseModel):
    """Resposta detalhada de navio."""
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    
    id: str = Field(..., description="UUID do navio")
    name: str = Field(..., description="Nome do navio")
    ship_class: str = Field(..., alias="class", serialization_alias="class", description="Classe")
    specifications: ShipSpecifications = Field(..., description="Especificações técnicas")
    current_status: Optional[ShipCurrentStatus] = Field(default=None, description="Status atual")
    current_position: Optional[ShipPosition] = Field(default=None, description="Posição atual")
    recent_events: List[RecentEvent] = Field(default=[], description="Eventos recentes")
    historical_indices: List[HistoricalIndex] = Field(default=[], description="Histórico de índices")
    alerts: List[ShipAlert] = Field(default=[], description="Alertas ativos")


class TimelineInterval(str, Enum):
    """Intervalo de agregação do timeline."""
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


class ShipTimelineRequest(BaseModel):
    """Request para timeline do navio."""
    
    start_date: datetime = Field(..., description="Data inicial")
    end_date: datetime = Field(..., description="Data final")
    interval: TimelineInterval = Field(default=TimelineInterval.DAY, description="Intervalo")


class EnvironmentalExposure(BaseModel):
    """Exposição ambiental em um período."""
    
    tropical_hours: float = Field(default=0, description="Horas em águas tropicais")
    subtropical_hours: float = Field(default=0, description="Horas em águas subtropicais")
    avg_temperature_c: Optional[float] = Field(default=None, description="Temperatura média")


class TimelineDataPoint(BaseModel):
    """Ponto de dados do timeline."""
    
    model_config = ConfigDict(populate_by_name=True)
    
    timestamp: datetime = Field(..., description="Timestamp")
    biofouling_index: float = Field(..., description="Índice de bioincrustação", validation_alias="index", serialization_alias="index")
    normam_level: int = Field(..., description="Nível NORMAM")
    components: BiofoulingComponents = Field(..., description="Componentes")
    position: Optional[ShipPosition] = Field(default=None, description="Posição")
    environmental_exposure: Optional[EnvironmentalExposure] = Field(
        default=None, description="Exposição ambiental"
    )


class TimelineStatistics(BaseModel):
    """Estatísticas do timeline."""
    
    avg_index: float = Field(..., description="Índice médio")
    max_index: float = Field(..., description="Índice máximo")
    min_index: float = Field(..., description="Índice mínimo")
    degradation_rate_per_month: float = Field(..., description="Taxa de degradação mensal")


class TimelineEvent(BaseModel):
    """Evento no timeline (limpeza, inspeção, etc)."""
    
    event_type: str = Field(..., description="Tipo do evento", serialization_alias="type")
    event_date: date = Field(..., description="Data do evento", serialization_alias="date")
    location: Optional[str] = Field(default=None, description="Local")
    normam_level_confirmed: Optional[int] = Field(default=None, description="Nível confirmado")


class TimelinePeriod(BaseModel):
    """Período do timeline."""
    
    start: date = Field(..., description="Data inicial")
    end: date = Field(..., description="Data final")


class ShipTimelineResponse(BaseModel):
    """Resposta do timeline do navio."""
    
    ship_id: str = Field(..., description="UUID do navio")
    ship_name: str = Field(..., description="Nome do navio")
    period: TimelinePeriod = Field(..., description="Período")
    data_points: List[TimelineDataPoint] = Field(..., description="Pontos de dados")
    statistics: TimelineStatistics = Field(..., description="Estatísticas")
    events: List[TimelineEvent] = Field(default=[], description="Eventos")


class ShipFilterParams(BaseModel):
    """Parâmetros de filtro para lista de navios."""
    
    status: Optional[ShipStatus] = Field(default=None, description="Filtrar por status")
    ship_class: Optional[str] = Field(default=None, alias="class", description="Filtrar por classe")
    sort_by: str = Field(default="name", description="Campo para ordenação")
    order: str = Field(default="asc", pattern="^(asc|desc)$", description="Ordem")
    limit: int = Field(default=50, ge=1, le=500, description="Limite")
    offset: int = Field(default=0, ge=0, description="Offset")
