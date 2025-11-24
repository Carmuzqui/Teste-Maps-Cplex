"""
Modelo FCSA MILP
Baseado na tese de Caio dos Santos
"""

import pandas as pd
import yaml
import numpy as np
from pathlib import Path
from docplex.mp.model import Model
import time
from typing import Dict, List, Tuple
from math import radians, cos, sin, asin, sqrt


class FCSA_MILP:
    """Modelo FCSA MILP para alocação de estações de recarga rápida com PV"""
    
    def __init__(self, pasta_problema: str):
        """
        Inicializa modelo carregando dados da pasta do problema
        
        Args:
            pasta_problema: Caminho para pasta com arquivos do problema
                           Ex: 'dados/problema0'
        """
        self.pasta = Path(pasta_problema)
        self._carregar_dados()
        self._calcular_fator_vp()
        self._calcular_subconjuntos_cobertura()
        self._calcular_big_m()
        self.modelo = None
        self.solucao = {}
        
    def _carregar_dados(self):
        """Carrega todos os arquivos de dados"""
        # Config geral
        with open(self.pasta / 'config_geral.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        self.alpha = config['parametros_financeiros']['alpha']
        self.Delta_h = config['parametros_financeiros']['Delta_h']
        self.h = config['parametros_financeiros']['h']
        self.min_estacoes = config['parametros_otimizacao']['min_estacoes']
        self.a = config['parametros_area']['a']
        self.time_limit = config['solver']['time_limit']
        self.mip_gap = config['solver']['mip_gap']
        self.log_output = config['solver']['log_output']
        
        # Raio de cobertura
        self.raio_cobertura_km = config['parametros_otimizacao'].get('raio_cobertura_km', 3.0)
        
        # CSVs
        links = pd.read_csv(self.pasta / 'links.csv')
        custos_est = pd.read_csv(self.pasta / 'custos_estacoes.csv')
        custos_pv = pd.read_csv(self.pasta / 'custos_carports_pv.csv')
        tarifas = pd.read_csv(self.pasta / 'tarifas_energia.csv')
        demanda = pd.read_csv(self.pasta / 'demanda_energia.csv')
        irradiacao = pd.read_csv(self.pasta / 'irradiacao_solar.csv')
        transporte = pd.read_csv(self.pasta / 'parametros_transporte.csv')
        areas = pd.read_csv(self.pasta / 'areas_disponiveis.csv')
        
        # Conjuntos
        self.L = [int(x) for x in links['link_id'].tolist()]
        self.T = list(range(24))
        self.K = [int(x) for x in custos_pv['tipo_pv'].tolist()]
        
        # Parâmetros
        self.c_CS = custos_est.set_index('link_id')['custo_instalacao_reais'].to_dict()
        self.c_PV = custos_pv.set_index('tipo_pv')['custo_instalacao_reais'].to_dict()
        self.P_k = custos_pv.set_index('tipo_pv')['potencia_kw'].to_dict()
        self.a_k = custos_pv.set_index('tipo_pv')['area_m2'].to_dict()
        self.c_e = tarifas.set_index('periodo')['tarifa_reais_kwh'].to_dict()
        self.cp = areas.set_index('link_id')['area_disponivel_m2'].to_dict()
        self.rho = transporte.set_index('link_id')['fluxo_agregado_veiculos_dia'].to_dict()
        self.beta = transporte.set_index('link_id')['fator_beneficio'].to_dict()
        
        # Demanda original (não agregada)
        self.E_d = demanda.set_index(['link_id', 'periodo'])['demanda_kwh'].to_dict()
        self.sh = irradiacao.set_index(['link_id', 'periodo'])['irradiacao_normalizada'].to_dict()
        
        # Coordenadas geográficas
        self.df_links = links
        self.coordenadas = links.set_index('link_id')[['latitude', 'longitude']].to_dict('index')
        
    def _haversine(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calcula distância entre dois pontos geográficos (fórmula de Haversine)"""
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371  # Raio da Terra em km
        return c * r
    
    def _calcular_subconjuntos_cobertura(self):
        """
        Calcula subconjuntos L_i baseados em distância geográfica
        
        L_i: Links que podem COBRIR o link i (para restrição 10)
        
        IMPORTANTE: Cobertura não significa atendimento de demanda.
        Cada estação atende APENAS sua própria demanda.
        """
        print(f"\n🗺️  Calculando subconjuntos de cobertura (raio: {self.raio_cobertura_km} km)...")
        
        self.L_i = {i: [] for i in self.L}
        
        # Auto-cobertura garantida
        for i in self.L:
            self.L_i[i].append(i)
        
        # Adicionar vizinhos dentro do raio
        for i in self.L:
            lat_i = self.coordenadas[i]['latitude']
            lon_i = self.coordenadas[i]['longitude']
            
            for j in self.L:
                if i == j:
                    continue
                    
                lat_j = self.coordenadas[j]['latitude']
                lon_j = self.coordenadas[j]['longitude']
                
                dist_km = self._haversine(lat_i, lon_i, lat_j, lon_j)
                
                if dist_km <= self.raio_cobertura_km:
                    self.L_i[i].append(j)
        
        # Estatísticas
        avg_cobertores = np.mean([len(self.L_i[i]) for i in self.L])
        
        print(f"   ✓ Média de estações que podem cobrir cada link: {avg_cobertores:.1f}")
        print(f"   ℹ️  NOTA: Cobertura ≠ Atendimento de demanda")
        print(f"   ℹ️  Cada estação atende APENAS sua própria demanda")
        
        # Salvar matriz
        self._salvar_matriz_cobertura()
        
    def _salvar_matriz_cobertura(self):
        """Salva matriz de cobertura para análise"""
        dados_cobertura = []
        for i in self.L:
            for j in self.L_i[i]:
                lat_i = self.coordenadas[i]['latitude']
                lon_i = self.coordenadas[i]['longitude']
                lat_j = self.coordenadas[j]['latitude']
                lon_j = self.coordenadas[j]['longitude']
                dist = self._haversine(lat_i, lon_i, lat_j, lon_j)
                
                dados_cobertura.append({
                    'link_destino': i,
                    'link_cobertor': j,
                    'distancia_km': round(dist, 2)
                })
        
        df_cob = pd.DataFrame(dados_cobertura)
        df_cob.to_csv(self.pasta / 'matriz_cobertura_calculada.csv', index=False)
        print(f"   ✓ Matriz salva: {self.pasta / 'matriz_cobertura_calculada.csv'}")
    
    def _calcular_fator_vp(self):
        """Calcula fator de valor presente"""
        num = (1 + self.alpha)**self.Delta_h - 1
        den = self.alpha * (1 + self.alpha)**self.h * (1 + self.alpha)**self.Delta_h
        self.fator_vp = num / den
        
    def _calcular_big_m(self):
        """Calcula Big-M baseado em DEMANDA ORIGINAL (não agregada)"""
        # Máxima geração PV possível
        max_pv = max(self.P_k[k] * self.sh.get((l, t), 0) 
                     for l in self.L for t in self.T for k in self.K)
        
        # Demanda original (cada estação atende apenas sua demanda)
        max_dem = max(self.E_d.values())
        
        self.BIG_M = max(max_pv, max_dem) * 1.5
        
        print(f"\n🔢 Parâmetros derivados:")
        print(f"   ✓ Fator VP ({self.Delta_h} anos): {self.fator_vp:.4f}")
        print(f"   ✓ Máx PV possível: {max_pv:,.0f} kWh")
        print(f"   ✓ Máx demanda (original): {max_dem:,.0f} kWh")
        print(f"   ✓ Big-M calculado: {self.BIG_M:,.0f} kWh")
        
    def construir(self):
        """
        Constrói modelo MILP conforme tese de Caio
        
        Restrições numeradas conforme Capítulo 4 da tese
        """
        print(f"\n{'='*80}\n🔧 CONSTRUINDO MODELO FCSA MILP\n{'='*80}")
        
        m = Model('FCSA_MILP_Exato_Caio')
        
        # === VARIÁVEIS ===
        x = m.binary_var_dict(self.L, name='x')
        w = {(l,k): m.binary_var(name=f'w_{l}_{k}') for l in self.L for k in self.K}
        E = m.continuous_var_dict([(l,t) for l in self.L for t in self.T], lb=0, name='E')
        E_pv = m.continuous_var_dict([(l,t) for l in self.L for t in self.T], lb=0, name='E_pv')
        E_minus_nm = m.continuous_var_dict([(l,t) for l in self.L for t in self.T], lb=0, name='E_minus_nm')
        E_plus_nm = m.continuous_var_dict([(l,t) for l in self.L for t in self.T], lb=0, name='E_plus_nm')
        E_lot = m.continuous_var_dict([(l,t) for l in self.L for t in self.T], lb=0, name='E_lot')
        E_nm = m.continuous_var_dict(self.T, lb=0, name='E_nm')
        E_d_eff = m.continuous_var_dict([(l,t) for l in self.L for t in self.T], lb=0, name='E_d_eff')
        x_aux = m.binary_var_dict([(l,t) for l in self.L for t in self.T], name='x_aux')
        
        print(f"✅ Variáveis: {m.number_of_variables}")
        
        # === COMPONENTES DA FUNÇÃO OBJETIVO ===
        self._C_in = m.sum(self.c_CS[l]*x[l] for l in self.L) + \
                     m.sum(self.c_PV[k]*w[l,k] for l in self.L for k in self.K)
        
        self._C_op = self.fator_vp * m.sum(self.c_e[t]*E[l,t] for l in self.L for t in self.T)
        
        self._f_trans = m.sum(x[l]*self.rho[l]*self.beta[l] for l in self.L)
        
        # === RESTRIÇÕES (numeradas conforme tese) ===
        
        print(f"\n📋 Adicionando restrições (numeração da tese):")             
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # DEMANDA EFETIVA (Linearização: E_d_eff = x_l * E_d)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        E_d_max = max(self.E_d.values())
        for l in self.L:
            for t in self.T:
                Ed = self.E_d.get((l,t), 0)
                m.add_constraint(E_d_eff[l,t] <= E_d_max * x[l], ctname=f'R1a_demanda_{l}_{t}')
                m.add_constraint(E_d_eff[l,t] <= Ed, ctname=f'R1b_demanda_{l}_{t}')
                m.add_constraint(E_d_eff[l,t] >= Ed - E_d_max*(1-x[l]), ctname=f'R1c_demanda_{l}_{t}')
        print(f"   ✓ (1) Demanda efetiva (original): {3*len(self.L)*len(self.T)} restrições")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # (4) BALANÇO ENERGÉTICO
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        for l in self.L:
            for t in self.T:
                m.add_constraint(
                    E_pv[l,t] + E_minus_nm[l,t] + E[l,t] == E_d_eff[l,t] + E_plus_nm[l,t],
                    ctname=f'R4_balanco_{l}_{t}'
                )
        print(f"   ✓ (4) Balanço energético: {len(self.L)*len(self.T)} restrições")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # (5) GERAÇÃO PV
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        for l in self.L:
            for t in self.T:
                m.add_constraint(
                    E_pv[l,t] == m.sum(self.P_k[k]*self.sh.get((l,t),0)*w[l,k] for k in self.K),
                    ctname=f'R5_pv_{l}_{t}'
                )
        print(f"   ✓ (5) Geração PV: {len(self.L)*len(self.T)} restrições")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # (6) LIMITE IMPORTAÇÃO NET-METERING
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        for l in self.L:
            for idx, t in enumerate(self.T):
                if idx > 0:
                    m.add_constraint(E_minus_nm[l,t] <= E_nm[self.T[idx-1]], ctname=f'R6_import_{l}_{t}')
                else:
                    m.add_constraint(E_minus_nm[l,t] == 0, ctname=f'R6_import_inicial_{l}_{t}')
        print(f"   ✓ (6) Limite importação NM: {len(self.L)*len(self.T)} restrições")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # (7) BALANÇO ACUMULATIVO CRÉDITOS NET-METERING
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        for idx, t in enumerate(self.T):
            if idx == 0:
                m.add_constraint(
                    E_nm[t] == m.sum(E_plus_nm[l,t] - E_minus_nm[l,t] for l in self.L),
                    ctname=f'R7_nm_inicial_{t}'
                )
            else:
                m.add_constraint(
                    E_nm[t] == E_nm[self.T[idx-1]] + m.sum(E_plus_nm[l,t] - E_minus_nm[l,t] for l in self.L),
                    ctname=f'R7_nm_acum_{t}'
                )
        print(f"   ✓ (7) Balanço créditos NM: {len(self.T)} restrições")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # (8) LINEARIZAÇÃO E_lot = max{0, E_pv - E_d_eff}
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        for l in self.L:
            for t in self.T:
                m.add_constraint(E_lot[l,t] >= E_pv[l,t] - E_d_eff[l,t], ctname=f'R8a_lin_{l}_{t}')
                m.add_constraint(E_lot[l,t] <= self.BIG_M * x_aux[l,t], ctname=f'R8b_lin_{l}_{t}')
                m.add_constraint(E_lot[l,t] <= E_pv[l,t] - E_d_eff[l,t] + self.BIG_M*(1-x_aux[l,t]), ctname=f'R8c_lin_{l}_{t}')
        print(f"   ✓ (8) Linearização max: {3*len(self.L)*len(self.T)} restrições")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # (9) LIMITE EXPORTAÇÃO NET-METERING
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        for l in self.L:
            for t in self.T:
                m.add_constraint(E_plus_nm[l,t] <= E_lot[l,t], ctname=f'R9_export_{l}_{t}')
        print(f"   ✓ (9) Limite exportação NM: {len(self.L)*len(self.T)} restrições")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # (10) COBERTURA ESPACIAL
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        for i in self.L:
            m.add_constraint(
                m.sum(x[j] for j in self.L_i[i]) >= 1,
                ctname=f'R10_cobertura_{i}'
            )
        print(f"   ✓ (10) Cobertura espacial: {len(self.L)} restrições")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # (11) ÁREA CARPORT
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        for l in self.L:
            m.add_constraint(
                m.sum(self.a_k[k]*w[l,k] for k in self.K) <= self.cp[l]*self.a,
                ctname=f'R11_area_{l}'
            )
        print(f"   ✓ (11) Área carport: {len(self.L)} restrições")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # (12) CARPORT REQUER ESTAÇÃO
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        for l in self.L:
            m.add_constraint(
                m.sum(w[l,k] for k in self.K) <= x[l],
                ctname=f'R12_carport_{l}'
            )
        print(f"   ✓ (12) Carport requer estação: {len(self.L)} restrições")
        
        print(f"\n✅ TOTAL: {m.number_of_constraints} restrições")
        print(f"{'='*80}")
        
        self.modelo = m
        self._vars = {'x': x, 'w': w, 'E': E, 'E_pv': E_pv, 'E_minus_nm': E_minus_nm,
                      'E_plus_nm': E_plus_nm, 'E_nm': E_nm, 'E_d_eff': E_d_eff}
        
    def resolver(self):
        """
        Resolve modelo usando método lexicográfico (Algoritmo 1)
        
        Paso 1: min f = Σ(xl·ρl·βl)
        Paso 2: min (Cin + Cop) s.t. f = f*
        """
        if not self.modelo:
            self.construir()
        
        self.modelo.parameters.mip.tolerances.mipgap = self.mip_gap
        self.modelo.parameters.timelimit = self.time_limit
        self.modelo.parameters.threads = 0
        
        tempo_total = 0
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # PASO 1: MINIMIZAR f (Algoritmo 1, líneas 4-5)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        print(f"\n{'='*80}\n📊 PASO 1: MINIMIZANDO f\n{'='*80}")
        print(f"   f = Σ(xl·ρl·βl)")
        print(f"   ℹ️  Minimizar f = Instalar em links com MAIOR demanda VE")
        print(f"   ℹ️  βl baixo → advl/tf alto → MUITOS usuários VE")
        
        # ✅ CORREÇÃO: MINIMIZAR f (não maximizar)
        self.modelo.minimize(self._f_trans)
        
        t0 = time.time()
        sol1 = self.modelo.solve(log_output=self.log_output)
        tempo1 = time.time() - t0
        tempo_total += tempo1
        
        if not sol1:
            print(f"\n❌ PASO 1 INFACTÍVEL")
            return False
        
        f_otimo = sol1.objective_value
        num_est_p1 = sum(1 for l in self.L if self._vars['x'][l].solution_value > 0.5)
        est_p1 = [l for l in self.L if self._vars['x'][l].solution_value > 0.5]
        
        print(f"\n✅ PASO 1 CONCLUÍDO:")
        print(f"   ⏱️  Tempo: {tempo1:.2f}s")
        print(f"   📊 f* = {f_otimo:.6f} (menor = melhor cobertura)")
        print(f"   ⚡ Estações: {num_est_p1} → {est_p1}")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # PASO 2: MINIMIZAR Cin + Cop mantendo f = f* (Algoritmo 1, líneas 7-9)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        print(f"\n{'='*80}\n💰 PASO 2: MINIMIZANDO CUSTOS\n{'='*80}")
        print(f"   Restricción (16): Σ(xl·ρl·βl) = {f_otimo:.6f}")
        
        # ✅ CORREÇÃO: Restricción de IGUALDAD (não >=)
        # self.modelo.add_constraint(self._f_trans == f_otimo, ctname='R16_lexicografica')
        self.modelo.add_constraint(self._f_trans <= f_otimo, ctname='R16_lexicografica')
        
        # Minimizar custos
        self.modelo.minimize(self._C_in + self._C_op)
        
        t0 = time.time()
        sol2 = self.modelo.solve(log_output=self.log_output)
        tempo2 = time.time() - t0
        tempo_total += tempo2
        
        if not sol2:
            print(f"\n❌ PASO 2 INFACTÍVEL")
            return False
        
        print(f"\n✅ PASO 2 CONCLUÍDO:")
        print(f"   ⏱️  Tempo: {tempo2:.2f}s")
        print(f"   💰 Custo: R$ {sol2.objective_value:,.2f}")
        
        self._extrair_solucao(tempo_total, f_otimo)
        self._imprimir_resultados()
        
        return True
    
    def _extrair_solucao(self, tempo: float, f_otimo: float):
        """Extrai solução"""
        x = self._vars['x']
        w = self._vars['w']
        E = self._vars['E']
        E_pv = self._vars['E_pv']
        E_nm = self._vars['E_nm']
        E_plus_nm = self._vars['E_plus_nm']
        E_minus_nm = self._vars['E_minus_nm']
        
        est = [l for l in self.L if x[l].solution_value > 0.5]
        cp_inst = {l: k for l in est for k in self.K if w[l,k].solution_value > 0.5}
        
        custo_inv = sum(self.c_CS[l] for l in est) + sum(self.c_PV[k] for k in cp_inst.values())
        custo_op = self.fator_vp * sum(self.c_e[t]*E[l,t].solution_value for l in est for t in self.T)
        
        # Calcular links cobertos
        links_cobertos = set()
        for i in self.L:
            for j in est:
                if j in self.L_i[i]:
                    links_cobertos.add(i)
                    break
        
        self.solucao = {
            'tempo_s': tempo,
            'gap_%': self.modelo.solve_details.mip_relative_gap * 100,
            'valor_objetivo': self.modelo.objective_value,
            'f_otimo': f_otimo,
            'estacoes_instaladas': est,
            'num_estacoes': len(est),
            'links_cobertos': sorted(links_cobertos),
            'num_links_cobertos': len(links_cobertos),
            'taxa_cobertura_%': (len(links_cobertos) / len(self.L)) * 100,
            'carports_instalados': cp_inst,
            'custo_investimento': custo_inv,
            'custo_operacao_vp': custo_op,
            'custo_total': custo_inv + custo_op,
            'energia_comprada_kwh': sum(E[l,t].solution_value for l in est for t in self.T),
            'energia_pv_kwh': sum(E_pv[l,t].solution_value for l in est for t in self.T),
            'energia_exportada_kwh': sum(E_plus_nm[l,t].solution_value for l in est for t in self.T),
            'energia_importada_kwh': sum(E_minus_nm[l,t].solution_value for l in est for t in self.T),
            'creditos_finais_kwh': E_nm[self.T[-1]].solution_value
        }
        
    def _imprimir_resultados(self):
        """Imprime resultados"""
        s = self.solucao
        print(f"\n{'='*80}\n📊 SOLUÇÃO FINAL (MODELO EXATO CAIO)\n{'='*80}")
        print(f"⏱️  Tempo total: {s['tempo_s']:.2f}s | Gap: {s['gap_%']:.2f}%")
        print(f"💰 Custo total: R$ {s['custo_total']:,.2f}")
        print(f"📊 f* = {s['f_otimo']:.6f}\n")
        
        print(f"🗺️  COBERTURA ESPACIAL:")
        print(f"   ⚡ Estações instaladas: {s['num_estacoes']} → {s['estacoes_instaladas']}")
        print(f"   ☀️  Carports PV: {len(s['carports_instalados'])}")
        for l, k in s['carports_instalados'].items():
            print(f"      → Link {l}: Tipo {k} ({self.P_k[k]} kW)")
        print(f"   📍 Links cobertos: {s['num_links_cobertos']}/{len(self.L)} ({s['taxa_cobertura_%']:.0f}%)\n")
        
        print(f"💰 CUSTOS:")
        print(f"   🏗️  Investimento: R$ {s['custo_investimento']:,.2f}")
        print(f"   ⚡ Operação VP ({self.Delta_h} anos): R$ {s['custo_operacao_vp']:,.2f}\n")
        
        print(f"⚡ ENERGIA:")
        print(f"   🔌 Comprada: {s['energia_comprada_kwh']:,.0f} kWh")
        print(f"   ☀️  Gerada PV: {s['energia_pv_kwh']:,.0f} kWh")
        print(f"   📤 Exportada NM: {s['energia_exportada_kwh']:,.0f} kWh")
        print(f"   📥 Importada NM: {s['energia_importada_kwh']:,.0f} kWh")
        print(f"   💾 Créditos finais: {s['creditos_finais_kwh']:,.0f} kWh")
        print(f"{'='*80}")


def resolver_problema(pasta: str) -> FCSA_MILP:
    """Resolve problema FCSA MILP completo"""
    modelo = FCSA_MILP(pasta)
    modelo.resolver()
    return modelo


if __name__ == '__main__':
    modelo = resolver_problema('dados/problema0')