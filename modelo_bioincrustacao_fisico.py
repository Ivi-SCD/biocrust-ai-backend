import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class ModeloBioincrustacaoFisico:
    """
    Modelo baseado em física naval para estimar bioincrustação.
    
    Não requer dados de treinamento - usa apenas princípios físicos
    e estatísticos conhecidos da indústria naval.
    """
    
    def __init__(self):
        """
        Inicializa o modelo com parâmetros baseados em literatura naval.
        
        Referências dos parâmetros:
        - IMO Guidelines for biofouling management (MEPC.207(62))
        - Schultz, M.P. (2007) "Effects of coating roughness and biofouling on ship resistance"
        - Townsin, R.L. (2003) "The ship hull fouling penalty"
        """

        self.baselines = {
            'Aframax': {
                'velocidade_economica': 14.5,
                'speed_length_ratio_otimo': 0.29,
                'consumo_especifico_base': 0.17, 
            },
            'Suezmax': {
                'velocidade_economica': 14.0,
                'speed_length_ratio_otimo': 0.27,
                'consumo_especifico_base': 0.16,
            },
            'MR2': {
                'velocidade_economica': 14.0,
                'speed_length_ratio_otimo': 0.30,
                'consumo_especifico_base': 0.18,
            },
            'Gaseiros 7k': {
                'velocidade_economica': 15.0,
                'speed_length_ratio_otimo': 0.31,
                'consumo_especifico_base': 0.19,
            }
        }
        

        self.pesos = {
            'eficiencia_hidrodinamica': 0.40,
            'exposicao_ambiental': 0.30,
            'temporal': 0.20,
            'operacional': 0.10
        }
        
        self.taxa_crescimento = {
            'tropical': 2.5,      
            'subtropical': 1.5,  
            'temperada': 0.8    
        }
    
    def calcular_indice_bioincrustacao(self, df_eventos, comprimento_navio=None):
        df = df_eventos.copy()
        
        df = self._padronizar_colunas(df)
        
        df['comp_eficiencia'] = self._calcular_componente_eficiencia(df, comprimento_navio)
        df['comp_ambiental'] = self._calcular_componente_ambiental(df)
        df['comp_temporal'] = self._calcular_componente_temporal(df)
        df['comp_operacional'] = self._calcular_componente_operacional(df)
        
        df['indice_bioincrustacao'] = (
            self.pesos['eficiencia_hidrodinamica'] * df['comp_eficiencia'] +
            self.pesos['exposicao_ambiental'] * df['comp_ambiental'] +
            self.pesos['temporal'] * df['comp_temporal'] +
            self.pesos['operacional'] * df['comp_operacional']
        )
        
        df['nivel_normam_estimado'] = df['indice_bioincrustacao'].apply(
            self._indice_para_nivel_normam
        )
        
        df['status_alerta'] = df['nivel_normam_estimado'].apply(
            self._nivel_para_status
        )
        
        return df
    
    def _padronizar_colunas(self, df):
        """Padroniza nomes de colunas para formato consistente"""
        mapeamento = {
            'sessao_navio_id': 'sessionId',
            'nome_navio': 'shipName',
            'classe_navio': 'class',
            'evento_navegacao': 'eventName',
            'data_inicio_gmt': 'startGMTDate',
            'data_fim_gmt': 'endGMTDate',
            'duracao_h': 'duration',
            'distancia_nm': 'distance',
            'calado_a_re_m': 'aftDraft',
            'calado_a_vante_m': 'fwdDraft',
            'calado_a_meia_nau_m': 'midDraft',
            'diferenca_re_vante_m': 'TRIM',
            'peso_volume_deslocado_ton': 'displacement',
            'escala_beaufort': 'beaufortScale',
            'velocidade_navegacao': 'speed',
            'velocidade_navegacao_gps': 'speedGps',
            'latitude': 'decLatitude',
            'longitude': 'decLongitude'
        }
        
        df = df.rename(columns=mapeamento)
        
        if 'startGMTDate' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['startGMTDate']):
            df['startGMTDate'] = pd.to_datetime(df['startGMTDate'])
        if 'endGMTDate' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['endGMTDate']):
            df['endGMTDate'] = pd.to_datetime(df['endGMTDate'])
        
        return df
    
    def _calcular_componente_eficiencia(self, df, comprimento_navio=None):
        """
        Componente 1: Degradação de Eficiência Hidrodinâmica (0-100)
        
        Princípio: Bioincrustação aumenta rugosidade do casco, aumentando resistência.
        A resistência total é aproximadamente proporcional à velocidade ao quadrado.
        
        Medimos através de:
        - Speed-Length Ratio vs esperado
        - Desvio da velocidade para o displacement
        - Froude Number (quando aplicável)
        """
        scores = []
        
        for _, row in df.iterrows():
            classe = row.get('class', 'Aframax')
            baseline = self.baselines.get(classe, self.baselines['Aframax'])
            
            # 1. Speed-Length Ratio
            # SLR = V(nós) / sqrt(L(pés))
            # Comprimento em pés = comprimento_metros * 3.28084
            if comprimento_navio:
                comprimento_pes = comprimento_navio * 3.28084
            else:
                # Estimativa por classe
                comprimento_est = {'Aframax': 250, 'Suezmax': 274, 'MR2': 180, 'Gaseiros 7k': 140}
                comprimento_pes = comprimento_est.get(classe, 250) * 3.28084
            
            velocidade = row.get('speed', row.get('speedGps', 0))
            slr_atual = velocidade / np.sqrt(comprimento_pes)
            slr_otimo = baseline['speed_length_ratio_otimo']
            
            # Degradação de SLR (quanto menor que ótimo, pior)
            degradacao_slr = max(0, (slr_otimo - slr_atual) / slr_otimo * 100)
            
            # 2. Velocidade vs Displacement
            # Navios mais carregados vão mais devagar, mas há um limite razoável
            displacement = row.get('displacement', 120000)
            velocidade_esperada = baseline['velocidade_economica'] * (1 - (displacement - 100000) / 500000)
            
            if velocidade > 0:
                degradacao_velocidade = max(0, (velocidade_esperada - velocidade) / velocidade_esperada * 100)
            else:
                degradacao_velocidade = 50  # Se não temos velocidade, assumir médio
            
            # 3. Trim Impact
            # Trim excessivo aumenta resistência (ótimo é ~0.5m)
            trim = abs(row.get('TRIM', 1.0))
            trim_penalty = min(30, (trim - 0.5) * 10) if trim > 0.5 else 0
            
            # Score composto (média ponderada)
            score = (
                0.5 * degradacao_slr +
                0.3 * degradacao_velocidade +
                0.2 * trim_penalty
            )
            
            scores.append(min(100, max(0, score)))
        
        return pd.Series(scores, index=df.index)
    
    def _calcular_componente_ambiental(self, df):
        """
        Componente 2: Exposição a Condições Favoráveis para Bioincrustação (0-100)
        
        Princípio: Organismos marinhos crescem mais rápido em:
        - Águas tropicais/quentes (temperatura > 20°C)
        - Águas calmas (baixa velocidade permite assentamento)
        - Águas ricas em nutrientes (costeiras)
        
        Usamos latitude como proxy para temperatura.
        """
        scores = []
        
        for _, row in df.iterrows():
            lat = row.get('decLatitude', 0)
            lon = row.get('decLongitude', 0)
            velocidade = row.get('speed', 10)
            beaufort = row.get('beaufortScale', 3)
            
            # 1. Fator de temperatura por latitude
            # Águas tropicais (-20° a +20°): score alto
            # Águas temperadas (>35°): score baixo
            lat_abs = abs(lat)
            if lat_abs <= 20:
                temp_score = 100  # Tropical - máximo crescimento
            elif lat_abs <= 35:
                temp_score = 70 - (lat_abs - 20) * 2  # Subtropical - crescimento moderado
            else:
                temp_score = 30  # Temperada - crescimento lento
            
            # 2. Fator de velocidade
            # Baixa velocidade = permite assentamento de larvas
            if velocidade < 5:
                vel_score = 80  # Quase parado - máximo assentamento
            elif velocidade < 10:
                vel_score = 50
            else:
                vel_score = 20  # Alta velocidade dificulta assentamento
            
            # 3. Fator de mar
            # Mar agitado ajuda a remover organismos
            beaufort_score = max(0, 60 - beaufort * 10)
            
            # 4. Fator costeiro
            # Águas costeiras têm mais nutrientes
            # Aproximação: longitude próxima a continentes
            costeiro_score = 40  # Valor médio (sem dados precisos de batimetria)
            
            # Score composto
            score = (
                0.40 * temp_score +
                0.30 * vel_score +
                0.20 * beaufort_score +
                0.10 * costeiro_score
            )
            
            scores.append(score)
        
        return pd.Series(scores, index=df.index)
    
    def _calcular_componente_temporal(self, df):
        """
        Componente 3: Acúmulo Temporal (0-100)
        
        Princípio: Bioincrustação é um processo progressivo.
        - 0-60 dias: biofilme, baixo impacto
        - 60-180 dias: assentamento de macro-organismos
        - 180-365 dias: crescimento acelerado
        - >365 dias: estado crítico
        
        Como não temos data de limpeza, usamos início da série temporal
        como proxy (assumindo que no início do período de dados havia sido limpo).
        """
        scores = []
        
        # Encontrar data mínima por navio (assumir como "limpeza recente")
        if 'startGMTDate' in df.columns and 'shipName' in df.columns:
            datas_minimas = df.groupby('shipName')['startGMTDate'].min()
            
            for _, row in df.iterrows():
                navio = row.get('shipName')
                data_atual = row.get('startGMTDate')
                
                if pd.notna(data_atual) and navio in datas_minimas:
                    data_ref = datas_minimas[navio]
                    dias = (data_atual - data_ref).days
                    
                    # Curva de crescimento não-linear (logarítmica)
                    # Cresce rápido no início, depois satura
                    if dias <= 60:
                        score = dias / 60 * 20  # 0-20 pontos
                    elif dias <= 180:
                        score = 20 + (dias - 60) / 120 * 30  # 20-50 pontos
                    elif dias <= 365:
                        score = 50 + (dias - 180) / 185 * 30  # 50-80 pontos
                    else:
                        score = 80 + min(20, (dias - 365) / 365 * 20)  # 80-100 pontos
                    
                    scores.append(score)
                else:
                    scores.append(50)  # Valor médio se não temos data
        else:
            scores = [50] * len(df)  # Sem dados temporais, assumir médio
        
        return pd.Series(scores, index=df.index)
    
    def _calcular_componente_operacional(self, df):
        """
        Componente 4: Condições Operacionais (0-100)
        
        Princípio: Certos padrões operacionais favorecem bioincrustação:
        - Muito tempo parado em porto
        - Baixa utilização (velocidade média baixa)
        - Carregamento constante (água salgada sempre na mesma área)
        """
        scores = []
        
        for _, row in df.iterrows():
            velocidade = row.get('speed', 10)
            duracao = row.get('duration', 24)
            displacement = row.get('displacement', 120000)
            
            # 1. Fator de utilização
            # Velocidade média baixa indica sub-utilização
            if velocidade < 8:
                util_score = 70
            elif velocidade < 12:
                util_score = 40
            else:
                util_score = 20
            
            # 2. Fator de carregamento
            # Displacement muito constante = mesma linha d'água = mais bioincrustação nessa área
            # (Isso requer análise de série temporal, por ora usar valor fixo)
            carga_score = 50
            
            # 3. Tempo em operação contínua
            if duracao > 20:
                tempo_score = 20  # Operação contínua ajuda
            else:
                tempo_score = 60  # Navegação intermitente pior
            
            score = (
                0.50 * util_score +
                0.30 * carga_score +
                0.20 * tempo_score
            )
            
            scores.append(score)
        
        return pd.Series(scores, index=df.index)
    
    def _indice_para_nivel_normam(self, indice):
        """
        Converte índice (0-100) para nível NORMAM (0-4)
        
        Mapeamento baseado em literatura e NORMAM 401:
        - 0-20: Nível 0 (limpo)
        - 20-35: Nível 1 (microincrustação)
        - 35-55: Nível 2 (macroincrustação leve, 1-15%)
        - 55-75: Nível 3 (macroincrustação moderada, 16-40%)
        - 75-100: Nível 4 (macroincrustação pesada, >40%)
        """
        if pd.isna(indice):
            return np.nan
        elif indice < 20:
            return 0
        elif indice < 35:
            return 1
        elif indice < 55:
            return 2
        elif indice < 75:
            return 3
        else:
            return 4
    
    def _nivel_para_status(self, nivel):
        """Converte nível NORMAM para status de alerta"""
        if pd.isna(nivel):
            return 'DESCONHECIDO'
        elif nivel <= 1:
            return 'OK'
        elif nivel == 2:
            return 'ATENÇÃO'
        elif nivel == 3:
            return 'ALERTA'
        else:
            return 'CRÍTICO'
    
    def gerar_relatorio(self, df_processado):
        """
        Gera relatório executivo com recomendações.
        
        Parâmetros:
        -----------
        df_processado : pd.DataFrame
            DataFrame com índices calculados
        
        Retorna:
        --------
        dict : Relatório estruturado
        """
        # Pegar dados mais recentes de cada navio
        if 'shipName' in df_processado.columns and 'startGMTDate' in df_processado.columns:
            df_recente = df_processado.sort_values('startGMTDate').groupby('shipName').tail(1)
        else:
            df_recente = df_processado
        
        relatorio = {
            'data_relatorio': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'resumo_frota': {
                'total_navios': len(df_recente),
                'nivel_0_1': len(df_recente[df_recente['nivel_normam_estimado'] <= 1]),
                'nivel_2': len(df_recente[df_recente['nivel_normam_estimado'] == 2]),
                'nivel_3': len(df_recente[df_recente['nivel_normam_estimado'] == 3]),
                'nivel_4': len(df_recente[df_recente['nivel_normam_estimado'] >= 4]),
            },
            'navios_criticos': [],
            'navios_atencao': [],
            'recomendacoes': []
        }
        
        # Navios em estado crítico
        criticos = df_recente[df_recente['nivel_normam_estimado'] >= 4]
        for _, navio in criticos.iterrows():
            relatorio['navios_criticos'].append({
                'nome': navio.get('shipName', 'N/A'),
                'indice': round(navio.get('indice_bioincrustacao', 0), 1),
                'nivel': int(navio.get('nivel_normam_estimado', 0)),
                'acao': 'URGENTE: Agendar limpeza imediatamente'
            })
        
        # Navios em atenção
        atencao = df_recente[df_recente['nivel_normam_estimado'].isin([2, 3])]
        for _, navio in atencao.iterrows():
            relatorio['navios_atencao'].append({
                'nome': navio.get('shipName', 'N/A'),
                'indice': round(navio.get('indice_bioincrustacao', 0), 1),
                'nivel': int(navio.get('nivel_normam_estimado', 0)),
                'acao': 'Planejar limpeza nos próximos 2-3 meses'
            })
        
        # Recomendações gerais
        indice_medio = df_recente['indice_bioincrustacao'].mean()
        if indice_medio > 60:
            relatorio['recomendacoes'].append(
                "Índice médio da frota está elevado. Considerar programa de limpeza proativa."
            )
        
        if len(criticos) > len(df_recente) * 0.3:
            relatorio['recomendacoes'].append(
                "Mais de 30% da frota em estado crítico. Revisar protocolo de manutenção."
            )
        
        return relatorio


