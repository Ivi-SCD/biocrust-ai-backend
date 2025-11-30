"""
Schemas Pydantic para validação de entrada/saída da API.
"""

from app.schemas.common import (
    PaginatedResponse,
    PaginationParams,
    TokenPayload,
    HealthCheck,
    ErrorResponse,
)
from app.schemas.ship import (
    ShipBase,
    ShipCreate,
    ShipResponse,
    ShipDetailResponse,
    ShipListResponse,
    ShipTimelineRequest,
    ShipTimelineResponse,
    ShipSpecifications,
    ShipPosition,
)
from app.schemas.biofouling import (
    BiofoulingCalculateRequest,
    BiofoulingCalculateResponse,
    BiofoulingEventInput,
    BiofoulingResult,
    FleetSummaryResponse,
    BiofoulingComponents,
)
from app.schemas.alert import (
    AlertResponse,
    AlertListResponse,
    AlertAcknowledgeRequest,
    AlertRuleResponse,
)
from app.schemas.analytics import (
    FleetTrendsResponse,
    BenchmarkingRequest,
    BenchmarkingResponse,
)

__all__ = [
    # Common
    "PaginatedResponse",
    "PaginationParams",
    "TokenPayload",
    "HealthCheck",
    "ErrorResponse",
    # Ship
    "ShipBase",
    "ShipCreate",
    "ShipResponse",
    "ShipDetailResponse",
    "ShipListResponse",
    "ShipTimelineRequest",
    "ShipTimelineResponse",
    "ShipSpecifications",
    "ShipPosition",
    # Biofouling
    "BiofoulingCalculateRequest",
    "BiofoulingCalculateResponse",
    "BiofoulingEventInput",
    "BiofoulingResult",
    "FleetSummaryResponse",
    "BiofoulingComponents",
    # Alert
    "AlertResponse",
    "AlertListResponse",
    "AlertAcknowledgeRequest",
    "AlertRuleResponse",
    # Analytics
    "FleetTrendsResponse",
    "BenchmarkingRequest",
    "BenchmarkingResponse",
]
