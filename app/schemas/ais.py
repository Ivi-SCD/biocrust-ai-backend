"""
Schemas para dados AIS.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class AISPositionInput(BaseModel):
    """Posição AIS de entrada."""
    
    ship_name: str = Field(..., min_length=1, description="Nome do navio")
    timestamp: datetime = Field(..., description="Timestamp da posição")
    latitude: float = Field(..., ge=-90, le=90, description="Latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude")
    speed: Optional[float] = Field(default=None, ge=0, description="Velocidade em nós")
    heading: Optional[float] = Field(default=None, ge=0, le=360, description="Rumo em graus")


class AISIngestRequest(BaseModel):
    """Request para ingestão de dados AIS."""
    
    positions: List[AISPositionInput] = Field(
        ..., min_length=1, max_length=10000, description="Lista de posições"
    )


class AISIngestResponse(BaseModel):
    """Resposta da ingestão de dados AIS."""
    
    accepted: int = Field(..., description="Posições aceitas")
    rejected: int = Field(..., description="Posições rejeitadas")
    processing_id: str = Field(..., description="ID do processamento")


class TrackPoint(BaseModel):
    """Ponto da trajetória."""
    
    timestamp: datetime = Field(..., description="Timestamp")
    lat: float = Field(..., description="Latitude")
    lon: float = Field(..., description="Longitude")
    speed: Optional[float] = Field(default=None, description="Velocidade")
    heading: Optional[float] = Field(default=None, description="Rumo")


class TrackStatistics(BaseModel):
    """Estatísticas da trajetória."""
    
    total_distance_nm: float = Field(..., description="Distância total em NM")
    avg_speed: float = Field(..., description="Velocidade média")
    max_speed: float = Field(..., description="Velocidade máxima")
    time_in_tropical_waters_hours: float = Field(
        ..., description="Horas em águas tropicais"
    )
    time_in_subtropical_waters_hours: float = Field(
        ..., description="Horas em águas subtropicais"
    )
    time_in_temperate_waters_hours: float = Field(
        ..., description="Horas em águas temperadas"
    )


class PortVisit(BaseModel):
    """Visita a porto."""
    
    name: str = Field(..., description="Nome do porto")
    arrival: datetime = Field(..., description="Chegada")
    departure: datetime = Field(..., description="Partida")


class TrackPeriod(BaseModel):
    """Período da trajetória."""
    
    start: datetime = Field(..., description="Início")
    end: datetime = Field(..., description="Fim")


class TrackResponse(BaseModel):
    """Resposta de trajetória."""
    
    ship_id: str = Field(..., description="UUID do navio")
    ship_name: str = Field(..., description="Nome do navio")
    period: TrackPeriod = Field(..., description="Período")
    total_points: int = Field(..., description="Total de pontos")
    simplified_points: int = Field(..., description="Pontos simplificados")
    track: List[TrackPoint] = Field(..., description="Pontos da trajetória")
    statistics: TrackStatistics = Field(..., description="Estatísticas")
    ports_visited: List[PortVisit] = Field(default=[], description="Portos visitados")


class TrackFilterParams(BaseModel):
    """Parâmetros de filtro para trajetória."""
    
    start_date: datetime = Field(..., description="Data inicial")
    end_date: datetime = Field(..., description="Data final")
    simplify: bool = Field(default=True, description="Simplificar trajetória")
    max_points: int = Field(default=500, ge=10, le=10000, description="Máximo de pontos")
