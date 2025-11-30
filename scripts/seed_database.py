#!/usr/bin/env python3
"""
Script para popular o banco de dados com dados de exemplo.

Uso:
    python scripts/seed_database.py
"""

import asyncio
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from uuid import uuid4

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from sqlalchemy import text

from app.db.session import async_session_maker, engine
from app.models.ship import Ship
from app.models.ais_position import AISPosition
from app.models.navigation_event import NavigationEvent
from app.models.biofouling_index import BiofoulingIndex
from app.models.alert import Alert


async def seed_ships():
    """Popula tabela de navios."""
    print("Populando navios...")
    
    # Tentar carregar dados do CSV existente
    data_path = Path(__file__).parent.parent.parent / "data" / "navios.csv"
    
    if data_path.exists():
        df = pd.read_csv(data_path)
        ships_data = []
        
        for _, row in df.iterrows():
            ships_data.append({
                "id": str(uuid4()),
                "name": row.get("Nome do navio", row.get("nome", "Unknown")),
                "ship_class": row.get("Classe", row.get("classe", "Aframax")),
                "ship_type": row.get("Tipo", None),
                "gross_tonnage": int(row.get("Porte Bruto", 0)) if pd.notna(row.get("Porte Bruto")) else None,
                "length_m": float(row.get("Comprimento total (m)", 0)) if pd.notna(row.get("Comprimento total (m)")) else None,
                "beam_m": float(row.get("Boca (m)", 0)) if pd.notna(row.get("Boca (m)")) else None,
                "draft_m": float(row.get("Calado (m)", 0)) if pd.notna(row.get("Calado (m)")) else None,
            })
        
        async with async_session_maker() as session:
            for ship_data in ships_data:
                # Verificar se já existe
                result = await session.execute(
                    text("SELECT id FROM ships WHERE name = :name"),
                    {"name": ship_data["name"]}
                )
                if not result.scalar():
                    ship = Ship(**ship_data)
                    session.add(ship)
            
            await session.commit()
        
        print(f"  {len(ships_data)} navios processados")
    else:
        print("  Arquivo de navios não encontrado, usando dados de exemplo")
        
        async with async_session_maker() as session:
            ships = [
                Ship(
                    id=str(uuid4()),
                    name="BRUNO LIMA",
                    ship_class="Gaseiros 7k",
                    ship_type="Gaseiro",
                    gross_tonnage=7000,
                    length_m=140,
                    beam_m=22,
                    draft_m=8
                ),
                Ship(
                    id=str(uuid4()),
                    name="CARLA SILVA",
                    ship_class="Aframax",
                    ship_type="Petroleiro",
                    gross_tonnage=105000,
                    length_m=250,
                    beam_m=44,
                    draft_m=14.5
                ),
            ]
            
            for ship in ships:
                session.add(ship)
            
            await session.commit()
        
        print(f"  {len(ships)} navios de exemplo criados")


async def seed_biofouling_indices():
    """Popula índices de bioincrustação de exemplo."""
    print("Populando índices de bioincrustação...")
    
    async with async_session_maker() as session:
        # Buscar navios
        result = await session.execute(text("SELECT id, name FROM ships"))
        ships = result.fetchall()
        
        indices_created = 0
        for ship_id, ship_name in ships:
            # Criar histórico de 30 dias
            for days_ago in range(30, 0, -5):
                calc_date = datetime.utcnow() - timedelta(days=days_ago)
                
                # Simular crescimento do índice
                base_index = 30 + (30 - days_ago) * 1.5
                
                index = BiofoulingIndex(
                    id=str(uuid4()),
                    ship_id=ship_id,
                    calculated_at=calc_date,
                    index_value=base_index,
                    normam_level=int(base_index // 25),
                    component_efficiency=base_index * 0.4,
                    component_environmental=base_index * 0.3,
                    component_temporal=base_index * 0.2,
                    component_operational=base_index * 0.1,
                )
                session.add(index)
                indices_created += 1
        
        await session.commit()
    
    print(f"  {indices_created} índices criados")


async def main():
    """Executa seed completo."""
    print("=" * 60)
    print("Iniciando seed do banco de dados")
    print("=" * 60)
    
    await seed_ships()
    await seed_biofouling_indices()
    
    print("=" * 60)
    print("Seed concluído!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
