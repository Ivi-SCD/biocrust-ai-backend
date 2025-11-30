-- =========================================================================
-- Script de inicialização do banco de dados
-- Executado automaticamente pelo Docker na primeira execução
-- =========================================================================

-- Habilitar extensão TimescaleDB
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Habilitar extensão UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =========================================================================
-- Tabela de Navios
-- =========================================================================
CREATE TABLE IF NOT EXISTS ships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    ship_class VARCHAR(50) NOT NULL,
    ship_type VARCHAR(50),
    gross_tonnage INTEGER,
    length_m DOUBLE PRECISION,
    beam_m DOUBLE PRECISION,
    draft_m DOUBLE PRECISION,
    last_cleaning_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ships_class_name ON ships(ship_class, name);

-- =========================================================================
-- Tabela de Posições AIS (Hypertable)
-- =========================================================================
CREATE TABLE IF NOT EXISTS ais_positions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ship_id UUID NOT NULL REFERENCES ships(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    speed DOUBLE PRECISION,
    heading DOUBLE PRECISION,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Converter para hypertable TimescaleDB
SELECT create_hypertable('ais_positions', 'timestamp', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_ais_positions_ship_time ON ais_positions(ship_id, timestamp DESC);

-- =========================================================================
-- Tabela de Índices de Bioincrustação (Hypertable)
-- =========================================================================
CREATE TABLE IF NOT EXISTS biofouling_indices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ship_id UUID NOT NULL REFERENCES ships(id) ON DELETE CASCADE,
    calculated_at TIMESTAMPTZ NOT NULL,
    index_value DOUBLE PRECISION NOT NULL,
    normam_level INTEGER NOT NULL CHECK (normam_level >= 0 AND normam_level <= 4),
    component_efficiency DOUBLE PRECISION,
    component_environmental DOUBLE PRECISION,
    component_temporal DOUBLE PRECISION,
    component_operational DOUBLE PRECISION,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Converter para hypertable TimescaleDB
SELECT create_hypertable('biofouling_indices', 'calculated_at', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_biofouling_ship_time ON biofouling_indices(ship_id, calculated_at DESC);

-- =========================================================================
-- Tabela de Eventos de Navegação
-- =========================================================================
CREATE TABLE IF NOT EXISTS navigation_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id BIGINT UNIQUE,
    ship_id UUID NOT NULL REFERENCES ships(id) ON DELETE CASCADE,
    event_name VARCHAR(100),
    start_date TIMESTAMPTZ NOT NULL,
    end_date TIMESTAMPTZ NOT NULL,
    duration_hours DOUBLE PRECISION,
    distance_nm DOUBLE PRECISION,
    avg_speed DOUBLE PRECISION,
    aft_draft DOUBLE PRECISION,
    fwd_draft DOUBLE PRECISION,
    mid_draft DOUBLE PRECISION,
    trim DOUBLE PRECISION,
    displacement DOUBLE PRECISION,
    beaufort_scale INTEGER,
    sea_condition VARCHAR(50),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_nav_events_ship_date ON navigation_events(ship_id, start_date DESC);

-- =========================================================================
-- Tabela de Consumo de Combustível
-- =========================================================================
CREATE TABLE IF NOT EXISTS fuel_consumption (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id BIGINT NOT NULL REFERENCES navigation_events(session_id) ON DELETE CASCADE,
    consumed_quantity DOUBLE PRECISION NOT NULL,
    fuel_type VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =========================================================================
-- Tabela de Inspeções
-- =========================================================================
CREATE TABLE IF NOT EXISTS inspections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ship_id UUID NOT NULL REFERENCES ships(id) ON DELETE CASCADE,
    inspection_date DATE NOT NULL,
    location VARCHAR(100),
    normam_level_confirmed INTEGER CHECK (normam_level_confirmed >= 0 AND normam_level_confirmed <= 4),
    hull_condition_pct INTEGER,
    fouling_type TEXT,
    notes TEXT,
    inspector_name VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_inspections_ship_date ON inspections(ship_id, inspection_date DESC);

-- =========================================================================
-- Tabela de Alertas
-- =========================================================================
CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ship_id UUID NOT NULL REFERENCES ships(id) ON DELETE CASCADE,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('info', 'warning', 'critical')),
    alert_type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    details JSONB,
    recommended_actions JSONB,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'acknowledged', 'resolved')),
    acknowledged_at TIMESTAMPTZ,
    acknowledged_by UUID,
    acknowledged_notes TEXT,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_alerts_ship_status ON alerts(ship_id, status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_severity_status ON alerts(severity, status);

-- =========================================================================
-- Tabela de Métricas Ambientais
-- =========================================================================
CREATE TABLE IF NOT EXISTS ship_environmental_metrics (
    ship_id UUID PRIMARY KEY REFERENCES ships(id) ON DELETE CASCADE,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    tropical_hours DOUBLE PRECISION DEFAULT 0,
    subtropical_hours DOUBLE PRECISION DEFAULT 0,
    temperate_hours DOUBLE PRECISION DEFAULT 0,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =========================================================================
-- Tabela de Usuários
-- =========================================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    role VARCHAR(20) DEFAULT 'viewer',
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =========================================================================
-- Tabela de Relatórios
-- =========================================================================
CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    progress_pct INTEGER DEFAULT 0,
    current_step VARCHAR(100),
    file_path VARCHAR(500),
    file_size_bytes BIGINT,
    download_url VARCHAR(500),
    pages INTEGER,
    expires_at TIMESTAMPTZ,
    parameters JSONB,
    error_message TEXT,
    requested_by UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =========================================================================
-- Função para atualizar updated_at automaticamente
-- =========================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers para updated_at
CREATE TRIGGER update_ships_updated_at BEFORE UPDATE ON ships
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_inspections_updated_at BEFORE UPDATE ON inspections
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_alerts_updated_at BEFORE UPDATE ON alerts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_reports_updated_at BEFORE UPDATE ON reports
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =========================================================================
-- Dados iniciais de exemplo
-- =========================================================================
INSERT INTO ships (name, ship_class, ship_type, gross_tonnage, length_m, beam_m, draft_m)
VALUES 
    ('BRUNO LIMA', 'Gaseiros 7k', 'Gaseiro', 7000, 140, 22, 8),
    ('CARLA SILVA', 'Aframax', 'Petroleiro', 105000, 250, 44, 14.5),
    ('HENRIQUE ALVES', 'Suezmax', 'Petroleiro', 150000, 274, 48, 16),
    ('DANIEL PEREIRA', 'MR2', 'Petroleiro', 50000, 180, 32, 11)
ON CONFLICT (name) DO NOTHING;

COMMIT;
