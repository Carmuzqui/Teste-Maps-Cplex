"""
Modelo FCSA MILP - Implementação baseada na tese de Caio dos Santos (UNICAMP, 2025).
Foco: Localização e dimensionamento de estações com integração fotovoltaica.
"""

import pandas as pd
import yaml
import numpy as np
from pathlib import Path
from docplex.mp.model import Model
import time
from math import radians, cos, sin, asin, sqrt

class FCSA_MILP:
    def __init__(self, pasta_problema: str):
        self.pasta = Path(pasta_problema)
        self._carregar_dados()
        self._calcular_fator_vp()
        self._calcular_subconjuntos_cobertura() # Pré-processamento
        self._agregar_demanda()                 # Consolidação da demanda
        self._calcular_big_m()
        self.modelo = None
        self.solucao = {}
        
    def _carregar_dados(self):
        """Carrega parâmetros conforme tabela de símbolos da tese"""
        with open(self.pasta / 'config_geral.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        self.alpha = config['parametros_financeiros']['alpha'] # Taxa de juros
        self.Delta_h = config['parametros_financeiros']['Delta_h'] # Horizonte temporal
        self.h = config['parametros_financeiros']['h'] # Período inicial
        self.time_limit = config['solver']['time_limit']
        self.mip_gap = config['solver']['mip_gap']
        self.log_output = config['solver']['log_output']
        self.raio_cobertura_km = config['parametros_otimizacao'].get('raio_cobertura_km', 25.0) # r-bar
        
        # Carregamento de CSVs (grafos e custos)
        links = pd.read_csv(self.pasta / 'links.csv')
        custos_pv = pd.read_csv(self.pasta / 'custos_carports_pv.csv')
        tarifas = pd.read_csv(self.pasta / 'tarifas_energia.csv')
        demanda = pd.read_csv(self.pasta / 'demanda_energia.csv')
        irradiacao = pd.read_csv(self.pasta / 'irradiacao_solar.csv')
        transporte = pd.read_csv(self.pasta / 'parametros_transporte.csv')
        areas = pd.read_csv(self.pasta / 'areas_disponiveis.csv')
        
        self.L = [int(x) for x in links['link_id'].tolist()] # Conjunto L
        self.T = list(range(24)) # Conjunto T
        self.K = [int(x) for x in custos_pv['tipo_pv'].tolist()] # Conjunto K
        
        self.c_CS = pd.read_csv(self.pasta / 'custos_estacoes.csv').set_index('link_id')['custo_instalacao_reais'].to_dict()
        self.c_PV = custos_pv.set_index('tipo_pv')['custo_instalacao_reais'].to_dict()
        self.P_k = custos_pv.set_index('tipo_pv')['potencia_kw'].to_dict() # P_k
        self.a_k = custos_pv.set_index('tipo_pv')['area_m2'].to_dict() # a_k
        self.c_e = tarifas.set_index('periodo')['tarifa_reais_kwh'].to_dict() # c_t^e
        self.cp = areas.set_index('link_id')['area_disponivel_m2'].to_dict() # cp_l
        self.rho = transporte.set_index('link_id')['fluxo_agregado_veiculos_dia'].to_dict() # rho_l
        self.beta = transporte.set_index('link_id')['fator_beneficio'].to_dict() # beta_l
        self.a_max = config['parametros_area']['a'] # Coeficiente de área útil a-bar
        
        self.E_d_original = demanda.set_index(['link_id', 'periodo'])['demanda_kwh'].to_dict() # E_l,t^d
        self.sh = irradiacao.set_index(['link_id', 'periodo'])['irradiacao_normalizada'].to_dict() # sh_l,t
        self.coordenadas = links.set_index('link_id')[['latitude', 'longitude']].to_dict('index')

    def _haversine(self, lat1, lon1, lat2, lon2):
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        return 2 * asin(sqrt(sin((lat2-lat1)/2)**2 + cos(lat1)*cos(lat2)*sin((lon2-lon1)/2)**2)) * 6371

    def _calcular_subconjuntos_cobertura(self):
        """Define os subconjuntos L_l^r baseados no raio de cobertura """
        self.L_i = {}
        for l in self.L:
            self.L_i[l] = [i for i in self.L if self._haversine(
                self.coordenadas[l]['latitude'], self.coordenadas[l]['longitude'], 
                self.coordenadas[i]['latitude'], self.coordenadas[i]['longitude']) <= self.raio_cobertura_km]

    def _agregar_demanda(self):
        """Soma as demandas individuais das arestas cobertas para cada local candidato """
        self.E_d = {}
        for l in self.L:
            for t in self.T:
                # Cada local l assume a demanda de todas as arestas i que ele cobre
                self.E_d[(l, t)] = sum(self.E_d_original.get((i, t), 0) for i in self.L_i[l])

    def _calcular_fator_vp(self):
        """Calcula o fator de Valor Presente conforme Equação (3) [cite: 69]"""
        term = (1 + self.alpha)**self.Delta_h
        self.fator_vp = (term - 1) / (self.alpha * (1 + self.alpha)**self.h * term)

    def _calcular_big_m(self):
        self.BIG_M = max(self.E_d.values()) * 2.0

    def construir(self):
        m = Model('FCSA_MILP_Tese_Caio')
        
        # VARIÁVEIS
        x = m.binary_var_dict(self.L, name='x') # Alocação de estação no trecho l
        w = {(l,k): m.binary_var(name=f'w_{l}_{k}') for l in self.L for k in self.K} # Sistema PV tipo k no trecho l
        E = m.continuous_var_dict([(l,t) for l in self.L for t in self.T], lb=0, name='E') # Suprimento da rede
        E_pv = m.continuous_var_dict([(l,t) for l in self.L for t in self.T], lb=0, name='E_pv') # Geração fotovoltaica
        E_minus_nm = m.continuous_var_dict([(l,t) for l in self.L for t in self.T], lb=0, name='E_minus_nm') # Importação créditos
        E_plus_nm = m.continuous_var_dict([(l,t) for l in self.L for t in self.T], lb=0, name='E_plus_nm') # Exportação créditos
        E_nm = m.continuous_var_dict(self.T, lb=0, name='E_nm') # Saldo acumulado de créditos
        
        # Auxiliares para linearização do excedente PV (E_lot)
        E_lot = m.continuous_var_dict([(l,t) for l in self.L for t in self.T], lb=0, name='E_lot')
        x_aux = m.binary_var_dict([(l,t) for l in self.L for t in self.T], name='x_aux')

        # FUNÇÕES OBJETIVO
        C_in = m.sum(self.c_CS[l]*x[l] for l in self.L) + m.sum(self.c_PV[k]*w[l,k] for l in self.L for k in self.K)
        C_op = self.fator_vp * m.sum(self.c_e[t]*E[l,t] for l in self.L for t in self.T)
        f_trans = m.sum(x[l]*self.rho[l]*self.beta[l] for l in self.L) # f (benefícios de transporte)

        # RESTRIÇÕES
        # (4) Balanço energético: suprimento + PV + importação = demanda Atendida + exportação
        for l in self.L:
            for t in self.T:
                m.add_constraint(E[l,t] + E_pv[l,t] + E_minus_nm[l,t] == x[l]*self.E_d[l,t] + E_plus_nm[l,t])

        # (5) Geração PV
        for l in self.L:
            for t in self.T:
                m.add_constraint(E_pv[l,t] == m.sum(w[l,k]*self.sh.get((l,t),0)*self.P_k[k] for k in self.K))

        # (6, 8, 9) Gerenciamento de créditos e exportação (linearização)
        for l in self.L:
            for t in self.T:
                # E_lot = max(0, E_pv - x*E_d)
                m.add_constraint(E_lot[l,t] >= E_pv[l,t] - x[l]*self.E_d[l,t])
                m.add_constraint(E_lot[l,t] <= self.BIG_M * x_aux[l,t])
                m.add_constraint(E_lot[l,t] <= E_pv[l,t] - x[l]*self.E_d[l,t] + self.BIG_M*(1-x_aux[l,t]))
                m.add_constraint(E_plus_nm[l,t] <= E_lot[l,t])

        # (7, 8, 9) Balanço e limite de importação
        for idx, t in enumerate(self.T):
            if idx == 0:
                m.add_constraint(E_nm[t] == m.sum(E_plus_nm[l,t] - E_minus_nm[l,t] for l in self.L))
                for l in self.L: m.add_constraint(E_minus_nm[l,t] == 0)
            else:
                m.add_constraint(E_nm[t] == E_nm[self.T[idx-1]] + m.sum(E_plus_nm[l,t] - E_minus_nm[l,t] for l in self.L))
                for l in self.L: m.add_constraint(m.sum(E_minus_nm[i,t] for i in self.L) <= E_nm[self.T[idx-1]])

        # (10) Cobertura de todos os trechos viários
        for i in self.L:
            m.add_constraint(m.sum(x[l] for l in self.L if i in self.L_i[l]) >= 1)

        # (11, 12) Restrições de área e lógica PV
        for l in self.L:
            m.add_constraint(m.sum(self.a_k[k]*w[l,k] for k in self.K) <= x[l]*self.cp[l]*self.a_max)
            m.add_constraint(m.sum(w[l,k] for k in self.K) <= x[l])

        self.modelo = m
        self._objs = {'C_in': C_in, 'C_op': C_op, 'f_trans': f_trans}
        self._vars = {'x': x, 'w': w, 'E': E, 'E_pv': E_pv, 'E_nm': E_nm, 'E_plus_nm': E_plus_nm, 'E_minus_nm': E_minus_nm}

    def resolver(self):
        """Abordagem Lexicográfica em duas etapas sequenciais [cite: 36, 1876]"""
        if not self.modelo: self.construir()
        self.modelo.parameters.mip.tolerances.mipgap = self.mip_gap
        
        # Passo 1: Minimizar f (tenefícios de transporte)
        self.modelo.minimize(self._objs['f_trans'])
        sol1 = self.modelo.solve(log_output=self.log_output)
        if not sol1: return False
        f_otimo = sol1.objective_value

        # Passo 2: Minimizar custos Econômicos mantendo f*
        self.modelo.add_constraint(self._objs['f_trans'] <= f_otimo)
        self.modelo.minimize(self._objs['C_in'] + self._objs['C_op'])
        sol2 = self.modelo.solve(log_output=self.log_output)
        
        if sol2:
            self._extrair_solucao(sol2, f_otimo)
            return True
        return False

    def _extrair_solucao(self, sol, f_otimo):
        """Extrai solução detalhada garantindo compatibilidade total com o dashboard"""
        x = self._vars['x']
        w = self._vars['w']
        E = self._vars['E']
        E_pv = self._vars['E_pv']
        E_nm = self._vars['E_nm']
        E_plus_nm = self._vars['E_plus_nm']
        E_minus_nm = self._vars['E_minus_nm']
        
        # Identificar estações e carports
        est = [l for l in self.L if x[l].solution_value > 0.5]
        carports = {l: k for l in est for k in self.K if w[l,k].solution_value > 0.5}
        
        # Calcular links cobertos conforme raio r-bar
        links_cobertos = set()
        for i in self.L:
            for j in est:
                if i in self.L_i[j]:
                    links_cobertos.add(i)
                    break
        
        # Consolidação financeira
        custo_inv = sum(self.c_CS[l] for l in est) + sum(self.c_PV[k] for k in carports.values())
        custo_op = self.fator_vp * sum(self.c_e[t] * E[l,t].solution_value for l in est for t in self.T)
        
        self.solucao = {
            'custo_total': sol.objective_value,
            'custo_investimento': custo_inv,
            'custo_operacao_vp': custo_op,
            'f_otimo': f_otimo,
            'estacoes_instaladas': est,
            'num_estacoes': len(est), 
            'carports_instalados': carports,
            'links_cobertos': sorted(list(links_cobertos)),
            'taxa_cobertura_%': (len(links_cobertos) / len(self.L)) * 100 if self.L else 0,
            'energia_pv_kwh': sum(E_pv[l,t].solution_value for l in est for t in self.T),
            'energia_comprada_kwh': sum(E[l,t].solution_value for l in est for t in self.T),
            'energia_exportada_kwh': sum(E_plus_nm[l,t].solution_value for l in est for t in self.T),
            'energia_importada_kwh': sum(E_minus_nm[l,t].solution_value for l in est for t in self.T),
            'creditos_finais_kwh': E_nm[self.T[-1]].solution_value if self.T else 0
        }