# ============================================================================
# EXEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    # Exemplo com dados mock
    dados_exemplo = pd.DataFrame({
        'sessionId': [1, 2, 3, 4],
        'shipName': ['NAVIO A', 'NAVIO A', 'NAVIO B', 'NAVIO B'],
        'class': ['Aframax', 'Aframax', 'Suezmax', 'Suezmax'],
        'startGMTDate': ['2024-01-01', '2024-06-01', '2024-01-01', '2024-06-01'],
        'distance': [280, 250, 290, 240],
        'speed': [12.0, 10.5, 12.5, 10.0],
        'displacement': [120000, 125000, 140000, 145000],
        'aftDraft': [14.5, 15.0, 15.5, 16.0],
        'fwdDraft': [14.0, 14.5, 15.0, 15.5],
        'TRIM': [0.5, 0.5, 0.5, 0.5],
        'beaufortScale': [3, 4, 3, 5],
        'decLatitude': [-23.5, -10.0, -25.0, -15.0],
        'decLongitude': [-45.0, -38.0, -46.0, -39.0],
        'duration': [24, 24, 24, 24]
    })
    
    modelo = ModeloBioincrustacaoFisico()
    
    resultado = modelo.calcular_indice_bioincrustacao(dados_exemplo, comprimento_navio=250)
    
    print("\n" + "="*80)
    print("RESULTADOS DA ANÁLISE DE BIOINCRUSTAÇÃO")
    print("="*80)
    print(resultado[['shipName', 'startGMTDate', 'indice_bioincrustacao', 
                     'nivel_normam_estimado', 'status_alerta']].to_string(index=False))
    
    relatorio = modelo.gerar_relatorio(resultado)
    print("\n" + "="*80)
    print("RELATÓRIO EXECUTIVO")
    print("="*80)
    print(f"\nResumo da Frota:")
    print(f"  Total de navios: {relatorio['resumo_frota']['total_navios']}")
    print(f"  Nível 0-1 (OK): {relatorio['resumo_frota']['nivel_0_1']}")
    print(f"  Nível 2 (Atenção): {relatorio['resumo_frota']['nivel_2']}")
    print(f"  Nível 3 (Alerta): {relatorio['resumo_frota']['nivel_3']}")
    print(f"  Nível 4 (Crítico): {relatorio['resumo_frota']['nivel_4']}")
    
    if relatorio['navios_criticos']:
        print(f"\nNavios Críticos: {len(relatorio['navios_criticos'])}")
        for navio in relatorio['navios_criticos']:
            print(f"  - {navio['nome']}: Índice {navio['indice']} (Nível {navio['nivel']})")
    
    if relatorio['recomendacoes']:
        print(f"\nRecomendações:")
        for rec in relatorio['recomendacoes']:
            print(f"  - {rec}")
