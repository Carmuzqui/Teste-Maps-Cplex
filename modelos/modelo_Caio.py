"""
Modelo FCSA MILP - Versão Compacta e Modular
Baseado na tese de Caio dos Santos (Unicamp, 2021)
Autor: Carlos Murgueitio
Data: 2025-01-15
"""

import pandas as pd
import yaml
from pathlib import Path
from docplex.mp.model import Model
import time
from typing import Dict, Tuple


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
        self._calcular_parametros_derivados()
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
        self.gamma = config['parametros_otimizacao']['gamma']
        self.min_estacoes = config['parametros_otimizacao']['min_estacoes']
        self.a = config['parametros_area']['a']
        self.time_limit = config['solver']['time_limit']
        self.mip_gap = config['solver']['mip_gap']
        self.log_output = config['solver']['log_output']
        
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
        self.L = links['link_id'].tolist()
        self.T = list(range(24))
        self.K = custos_pv['tipo_pv'].tolist()
        
        # Parâmetros em dicionários
        self.c_CS = custos_est.set_index('link_id')['custo_instalacao_reais'].to_dict()
        self.c_PV = custos_pv.set_index('tipo_pv')['custo_instalacao_reais'].to_dict()
        self.P_k = custos_pv.set_index('tipo_pv')['potencia_kw'].to_dict()
        self.a_k = custos_pv.set_index('tipo_pv')['area_m2'].to_dict()
        self.c_e = tarifas.set_index('periodo')['tarifa_reais_kwh'].to_dict()
        self.cp = areas.set_index('link_id')['area_disponivel_m2'].to_dict()
        self.rho = transporte.set_index('link_id')['fluxo_agregado_veiculos_dia'].to_dict()
        self.beta = transporte.set_index('link_id')['fator_beneficio'].to_dict()
        
        # Parâmetros indexados (l,t)
        self.E_d = demanda.set_index(['link_id', 'periodo'])['demanda_kwh'].to_dict()
        self.sh = irradiacao.set_index(['link_id', 'periodo'])['irradiacao_normalizada'].to_dict()
        
        # Guardar DataFrames para geolocalização
        self.df_links = links
        
    def _calcular_parametros_derivados(self):
        """Calcula Big-M e fator de valor presente"""
        # Big-M
        max_pv = max(self.P_k[k] * self.sh.get((l, t), 0) 
                     for l in self.L for t in self.T for k in self.K)
        max_dem = max(self.E_d.values())
        self.BIG_M = max(max_pv, max_dem) * 1.5
        
        # Fator valor presente
        num = (1 + self.alpha)**self.Delta_h - 1
        den = self.alpha * (1 + self.alpha)**self.h * (1 + self.alpha)**self.Delta_h
        self.fator_vp = num / den
        
    def construir(self):
        """Constrói modelo MILP"""
        print(f"\n{'='*80}\n🔧 CONSTRUINDO MODELO FCSA MILP\n{'='*80}")
        print(f"📊 L={len(self.L)} | T={len(self.T)} | K={len(self.K)} | "
              f"γ={self.gamma} | α={self.alpha*100:.0f}%")
        
        m = Model('FCSA_MILP')
        
        # === VARIÁVEIS ===
        x = m.binary_var_dict(self.L, name='x')  # Instalar estação
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
        
        # === FUNÇÃO OBJETIVO ===
        C_in = m.sum(self.c_CS[l]*x[l] for l in self.L) + \
               m.sum(self.c_PV[k]*w[l,k] for l in self.L for k in self.K)
        C_op = self.fator_vp * m.sum(self.c_e[t]*E[l,t] for l in self.L for t in self.T)
        f_trans = self.gamma * m.sum(x[l]*self.rho[l]*self.beta[l] for l in self.L)
        m.minimize(C_in + C_op - f_trans)
        
        # === RESTRIÇÕES ===
        # (0) Cobertura mínima
        m.add_constraint(m.sum(x[l] for l in self.L) >= self.min_estacoes)
        
        # (1) Linearização demanda efetiva: E_d_eff = x_l * E_d
        E_d_max = max(self.E_d.values())
        for l in self.L:
            for t in self.T:
                Ed = self.E_d.get((l,t), 0)
                m.add_constraint(E_d_eff[l,t] <= E_d_max * x[l])
                m.add_constraint(E_d_eff[l,t] <= Ed)
                m.add_constraint(E_d_eff[l,t] >= Ed - E_d_max*(1-x[l]))
        
        # (4) Balanço energético: E_pv + E_minus_nm + E = E_d_eff + E_plus_nm
        for l in self.L:
            for t in self.T:
                m.add_constraint(E_pv[l,t] + E_minus_nm[l,t] + E[l,t] == 
                                E_d_eff[l,t] + E_plus_nm[l,t])
        
        # (5) Geração PV
        for l in self.L:
            for t in self.T:
                m.add_constraint(E_pv[l,t] == m.sum(self.P_k[k]*self.sh.get((l,t),0)*w[l,k] 
                                                     for k in self.K))
        
        # (6) Limite importação net-metering
        for l in self.L:
            for idx, t in enumerate(self.T):
                if idx > 0:
                    m.add_constraint(E_minus_nm[l,t] <= E_nm[self.T[idx-1]])
                else:
                    m.add_constraint(E_minus_nm[l,t] == 0)
        
        # (7) Balanço acumulativo créditos
        for idx, t in enumerate(self.T):
            if idx == 0:
                m.add_constraint(E_nm[t] == m.sum(E_plus_nm[l,t] - E_minus_nm[l,t] for l in self.L))
            else:
                m.add_constraint(E_nm[t] == E_nm[self.T[idx-1]] + 
                                m.sum(E_plus_nm[l,t] - E_minus_nm[l,t] for l in self.L))
        
        # (8) Linearização E_lot = max{0, E_pv - E_d_eff}
        for l in self.L:
            for t in self.T:
                m.add_constraint(E_lot[l,t] >= E_pv[l,t] - E_d_eff[l,t])
                m.add_constraint(E_lot[l,t] <= self.BIG_M * x_aux[l,t])
                m.add_constraint(E_lot[l,t] <= E_pv[l,t] - E_d_eff[l,t] + self.BIG_M*(1-x_aux[l,t]))
        
        # (9) Limite exportação
        for l in self.L:
            for t in self.T:
                m.add_constraint(E_plus_nm[l,t] <= E_lot[l,t])
        
        # (10) Área carport
        for l in self.L:
            m.add_constraint(m.sum(self.a_k[k]*w[l,k] for k in self.K) <= self.cp[l]*self.a)
        
        # (11) Carport requer estação
        for l in self.L:
            m.add_constraint(m.sum(w[l,k] for k in self.K) <= x[l])
        
        print(f"✅ Restrições: {m.number_of_constraints}\n{'='*80}")
        
        self.modelo = m
        self._vars = {'x': x, 'w': w, 'E': E, 'E_pv': E_pv, 'E_minus_nm': E_minus_nm,
                      'E_plus_nm': E_plus_nm, 'E_nm': E_nm}
        
    def resolver(self):
        """Resolve modelo"""
        if not self.modelo:
            self.construir()
            
        print(f"\n{'='*80}\n🚀 RESOLVENDO\n{'='*80}")
        print(f"⏱️  Limite: {self.time_limit}s | Gap: {self.mip_gap*100}%\n{'='*80}")
        
        self.modelo.parameters.mip.tolerances.mipgap = self.mip_gap
        self.modelo.parameters.timelimit = self.time_limit
        self.modelo.parameters.threads = 0
        
        t0 = time.time()
        sol = self.modelo.solve(log_output=self.log_output)
        tempo = time.time() - t0
        
        if sol:
            self._extrair_solucao(tempo)
            self._imprimir_resultados()
            return True
        else:
            print(f"\n{'='*80}\n❌ MODELO INFACTÍVEL\n{'='*80}")
            return False
    
    def _extrair_solucao(self, tempo: float):
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
        
        self.solucao = {
            'tempo_s': tempo,
            'gap_%': self.modelo.solve_details.mip_relative_gap * 100,
            'valor_objetivo': self.modelo.objective_value,
            'estacoes_instaladas': est,
            'num_estacoes': len(est),
            'carports_instalados': cp_inst,
            'custo_investimento': sum(self.c_CS[l] for l in est) + 
                                 sum(self.c_PV[k] for k in cp_inst.values()),
            'custo_operacao_vp': self.fator_vp * sum(self.c_e[t]*E[l,t].solution_value 
                                                     for l in est for t in self.T),
            'beneficio_transporte': sum(self.rho[l]*self.beta[l] for l in est),
            'energia_comprada_kwh': sum(E[l,t].solution_value for l in est for t in self.T),
            'energia_pv_kwh': sum(E_pv[l,t].solution_value for l in est for t in self.T),
            'energia_exportada_kwh': sum(E_plus_nm[l,t].solution_value for l in est for t in self.T),
            'energia_importada_kwh': sum(E_minus_nm[l,t].solution_value for l in est for t in self.T),
            'creditos_finais_kwh': E_nm[self.T[-1]].solution_value
        }
        
    def _imprimir_resultados(self):
        """Imprime resumo"""
        s = self.solucao
        print(f"\n{'='*80}\n✅ SOLUÇÃO ENCONTRADA\n{'='*80}")
        print(f"⏱️  Tempo: {s['tempo_s']:.2f}s | Gap: {s['gap_%']:.2f}%")
        print(f"💰 Valor objetivo: R$ {s['valor_objetivo']:,.2f}\n")
        
        print(f"🏗️  INVESTIMENTO:")
        print(f"   ⚡ Estações: {s['num_estacoes']} → {s['estacoes_instaladas']}")
        print(f"   ☀️  Carports PV: {len(s['carports_instalados'])}")
        print(f"   💰 Custo: R$ {s['custo_investimento']:,.2f}\n")
        
        print(f"💡 OPERAÇÃO ({self.Delta_h} anos):")
        print(f"   💰 Custo VP: R$ {s['custo_operacao_vp']:,.2f}")
        print(f"   🔌 Comprada: {s['energia_comprada_kwh']:,.0f} kWh")
        print(f"   ☀️  Gerada PV: {s['energia_pv_kwh']:,.0f} kWh\n")
        
        print(f"🔋 NET-METERING:")
        print(f"   📤 Exportada: {s['energia_exportada_kwh']:,.0f} kWh")
        print(f"   📥 Importada: {s['energia_importada_kwh']:,.0f} kWh")
        print(f"   💾 Créditos finais: {s['creditos_finais_kwh']:,.0f} kWh\n")
        
        print(f"🚗 TRANSPORTE:")
        print(f"   📊 Benefício: {s['beneficio_transporte']:.1f}")
        print(f"   💡 Contribuição FO: R$ {-self.gamma * s['beneficio_transporte']:,.2f}")
        print(f"{'='*80}\n")
        
        # Detalhes por estação
        for l in s['estacoes_instaladas']:
            k = s['carports_instalados'].get(l)
            print(f"📍 Link {l} ({self.df_links[self.df_links.link_id==l]['nome'].values[0]}):")
            print(f"   - Estação: R$ {self.c_CS[l]:,.0f}")
            if k is not None:
                print(f"   - Carport PV Tipo {k}: {self.P_k[k]} kW (R$ {self.c_PV[k]:,.0f})")
            print(f"   - Benefício: {self.rho[l]*self.beta[l]:.1f}")
        print(f"{'='*80}")


# === FUNÇÃO PRINCIPAL ===
def resolver_problema(pasta: str) -> FCSA_MILP:
    """
    Resolve problema FCSA MILP completo
    
    Args:
        pasta: Caminho para pasta do problema (ex: 'dados/problema0')
    
    Returns:
        Objeto FCSA_MILP com solução
    """
    modelo = FCSA_MILP(pasta)
    modelo.resolver()
    return modelo


if __name__ == '__main__':
    # Resolver problema 0
    modelo = resolver_problema('dados/problema0')