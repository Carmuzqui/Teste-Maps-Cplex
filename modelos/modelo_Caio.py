# """
# Modelo FCSA MILP - Versão Compacta e Modular
# Baseado na tese de Caio dos Santos (Unicamp, 2021)
# Autor: Carlos Murgueitio
# Data: 2025-01-15
# """

# import pandas as pd
# import yaml
# from pathlib import Path
# from docplex.mp.model import Model
# import time
# from typing import Dict, Tuple


# class FCSA_MILP:
#     """Modelo FCSA MILP para alocação de estações de recarga rápida com PV"""
    
#     def __init__(self, pasta_problema: str):
#         """
#         Inicializa modelo carregando dados da pasta do problema
        
#         Args:
#             pasta_problema: Caminho para pasta com arquivos do problema
#                            Ex: 'dados/problema0'
#         """
#         self.pasta = Path(pasta_problema)
#         self._carregar_dados()
#         self._calcular_parametros_derivados()
#         self.modelo = None
#         self.solucao = {}
        
#     def _carregar_dados(self):
#         """Carrega todos os arquivos de dados"""
#         # Config geral
#         with open(self.pasta / 'config_geral.yaml', 'r', encoding='utf-8') as f:
#             config = yaml.safe_load(f)
        
#         self.alpha = config['parametros_financeiros']['alpha']
#         self.Delta_h = config['parametros_financeiros']['Delta_h']
#         self.h = config['parametros_financeiros']['h']
#         self.gamma = config['parametros_otimizacao']['gamma']
#         self.min_estacoes = config['parametros_otimizacao']['min_estacoes']
#         self.a = config['parametros_area']['a']
#         self.time_limit = config['solver']['time_limit']
#         self.mip_gap = config['solver']['mip_gap']
#         self.log_output = config['solver']['log_output']
        
#         # CSVs
#         links = pd.read_csv(self.pasta / 'links.csv')
#         custos_est = pd.read_csv(self.pasta / 'custos_estacoes.csv')
#         custos_pv = pd.read_csv(self.pasta / 'custos_carports_pv.csv')
#         tarifas = pd.read_csv(self.pasta / 'tarifas_energia.csv')
#         demanda = pd.read_csv(self.pasta / 'demanda_energia.csv')
#         irradiacao = pd.read_csv(self.pasta / 'irradiacao_solar.csv')
#         transporte = pd.read_csv(self.pasta / 'parametros_transporte.csv')
#         areas = pd.read_csv(self.pasta / 'areas_disponiveis.csv')
        
#         # Conjuntos
#         self.L = links['link_id'].tolist()
#         self.T = list(range(24))
#         self.K = custos_pv['tipo_pv'].tolist()
        
#         # Parâmetros em dicionários
#         self.c_CS = custos_est.set_index('link_id')['custo_instalacao_reais'].to_dict()
#         self.c_PV = custos_pv.set_index('tipo_pv')['custo_instalacao_reais'].to_dict()
#         self.P_k = custos_pv.set_index('tipo_pv')['potencia_kw'].to_dict()
#         self.a_k = custos_pv.set_index('tipo_pv')['area_m2'].to_dict()
#         self.c_e = tarifas.set_index('periodo')['tarifa_reais_kwh'].to_dict()
#         self.cp = areas.set_index('link_id')['area_disponivel_m2'].to_dict()
#         self.rho = transporte.set_index('link_id')['fluxo_agregado_veiculos_dia'].to_dict()
#         self.beta = transporte.set_index('link_id')['fator_beneficio'].to_dict()
        
#         # Parâmetros indexados (l,t)
#         self.E_d = demanda.set_index(['link_id', 'periodo'])['demanda_kwh'].to_dict()
#         self.sh = irradiacao.set_index(['link_id', 'periodo'])['irradiacao_normalizada'].to_dict()
        
#         # Guardar DataFrames para geolocalização
#         self.df_links = links
        
#     def _calcular_parametros_derivados(self):
#         """Calcula Big-M e fator de valor presente"""
#         # Big-M
#         max_pv = max(self.P_k[k] * self.sh.get((l, t), 0) 
#                      for l in self.L for t in self.T for k in self.K)
#         max_dem = max(self.E_d.values())
#         self.BIG_M = max(max_pv, max_dem) * 1.5
        
#         # Fator valor presente
#         num = (1 + self.alpha)**self.Delta_h - 1
#         den = self.alpha * (1 + self.alpha)**self.h * (1 + self.alpha)**self.Delta_h
#         self.fator_vp = num / den
        
#     def construir(self):
#         """Constrói modelo MILP"""
#         print(f"\n{'='*80}\n🔧 CONSTRUINDO MODELO FCSA MILP\n{'='*80}")
#         print(f"📊 L={len(self.L)} | T={len(self.T)} | K={len(self.K)} | "
#               f"γ={self.gamma} | α={self.alpha*100:.0f}%")
        
#         m = Model('FCSA_MILP')
        
#         # === VARIÁVEIS ===
#         x = m.binary_var_dict(self.L, name='x')  # Instalar estação
#         w = {(l,k): m.binary_var(name=f'w_{l}_{k}') for l in self.L for k in self.K}
#         E = m.continuous_var_dict([(l,t) for l in self.L for t in self.T], lb=0, name='E')
#         E_pv = m.continuous_var_dict([(l,t) for l in self.L for t in self.T], lb=0, name='E_pv')
#         E_minus_nm = m.continuous_var_dict([(l,t) for l in self.L for t in self.T], lb=0, name='E_minus_nm')
#         E_plus_nm = m.continuous_var_dict([(l,t) for l in self.L for t in self.T], lb=0, name='E_plus_nm')
#         E_lot = m.continuous_var_dict([(l,t) for l in self.L for t in self.T], lb=0, name='E_lot')
#         E_nm = m.continuous_var_dict(self.T, lb=0, name='E_nm')
#         E_d_eff = m.continuous_var_dict([(l,t) for l in self.L for t in self.T], lb=0, name='E_d_eff')
#         x_aux = m.binary_var_dict([(l,t) for l in self.L for t in self.T], name='x_aux')
        
#         print(f"✅ Variáveis: {m.number_of_variables}")
        
#         # === FUNÇÃO OBJETIVO ===
#         C_in = m.sum(self.c_CS[l]*x[l] for l in self.L) + \
#                m.sum(self.c_PV[k]*w[l,k] for l in self.L for k in self.K)
#         C_op = self.fator_vp * m.sum(self.c_e[t]*E[l,t] for l in self.L for t in self.T)
#         f_trans = self.gamma * m.sum(x[l]*self.rho[l]*self.beta[l] for l in self.L)
#         m.minimize(C_in + C_op - f_trans)
        
#         # === RESTRIÇÕES ===
#         # (0) Cobertura mínima
#         m.add_constraint(m.sum(x[l] for l in self.L) >= self.min_estacoes)
        
#         # (1) Linearização demanda efetiva: E_d_eff = x_l * E_d
#         E_d_max = max(self.E_d.values())
#         for l in self.L:
#             for t in self.T:
#                 Ed = self.E_d.get((l,t), 0)
#                 m.add_constraint(E_d_eff[l,t] <= E_d_max * x[l])
#                 m.add_constraint(E_d_eff[l,t] <= Ed)
#                 m.add_constraint(E_d_eff[l,t] >= Ed - E_d_max*(1-x[l]))
        
#         # (4) Balanço energético: E_pv + E_minus_nm + E = E_d_eff + E_plus_nm
#         for l in self.L:
#             for t in self.T:
#                 m.add_constraint(E_pv[l,t] + E_minus_nm[l,t] + E[l,t] == 
#                                 E_d_eff[l,t] + E_plus_nm[l,t])
        
#         # (5) Geração PV
#         for l in self.L:
#             for t in self.T:
#                 m.add_constraint(E_pv[l,t] == m.sum(self.P_k[k]*self.sh.get((l,t),0)*w[l,k] 
#                                                      for k in self.K))
        
#         # (6) Limite importação net-metering
#         for l in self.L:
#             for idx, t in enumerate(self.T):
#                 if idx > 0:
#                     m.add_constraint(E_minus_nm[l,t] <= E_nm[self.T[idx-1]])
#                 else:
#                     m.add_constraint(E_minus_nm[l,t] == 0)
        
#         # (7) Balanço acumulativo créditos
#         for idx, t in enumerate(self.T):
#             if idx == 0:
#                 m.add_constraint(E_nm[t] == m.sum(E_plus_nm[l,t] - E_minus_nm[l,t] for l in self.L))
#             else:
#                 m.add_constraint(E_nm[t] == E_nm[self.T[idx-1]] + 
#                                 m.sum(E_plus_nm[l,t] - E_minus_nm[l,t] for l in self.L))
        
#         # (8) Linearização E_lot = max{0, E_pv - E_d_eff}
#         for l in self.L:
#             for t in self.T:
#                 m.add_constraint(E_lot[l,t] >= E_pv[l,t] - E_d_eff[l,t])
#                 m.add_constraint(E_lot[l,t] <= self.BIG_M * x_aux[l,t])
#                 m.add_constraint(E_lot[l,t] <= E_pv[l,t] - E_d_eff[l,t] + self.BIG_M*(1-x_aux[l,t]))
        
#         # (9) Limite exportação
#         for l in self.L:
#             for t in self.T:
#                 m.add_constraint(E_plus_nm[l,t] <= E_lot[l,t])
        
#         # (10) Área carport
#         for l in self.L:
#             m.add_constraint(m.sum(self.a_k[k]*w[l,k] for k in self.K) <= self.cp[l]*self.a)
        
#         # (11) Carport requer estação
#         for l in self.L:
#             m.add_constraint(m.sum(w[l,k] for k in self.K) <= x[l])
        
#         print(f"✅ Restrições: {m.number_of_constraints}\n{'='*80}")
        
#         self.modelo = m
#         self._vars = {'x': x, 'w': w, 'E': E, 'E_pv': E_pv, 'E_minus_nm': E_minus_nm,
#                       'E_plus_nm': E_plus_nm, 'E_nm': E_nm}
        
#     def resolver(self):
#         """Resolve modelo"""
#         if not self.modelo:
#             self.construir()
            
#         print(f"\n{'='*80}\n🚀 RESOLVENDO\n{'='*80}")
#         print(f"⏱️  Limite: {self.time_limit}s | Gap: {self.mip_gap*100}%\n{'='*80}")
        
#         self.modelo.parameters.mip.tolerances.mipgap = self.mip_gap
#         self.modelo.parameters.timelimit = self.time_limit
#         self.modelo.parameters.threads = 0
        
#         t0 = time.time()
#         sol = self.modelo.solve(log_output=self.log_output)
#         tempo = time.time() - t0
        
#         if sol:
#             self._extrair_solucao(tempo)
#             self._imprimir_resultados()
#             return True
#         else:
#             print(f"\n{'='*80}\n❌ MODELO INFACTÍVEL\n{'='*80}")
#             return False
    
#     def _extrair_solucao(self, tempo: float):
#         """Extrai solução"""
#         x = self._vars['x']
#         w = self._vars['w']
#         E = self._vars['E']
#         E_pv = self._vars['E_pv']
#         E_nm = self._vars['E_nm']
#         E_plus_nm = self._vars['E_plus_nm']
#         E_minus_nm = self._vars['E_minus_nm']
        
#         est = [l for l in self.L if x[l].solution_value > 0.5]
#         cp_inst = {l: k for l in est for k in self.K if w[l,k].solution_value > 0.5}
        
#         self.solucao = {
#             'tempo_s': tempo,
#             'gap_%': self.modelo.solve_details.mip_relative_gap * 100,
#             'valor_objetivo': self.modelo.objective_value,
#             'estacoes_instaladas': est,
#             'num_estacoes': len(est),
#             'carports_instalados': cp_inst,
#             'custo_investimento': sum(self.c_CS[l] for l in est) + 
#                                  sum(self.c_PV[k] for k in cp_inst.values()),
#             'custo_operacao_vp': self.fator_vp * sum(self.c_e[t]*E[l,t].solution_value 
#                                                      for l in est for t in self.T),
#             'beneficio_transporte': sum(self.rho[l]*self.beta[l] for l in est),
#             'energia_comprada_kwh': sum(E[l,t].solution_value for l in est for t in self.T),
#             'energia_pv_kwh': sum(E_pv[l,t].solution_value for l in est for t in self.T),
#             'energia_exportada_kwh': sum(E_plus_nm[l,t].solution_value for l in est for t in self.T),
#             'energia_importada_kwh': sum(E_minus_nm[l,t].solution_value for l in est for t in self.T),
#             'creditos_finais_kwh': E_nm[self.T[-1]].solution_value
#         }
        
#     def _imprimir_resultados(self):
#         """Imprime resumo"""
#         s = self.solucao
#         print(f"\n{'='*80}\n✅ SOLUÇÃO ENCONTRADA\n{'='*80}")
#         print(f"⏱️  Tempo: {s['tempo_s']:.2f}s | Gap: {s['gap_%']:.2f}%")
#         print(f"💰 Valor objetivo: R$ {s['valor_objetivo']:,.2f}\n")
        
#         print(f"🏗️  INVESTIMENTO:")
#         print(f"   ⚡ Estações: {s['num_estacoes']} → {s['estacoes_instaladas']}")
#         print(f"   ☀️  Carports PV: {len(s['carports_instalados'])}")
#         print(f"   💰 Custo: R$ {s['custo_investimento']:,.2f}\n")
        
#         print(f"💡 OPERAÇÃO ({self.Delta_h} anos):")
#         print(f"   💰 Custo VP: R$ {s['custo_operacao_vp']:,.2f}")
#         print(f"   🔌 Comprada: {s['energia_comprada_kwh']:,.0f} kWh")
#         print(f"   ☀️  Gerada PV: {s['energia_pv_kwh']:,.0f} kWh\n")
        
#         print(f"🔋 NET-METERING:")
#         print(f"   📤 Exportada: {s['energia_exportada_kwh']:,.0f} kWh")
#         print(f"   📥 Importada: {s['energia_importada_kwh']:,.0f} kWh")
#         print(f"   💾 Créditos finais: {s['creditos_finais_kwh']:,.0f} kWh\n")
        
#         print(f"🚗 TRANSPORTE:")
#         print(f"   📊 Benefício: {s['beneficio_transporte']:.1f}")
#         print(f"   💡 Contribuição FO: R$ {-self.gamma * s['beneficio_transporte']:,.2f}")
#         print(f"{'='*80}\n")
        
#         # Detalhes por estação
#         for l in s['estacoes_instaladas']:
#             k = s['carports_instalados'].get(l)
#             print(f"📍 Link {l} ({self.df_links[self.df_links.link_id==l]['nome'].values[0]}):")
#             print(f"   - Estação: R$ {self.c_CS[l]:,.0f}")
#             if k is not None:
#                 print(f"   - Carport PV Tipo {k}: {self.P_k[k]} kW (R$ {self.c_PV[k]:,.0f})")
#             print(f"   - Benefício: {self.rho[l]*self.beta[l]:.1f}")
#         print(f"{'='*80}")


# # === FUNÇÃO PRINCIPAL ===
# def resolver_problema(pasta: str) -> FCSA_MILP:
#     """
#     Resolve problema FCSA MILP completo
    
#     Args:
#         pasta: Caminho para pasta do problema (ex: 'dados/problema0')
    
#     Returns:
#         Objeto FCSA_MILP com solução
#     """
#     modelo = FCSA_MILP(pasta)
#     modelo.resolver()
#     return modelo


# if __name__ == '__main__':
#     # Resolver problema 0
#     modelo = resolver_problema('dados/problema0')










# """
# Modelo FCSA MILP - Versão Compacta com Método Lexicográfico
# Baseado na tese de Caio dos Santos (Unicamp, 2021)
# Autor: Carlos Murgueitio
# Data: 2025-01-15

# Método Lexicográfico (2 passos):
# 1. Maximiza benefícios de transporte
# 2. Minimiza custos mantendo benefícios máximos
# """

# import pandas as pd
# import yaml
# from pathlib import Path
# from docplex.mp.model import Model
# import time
# from typing import Dict, Tuple


# class FCSA_MILP:
#     """Modelo FCSA MILP para alocação de estações de recarga rápida com PV"""
    
#     def __init__(self, pasta_problema: str):
#         """
#         Inicializa modelo carregando dados da pasta do problema
        
#         Args:
#             pasta_problema: Caminho para pasta com arquivos do problema
#                            Ex: 'dados/problema0'
#         """
#         self.pasta = Path(pasta_problema)
#         self._carregar_dados()
#         self._calcular_parametros_derivados()
#         self.modelo = None
#         self.solucao = {}
        
#     def _carregar_dados(self):
#         """Carrega todos os arquivos de dados"""
#         # Config geral
#         with open(self.pasta / 'config_geral.yaml', 'r', encoding='utf-8') as f:
#             config = yaml.safe_load(f)
        
#         self.alpha = config['parametros_financeiros']['alpha']
#         self.Delta_h = config['parametros_financeiros']['Delta_h']
#         self.h = config['parametros_financeiros']['h']
#         self.gamma = config['parametros_otimizacao']['gamma']
#         self.min_estacoes = config['parametros_otimizacao']['min_estacoes']
#         self.a = config['parametros_area']['a']
#         self.time_limit = config['solver']['time_limit']
#         self.mip_gap = config['solver']['mip_gap']
#         self.log_output = config['solver']['log_output']
        
#         # CSVs
#         links = pd.read_csv(self.pasta / 'links.csv')
#         custos_est = pd.read_csv(self.pasta / 'custos_estacoes.csv')
#         custos_pv = pd.read_csv(self.pasta / 'custos_carports_pv.csv')
#         tarifas = pd.read_csv(self.pasta / 'tarifas_energia.csv')
#         demanda = pd.read_csv(self.pasta / 'demanda_energia.csv')
#         irradiacao = pd.read_csv(self.pasta / 'irradiacao_solar.csv')
#         transporte = pd.read_csv(self.pasta / 'parametros_transporte.csv')
#         areas = pd.read_csv(self.pasta / 'areas_disponiveis.csv')
        
#         # Conjuntos
#         self.L = links['link_id'].tolist()
#         self.T = list(range(24))
#         self.K = custos_pv['tipo_pv'].tolist()
        
#         # Parâmetros em dicionários
#         self.c_CS = custos_est.set_index('link_id')['custo_instalacao_reais'].to_dict()
#         self.c_PV = custos_pv.set_index('tipo_pv')['custo_instalacao_reais'].to_dict()
#         self.P_k = custos_pv.set_index('tipo_pv')['potencia_kw'].to_dict()
#         self.a_k = custos_pv.set_index('tipo_pv')['area_m2'].to_dict()
#         self.c_e = tarifas.set_index('periodo')['tarifa_reais_kwh'].to_dict()
#         self.cp = areas.set_index('link_id')['area_disponivel_m2'].to_dict()
#         self.rho = transporte.set_index('link_id')['fluxo_agregado_veiculos_dia'].to_dict()
#         self.beta = transporte.set_index('link_id')['fator_beneficio'].to_dict()
        
#         # Parâmetros indexados (l,t)
#         self.E_d = demanda.set_index(['link_id', 'periodo'])['demanda_kwh'].to_dict()
#         self.sh = irradiacao.set_index(['link_id', 'periodo'])['irradiacao_normalizada'].to_dict()
        
#         # Guardar DataFrames para geolocalização
#         self.df_links = links
        
#     def _calcular_parametros_derivados(self):
#         """Calcula Big-M e fator de valor presente"""
#         # Big-M
#         max_pv = max(self.P_k[k] * self.sh.get((l, t), 0) 
#                      for l in self.L for t in self.T for k in self.K)
#         max_dem = max(self.E_d.values())
#         self.BIG_M = max(max_pv, max_dem) * 1.5
        
#         # Fator valor presente
#         num = (1 + self.alpha)**self.Delta_h - 1
#         den = self.alpha * (1 + self.alpha)**self.h * (1 + self.alpha)**self.Delta_h
#         self.fator_vp = num / den
        
#     def construir(self):
#         """Constrói modelo MILP com todas as restrições técnicas"""
#         print(f"\n{'='*80}\n🔧 CONSTRUINDO MODELO FCSA MILP (MÉTODO LEXICOGRÁFICO)\n{'='*80}")
#         print(f"📊 L={len(self.L)} | T={len(self.T)} | K={len(self.K)} | "
#               f"γ={self.gamma} | α={self.alpha*100:.0f}%")
        
#         m = Model('FCSA_MILP_Lexicografico')
        
#         # === VARIÁVEIS ===
#         x = m.binary_var_dict(self.L, name='x')  # Instalar estação
#         w = {(l,k): m.binary_var(name=f'w_{l}_{k}') for l in self.L for k in self.K}
#         E = m.continuous_var_dict([(l,t) for l in self.L for t in self.T], lb=0, name='E')
#         E_pv = m.continuous_var_dict([(l,t) for l in self.L for t in self.T], lb=0, name='E_pv')
#         E_minus_nm = m.continuous_var_dict([(l,t) for l in self.L for t in self.T], lb=0, name='E_minus_nm')
#         E_plus_nm = m.continuous_var_dict([(l,t) for l in self.L for t in self.T], lb=0, name='E_plus_nm')
#         E_lot = m.continuous_var_dict([(l,t) for l in self.L for t in self.T], lb=0, name='E_lot')
#         E_nm = m.continuous_var_dict(self.T, lb=0, name='E_nm')
#         E_d_eff = m.continuous_var_dict([(l,t) for l in self.L for t in self.T], lb=0, name='E_d_eff')
#         x_aux = m.binary_var_dict([(l,t) for l in self.L for t in self.T], name='x_aux')
        
#         print(f"✅ Variáveis: {m.number_of_variables}")
        
#         # === COMPONENTES DA FUNÇÃO OBJETIVO (guardados para uso posterior) ===
#         self._C_in = m.sum(self.c_CS[l]*x[l] for l in self.L) + \
#                      m.sum(self.c_PV[k]*w[l,k] for l in self.L for k in self.K)
        
#         self._C_op = self.fator_vp * m.sum(self.c_e[t]*E[l,t] for l in self.L for t in self.T)
        
#         self._f_trans = m.sum(x[l]*self.rho[l]*self.beta[l] for l in self.L)
        
#         # === RESTRIÇÕES TÉCNICAS (0-11) ===
        
#         # (0) Cobertura mínima (se especificada)
#         if self.min_estacoes > 0:
#             m.add_constraint(m.sum(x[l] for l in self.L) >= self.min_estacoes,
#                            ctname='cobertura_minima')
        
#         # (1) Linearização demanda efetiva: E_d_eff = x_l * E_d
#         E_d_max = max(self.E_d.values())
#         for l in self.L:
#             for t in self.T:
#                 Ed = self.E_d.get((l,t), 0)
#                 m.add_constraint(E_d_eff[l,t] <= E_d_max * x[l])
#                 m.add_constraint(E_d_eff[l,t] <= Ed)
#                 m.add_constraint(E_d_eff[l,t] >= Ed - E_d_max*(1-x[l]))
        
#         # (4) Balanço energético: E_pv + E_minus_nm + E = E_d_eff + E_plus_nm
#         for l in self.L:
#             for t in self.T:
#                 m.add_constraint(E_pv[l,t] + E_minus_nm[l,t] + E[l,t] == 
#                                 E_d_eff[l,t] + E_plus_nm[l,t],
#                                 ctname=f'balanco_energia_{l}_{t}')
        
#         # (5) Geração PV
#         for l in self.L:
#             for t in self.T:
#                 m.add_constraint(E_pv[l,t] == m.sum(self.P_k[k]*self.sh.get((l,t),0)*w[l,k] 
#                                                      for k in self.K),
#                                 ctname=f'geracao_pv_{l}_{t}')
        
#         # (6) Limite importação net-metering
#         for l in self.L:
#             for idx, t in enumerate(self.T):
#                 if idx > 0:
#                     m.add_constraint(E_minus_nm[l,t] <= E_nm[self.T[idx-1]],
#                                    ctname=f'limite_importacao_{l}_{t}')
#                 else:
#                     m.add_constraint(E_minus_nm[l,t] == 0,
#                                    ctname=f'sem_creditos_iniciais_{l}_{t}')
        
#         # (7) Balanço acumulativo créditos
#         for idx, t in enumerate(self.T):
#             if idx == 0:
#                 m.add_constraint(E_nm[t] == m.sum(E_plus_nm[l,t] - E_minus_nm[l,t] for l in self.L),
#                                ctname=f'balanco_nm_inicial_{t}')
#             else:
#                 m.add_constraint(E_nm[t] == E_nm[self.T[idx-1]] + 
#                                 m.sum(E_plus_nm[l,t] - E_minus_nm[l,t] for l in self.L),
#                                 ctname=f'balanco_nm_acumulativo_{t}')
        
#         # (8) Linearização E_lot = max{0, E_pv - E_d_eff}
#         for l in self.L:
#             for t in self.T:
#                 m.add_constraint(E_lot[l,t] >= E_pv[l,t] - E_d_eff[l,t],
#                                ctname=f'lin_L2_{l}_{t}')
#                 m.add_constraint(E_lot[l,t] <= self.BIG_M * x_aux[l,t],
#                                ctname=f'lin_L3_{l}_{t}')
#                 m.add_constraint(E_lot[l,t] <= E_pv[l,t] - E_d_eff[l,t] + self.BIG_M*(1-x_aux[l,t]),
#                                ctname=f'lin_L4_{l}_{t}')
        
#         # (9) Limite exportação
#         for l in self.L:
#             for t in self.T:
#                 m.add_constraint(E_plus_nm[l,t] <= E_lot[l,t],
#                                ctname=f'limite_exportacao_{l}_{t}')
        
#         # (10) Área carport
#         for l in self.L:
#             m.add_constraint(m.sum(self.a_k[k]*w[l,k] for k in self.K) <= self.cp[l]*self.a,
#                            ctname=f'area_carport_{l}')
        
#         # (11) Carport requer estação
#         for l in self.L:
#             m.add_constraint(m.sum(w[l,k] for k in self.K) <= x[l],
#                            ctname=f'carport_requer_estacao_{l}')
        
#         print(f"✅ Restrições técnicas (0-11): {m.number_of_constraints}")
        
#         self.modelo = m
#         self._vars = {'x': x, 'w': w, 'E': E, 'E_pv': E_pv, 'E_minus_nm': E_minus_nm,
#                       'E_plus_nm': E_plus_nm, 'E_nm': E_nm}
        
#         print(f"{'='*80}")
        
#     def resolver(self):
#         """Resolve modelo usando método lexicográfico de 2 passos"""
#         if not self.modelo:
#             self.construir()
        
#         # Configurar solver
#         self.modelo.parameters.mip.tolerances.mipgap = self.mip_gap
#         self.modelo.parameters.timelimit = self.time_limit
#         self.modelo.parameters.threads = 0
        
#         tempo_total = 0
        
#         # ========== PASSO 1: MAXIMIZAR BENEFÍCIOS DE TRANSPORTE ==========
#         print(f"\n{'='*80}\n📊 PASSO 1: MAXIMIZANDO BENEFÍCIOS DE TRANSPORTE\n{'='*80}")
#         print(f"⏱️  Limite: {self.time_limit}s | Gap: {self.mip_gap*100}%")
        
#         # Função objetivo Passo 1: max f_transporte
#         self.modelo.maximize(self._f_trans)
        
#         t0 = time.time()
#         sol1 = self.modelo.solve(log_output=self.log_output)
#         tempo1 = time.time() - t0
#         tempo_total += tempo1
        
#         if not sol1:
#             print(f"\n{'='*80}\n❌ PASSO 1 INFACTÍVEL\n{'='*80}")
#             return False
        
#         # Guardar benefício máximo
#         f_trans_otimo = sol1.objective_value
#         print(f"\n{'='*80}\n✅ PASSO 1 CONCLUÍDO\n{'='*80}")
#         print(f"⏱️  Tempo: {tempo1:.2f}s")
#         print(f"📊 Benefício máximo: {f_trans_otimo:.2f}")
#         print(f"⚡ Estações instaladas: {sum(1 for l in self.L if self._vars['x'][l].solution_value > 0.5)}")
#         print(f"{'='*80}")
        
#         # ========== PASSO 2: MINIMIZAR CUSTOS (COM RESTRIÇÃO LEXICOGRÁFICA) ==========
#         print(f"\n{'='*80}\n💰 PASSO 2: MINIMIZANDO CUSTOS\n{'='*80}")
#         print(f"📌 Restrição lexicográfica: f_transporte >= {f_trans_otimo:.2f}")
        
#         # Adicionar restrição lexicográfica
#         self.modelo.add_constraint(self._f_trans >= f_trans_otimo,
#                                   ctname='restricao_lexicografica')
        
#         print(f"✅ Restrição lexicográfica adicionada")
#         print(f"⏱️  Limite: {self.time_limit}s | Gap: {self.mip_gap*100}%")
        
#         # Função objetivo Passo 2: min (C_in + C_op)
#         self.modelo.minimize(self._C_in + self._C_op)
        
#         t0 = time.time()
#         sol2 = self.modelo.solve(log_output=self.log_output)
#         tempo2 = time.time() - t0
#         tempo_total += tempo2
        
#         if not sol2:
#             print(f"\n{'='*80}\n❌ PASSO 2 INFACTÍVEL\n{'='*80}")
#             return False
        
#         print(f"\n{'='*80}\n✅ PASSO 2 CONCLUÍDO\n{'='*80}")
#         print(f"⏱️  Tempo Passo 2: {tempo2:.2f}s")
#         print(f"⏱️  Tempo Total: {tempo_total:.2f}s")
#         print(f"{'='*80}")
        
#         # Extrair e imprimir solução final
#         self._extrair_solucao(tempo_total, f_trans_otimo)
#         self._imprimir_resultados()
        
#         return True
    
#     def _extrair_solucao(self, tempo: float, f_trans_otimo: float):
#         """Extrai solução do Passo 2"""
#         x = self._vars['x']
#         w = self._vars['w']
#         E = self._vars['E']
#         E_pv = self._vars['E_pv']
#         E_nm = self._vars['E_nm']
#         E_plus_nm = self._vars['E_plus_nm']
#         E_minus_nm = self._vars['E_minus_nm']
        
#         est = [l for l in self.L if x[l].solution_value > 0.5]
#         cp_inst = {l: k for l in est for k in self.K if w[l,k].solution_value > 0.5}
        
#         # Calcular custos
#         custo_inv = sum(self.c_CS[l] for l in est) + sum(self.c_PV[k] for k in cp_inst.values())
#         custo_op = self.fator_vp * sum(self.c_e[t]*E[l,t].solution_value for l in est for t in self.T)
        
#         self.solucao = {
#             'tempo_s': tempo,
#             'gap_%': self.modelo.solve_details.mip_relative_gap * 100,
#             'valor_objetivo': self.modelo.objective_value,
#             'estacoes_instaladas': est,
#             'num_estacoes': len(est),
#             'carports_instalados': cp_inst,
#             'custo_investimento': custo_inv,
#             'custo_operacao_vp': custo_op,
#             'custo_total': custo_inv + custo_op,
#             'beneficio_transporte': f_trans_otimo,  # Benefício máximo do Passo 1
#             'energia_comprada_kwh': sum(E[l,t].solution_value for l in est for t in self.T),
#             'energia_pv_kwh': sum(E_pv[l,t].solution_value for l in est for t in self.T),
#             'energia_exportada_kwh': sum(E_plus_nm[l,t].solution_value for l in est for t in self.T),
#             'energia_importada_kwh': sum(E_minus_nm[l,t].solution_value for l in est for t in self.T),
#             'creditos_finais_kwh': E_nm[self.T[-1]].solution_value
#         }
        
#     def _imprimir_resultados(self):
#         """Imprime resumo da solução lexicográfica"""
#         s = self.solucao
#         print(f"\n{'='*80}\n📊 SOLUÇÃO FINAL (MÉTODO LEXICOGRÁFICO)\n{'='*80}")
#         print(f"⏱️  Tempo total: {s['tempo_s']:.2f}s | Gap: {s['gap_%']:.2f}%")
#         print(f"💰 Custo total mínimo: R$ {s['custo_total']:,.2f}")
#         print(f"📊 Benefício máximo garantido: {s['beneficio_transporte']:.2f}\n")
        
#         print(f"🏗️  INVESTIMENTO:")
#         print(f"   ⚡ Estações: {s['num_estacoes']} → {s['estacoes_instaladas']}")
#         print(f"   ☀️  Carports PV: {len(s['carports_instalados'])}")
#         print(f"   💰 Custo: R$ {s['custo_investimento']:,.2f}\n")
        
#         print(f"💡 OPERAÇÃO ({self.Delta_h} anos):")
#         print(f"   💰 Custo VP: R$ {s['custo_operacao_vp']:,.2f}")
#         print(f"   🔌 Comprada: {s['energia_comprada_kwh']:,.0f} kWh")
#         print(f"   ☀️  Gerada PV: {s['energia_pv_kwh']:,.0f} kWh\n")
        
#         print(f"🔋 NET-METERING:")
#         print(f"   📤 Exportada: {s['energia_exportada_kwh']:,.0f} kWh")
#         print(f"   📥 Importada: {s['energia_importada_kwh']:,.0f} kWh")
#         print(f"   💾 Créditos finais: {s['creditos_finais_kwh']:,.0f} kWh\n")
        
#         print(f"🚗 TRANSPORTE (PRIORIDADE LEXICOGRÁFICA):")
#         print(f"   📊 Benefício máximo: {s['beneficio_transporte']:.2f}")
#         print(f"   🎯 Garantido pela restrição lexicográfica")
#         print(f"{'='*80}\n")
        
#         # Detalhes por estação
#         for l in s['estacoes_instaladas']:
#             k = s['carports_instalados'].get(l)
#             print(f"📍 Link {l} ({self.df_links[self.df_links.link_id==l]['nome'].values[0]}):")
#             print(f"   - Estação: R$ {self.c_CS[l]:,.0f}")
#             if k is not None:
#                 print(f"   - Carport PV Tipo {k}: {self.P_k[k]} kW (R$ {self.c_PV[k]:,.0f})")
#             print(f"   - Benefício: {self.rho[l]*self.beta[l]:.1f}")
#         print(f"{'='*80}")


# # === FUNÇÃO PRINCIPAL ===
# def resolver_problema(pasta: str) -> FCSA_MILP:
#     """
#     Resolve problema FCSA MILP usando método lexicográfico
    
#     Args:
#         pasta: Caminho para pasta do problema (ex: 'dados/problema0')
    
#     Returns:
#         Objeto FCSA_MILP com solução lexicográfica
#     """
#     modelo = FCSA_MILP(pasta)
#     modelo.resolver()
#     return modelo


# if __name__ == '__main__':
#     # Resolver problema 0 com método lexicográfico
#     modelo = resolver_problema('dados/problema0')





# """
# Modelo FCSA MILP - Versão Completa com Cobertura Espacial e Demanda Agregada
# Baseado na tese de Caio dos Santos (Unicamp, 2021)
# Autor: Carlos Murgueitio
# Data: 2025-01-16

# NOVAS IMPLEMENTAÇÕES:
# - Restrição (10): Cobertura espacial por subconjuntos L_i
# - Demanda agregada: Estação em j atende links em I_j
# - Cálculo automático de L_i e I_j por distância geográfica
# """

# import pandas as pd
# import yaml
# import numpy as np
# from pathlib import Path
# from docplex.mp.model import Model
# import time
# from typing import Dict, List, Tuple
# from math import radians, cos, sin, asin, sqrt


# class FCSA_MILP:
#     """Modelo FCSA MILP para alocação de estações de recarga rápida com PV"""
    
#     def __init__(self, pasta_problema: str):
#         """
#         Inicializa modelo carregando dados da pasta do problema
        
#         Args:
#             pasta_problema: Caminho para pasta com arquivos do problema
#                            Ex: 'dados/problema0'
#         """
#         self.pasta = Path(pasta_problema)
#         self._carregar_dados()
#         # self._calcular_parametros_derivados()
#         self._calcular_subconjuntos_cobertura() 
#         self._calcular_demanda_agregada()  
#          self._calcular_parametros_derivados()
#          self._calcular_big_m()  # Big-M AL FINAL
#         self.modelo = None
#         self.solucao = {}

#     def _calcular_fator_vp(self):
#         """Calcula fator de valor presente"""
#         num = (1 + self.alpha)**self.Delta_h - 1
#         den = self.alpha * (1 + self.alpha)**self.h * (1 + self.alpha)**self.Delta_h
#         self.fator_vp = num / den

#     def _calcular_big_m(self):
#         """Calcula Big-M baseado em demanda agregada (APÓS cálculo)"""
#         max_pv = max(self.P_k[k] * self.sh.get((l, t), 0) 
#                     for l in self.L for t in self.T for k in self.K)
#         max_dem_agregada = max(self.E_d_agregada.values())
#         self.BIG_M = max(max_pv, max_dem_agregada) * 1.5
        
#         print(f"   ✓ Big-M: {self.BIG_M:,.0f} kWh (demanda agregada máx: {max_dem_agregada:,.0f})")


        
#     def _carregar_dados(self):
#         """Carrega todos os arquivos de dados"""
#         # Config geral
#         with open(self.pasta / 'config_geral.yaml', 'r', encoding='utf-8') as f:
#             config = yaml.safe_load(f)
        
#         self.alpha = config['parametros_financeiros']['alpha']
#         self.Delta_h = config['parametros_financeiros']['Delta_h']
#         self.h = config['parametros_financeiros']['h']
#         self.gamma = config['parametros_otimizacao']['gamma']
#         self.min_estacoes = config['parametros_otimizacao']['min_estacoes']
#         self.a = config['parametros_area']['a']
#         self.time_limit = config['solver']['time_limit']
#         self.mip_gap = config['solver']['mip_gap']
#         self.log_output = config['solver']['log_output']
        
#         # NOVO: Raio de cobertura
#         self.raio_cobertura_km = config['parametros_otimizacao'].get('raio_cobertura_km', 3.0)
        
#         # CSVs
#         links = pd.read_csv(self.pasta / 'links.csv')
#         custos_est = pd.read_csv(self.pasta / 'custos_estacoes.csv')
#         custos_pv = pd.read_csv(self.pasta / 'custos_carports_pv.csv')
#         tarifas = pd.read_csv(self.pasta / 'tarifas_energia.csv')
#         demanda = pd.read_csv(self.pasta / 'demanda_energia.csv')
#         irradiacao = pd.read_csv(self.pasta / 'irradiacao_solar.csv')
#         transporte = pd.read_csv(self.pasta / 'parametros_transporte.csv')
#         areas = pd.read_csv(self.pasta / 'areas_disponiveis.csv')
        
#         # Conjuntos
#         self.L = links['link_id'].tolist()
#         self.T = list(range(24))
#         self.K = custos_pv['tipo_pv'].tolist()
        
#         # Parâmetros em dicionários
#         self.c_CS = custos_est.set_index('link_id')['custo_instalacao_reais'].to_dict()
#         self.c_PV = custos_pv.set_index('tipo_pv')['custo_instalacao_reais'].to_dict()
#         self.P_k = custos_pv.set_index('tipo_pv')['potencia_kw'].to_dict()
#         self.a_k = custos_pv.set_index('tipo_pv')['area_m2'].to_dict()
#         self.c_e = tarifas.set_index('periodo')['tarifa_reais_kwh'].to_dict()
#         self.cp = areas.set_index('link_id')['area_disponivel_m2'].to_dict()
#         self.rho = transporte.set_index('link_id')['fluxo_agregado_veiculos_dia'].to_dict()
#         self.beta = transporte.set_index('link_id')['fator_beneficio'].to_dict()
        
#         # Parâmetros indexados (l,t)
#         self.E_d = demanda.set_index(['link_id', 'periodo'])['demanda_kwh'].to_dict()
#         self.sh = irradiacao.set_index(['link_id', 'periodo'])['irradiacao_normalizada'].to_dict()
        
#         # Guardar DataFrames com coordenadas geográficas
#         self.df_links = links
#         self.coordenadas = links.set_index('link_id')[['latitude', 'longitude']].to_dict('index')
        
#     def _haversine(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
#         """
#         Calcula distância entre dois pontos geográficos (fórmula de Haversine)
        
#         Returns:
#             Distância em quilômetros
#         """
#         # Converter para radianos
#         lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
#         # Fórmula de Haversine
#         dlat = lat2 - lat1
#         dlon = lon2 - lon1
#         a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
#         c = 2 * asin(sqrt(a))
        
#         # Raio da Terra em km
#         r = 6371
        
#         return c * r
    
#     # def _calcular_subconjuntos_cobertura(self):
#     #     """
#     #     Calcula subconjuntos L_i e I_j baseados em distância geográfica
        
#     #     L_i: Links que podem COBRIR o link i (para restrição 10)
#     #     I_j: Links que o link j PODE COBRIR (para demanda agregada)
#     #     """
#     #     print(f"\n🗺️  Calculando subconjuntos de cobertura (raio: {self.raio_cobertura_km} km)...")
        
#     #     self.L_i = {i: [] for i in self.L}  # Links que cobrem i
#     #     self.I_j = {j: [] for j in self.L}  # Links cobertos por j
        
#     #     # Calcular distâncias e preencher subconjuntos
#     #     for i in self.L:
#     #         lat_i = self.coordenadas[i]['latitude']
#     #         lon_i = self.coordenadas[i]['longitude']
            
#     #         for j in self.L:
#     #             lat_j = self.coordenadas[j]['latitude']
#     #             lon_j = self.coordenadas[j]['longitude']
                
#     #             dist_km = self._haversine(lat_i, lon_i, lat_j, lon_j)
                
#     #             # Se j está dentro do raio de i
#     #             if dist_km <= self.raio_cobertura_km:
#     #                 self.L_i[i].append(j)  # j pode cobrir i
#     #                 self.I_j[j].append(i)  # j pode atender i
        
#     #     # Verificar que todos os links têm ao menos um cobertor
#     #     links_sem_cobertura = [i for i in self.L if len(self.L_i[i]) == 0]
#     #     if links_sem_cobertura:
#     #         print(f"⚠️  AVISO: Links sem cobertura: {links_sem_cobertura}")
#     #         print(f"   Solução: Aumentar raio_cobertura_km em config_geral.yaml")
#     #         # Auto-cobertura como fallback
#     #         for i in links_sem_cobertura:
#     #             self.L_i[i] = [i]
#     #             self.I_j[i].append(i)
        
#     #     # Estatísticas
#     #     avg_cobertores = np.mean([len(self.L_i[i]) for i in self.L])
#     #     avg_cobertos = np.mean([len(self.I_j[j]) for j in self.L])
        
#     #     print(f"   ✓ Média de cobertores por link: {avg_cobertores:.1f}")
#     #     print(f"   ✓ Média de links cobertos por estação: {avg_cobertos:.1f}")
        
#     #     # Salvar para visualização posterior
#     #     self._salvar_matriz_cobertura()



#     def _calcular_subconjuntos_cobertura(self):
#         """
#         Calcula subconjuntos L_i e I_j baseados em distância geográfica
        
#         L_i: Links que podem COBRIR o link i (para restrição 10)
#         I_j: Links que o link j PODE COBRIR (para demanda agregada)
#         """
#         print(f"\n🗺️  Calculando subconjuntos de cobertura (raio: {self.raio_cobertura_km} km)...")
        
#         self.L_i = {i: [] for i in self.L}  # Links que cobrem i
#         self.I_j = {j: [] for j in self.L}  # Links cobertos por j
        
#         # PRIMEIRO: Garantir auto-cobertura (cada link cobre a si mesmo)
#         for i in self.L:
#             self.L_i[i].append(i)
#             self.I_j[i].append(i)
        
#         # SEGUNDO: Adicionar links vizinhos dentro do raio
#         for i in self.L:
#             lat_i = self.coordenadas[i]['latitude']
#             lon_i = self.coordenadas[i]['longitude']
            
#             for j in self.L:
#                 if i == j:  # Já adicionado acima
#                     continue
                    
#                 lat_j = self.coordenadas[j]['latitude']
#                 lon_j = self.coordenadas[j]['longitude']
                
#                 dist_km = self._haversine(lat_i, lon_i, lat_j, lon_j)
                
#                 # Se j está dentro do raio de i
#                 if dist_km <= self.raio_cobertura_km:
#                     self.L_i[i].append(j)  # j pode cobrir i
#                     self.I_j[j].append(i)  # j pode atender i
        
#         # Estatísticas
#         avg_cobertores = np.mean([len(self.L_i[i]) for i in self.L])
#         avg_cobertos = np.mean([len(self.I_j[j]) for j in self.L])
        
#         print(f"   ✓ Média de cobertores por link: {avg_cobertores:.1f}")
#         print(f"   ✓ Média de links cobertos por estação: {avg_cobertos:.1f}")
        
#         # Verificação de segurança
#         links_sem_cobertura = [i for i in self.L if len(self.L_i[i]) == 0]
#         if links_sem_cobertura:
#             print(f"   ⚠️  ERRO: Links sem cobertura após auto-inclusão: {links_sem_cobertura}")
#             raise ValueError("Erro crítico: links sem cobertura mesmo com auto-inclusão")
        
#         # Salvar para visualização posterior
#         self._salvar_matriz_cobertura()











        
#     def _salvar_matriz_cobertura(self):
#         """Salva matriz de cobertura para análise"""
#         dados_cobertura = []
#         for i in self.L:
#             for j in self.L_i[i]:
#                 lat_i = self.coordenadas[i]['latitude']
#                 lon_i = self.coordenadas[i]['longitude']
#                 lat_j = self.coordenadas[j]['latitude']
#                 lon_j = self.coordenadas[j]['longitude']
#                 dist = self._haversine(lat_i, lon_i, lat_j, lon_j)
                
#                 dados_cobertura.append({
#                     'link_destino': i,
#                     'link_cobertor': j,
#                     'distancia_km': round(dist, 2)
#                 })
        
#         df_cob = pd.DataFrame(dados_cobertura)
#         df_cob.to_csv(self.pasta / 'matriz_cobertura_calculada.csv', index=False)
#         print(f"   ✓ Matriz salva: {self.pasta / 'matriz_cobertura_calculada.csv'}")
    
#     def _calcular_demanda_agregada(self):
#         """
#         Calcula demanda agregada para cada link:
#         E_d_agregada[j,t] = Σ_{i ∈ I_j} E_d[i,t]
#         """
#         print(f"\n📊 Calculando demanda agregada...")
        
#         self.E_d_agregada = {}
        
#         for j in self.L:
#             for t in self.T:
#                 # Somar demandas de todos os links que j pode atender
#                 demanda_total = sum(self.E_d.get((i, t), 0) for i in self.I_j[j])
#                 self.E_d_agregada[(j, t)] = demanda_total
        
#         # Estatísticas
#         demanda_original_total = sum(self.E_d.values())
#         demanda_agregada_max = max(self.E_d_agregada.values())
        
#         print(f"   ✓ Demanda original total/dia: {demanda_original_total:,.0f} kWh")
#         print(f"   ✓ Demanda agregada máxima (link+vizinhos): {demanda_agregada_max:,.0f} kWh")
        
#     # def _calcular_parametros_derivados(self):
#     #     """Calcula Big-M e fator de valor presente"""
#     #     # Big-M
#     #     max_pv = max(self.P_k[k] * self.sh.get((l, t), 0) 
#     #                  for l in self.L for t in self.T for k in self.K)
#     #     max_dem = max(self.E_d.values())
#     #     self.BIG_M = max(max_pv, max_dem) * 1.5
        
#     #     # Fator valor presente
#     #     num = (1 + self.alpha)**self.Delta_h - 1
#     #     den = self.alpha * (1 + self.alpha)**self.h * (1 + self.alpha)**self.Delta_h
#     #     self.fator_vp = num / den


#     def _calcular_parametros_derivados(self):
#         """Calcula Big-M e fator de valor presente"""
#         # Big-M baseado em demanda AGREGADA
#         max_pv = max(self.P_k[k] * self.sh.get((l, t), 0) 
#                     for l in self.L for t in self.T for k in self.K)
        
#         # ✅ USAR DEMANDA AGREGADA (já calculada)
#         max_dem = max(self.E_d_agregada.values())
        
#         self.BIG_M = max(max_pv, max_dem) * 1.5
        
#         # Fator valor presente
#         num = (1 + self.alpha)**self.Delta_h - 1
#         den = self.alpha * (1 + self.alpha)**self.h * (1 + self.alpha)**self.Delta_h
#         self.fator_vp = num / den




        
#     def construir(self):
#         """Constrói modelo MILP com TODAS as restrições (incluindo 10 e demanda agregada)"""
#         print(f"\n{'='*80}\n🔧 CONSTRUINDO MODELO FCSA MILP COMPLETO\n{'='*80}")
#         print(f"📊 L={len(self.L)} | T={len(self.T)} | K={len(self.K)} | "
#               f"γ={self.gamma} | α={self.alpha*100:.0f}% | r={self.raio_cobertura_km}km")
        
#         m = Model('FCSA_MILP_Completo')
        
#         # === VARIÁVEIS ===
#         x = m.binary_var_dict(self.L, name='x')
#         w = {(l,k): m.binary_var(name=f'w_{l}_{k}') for l in self.L for k in self.K}
#         E = m.continuous_var_dict([(l,t) for l in self.L for t in self.T], lb=0, name='E')
#         E_pv = m.continuous_var_dict([(l,t) for l in self.L for t in self.T], lb=0, name='E_pv')
#         E_minus_nm = m.continuous_var_dict([(l,t) for l in self.L for t in self.T], lb=0, name='E_minus_nm')
#         E_plus_nm = m.continuous_var_dict([(l,t) for l in self.L for t in self.T], lb=0, name='E_plus_nm')
#         E_lot = m.continuous_var_dict([(l,t) for l in self.L for t in self.T], lb=0, name='E_lot')
#         E_nm = m.continuous_var_dict(self.T, lb=0, name='E_nm')
#         E_d_eff = m.continuous_var_dict([(l,t) for l in self.L for t in self.T], lb=0, name='E_d_eff')
#         x_aux = m.binary_var_dict([(l,t) for l in self.L for t in self.T], name='x_aux')
        
#         print(f"✅ Variáveis: {m.number_of_variables}")
        
#         # === COMPONENTES DA FUNÇÃO OBJETIVO ===
#         self._C_in = m.sum(self.c_CS[l]*x[l] for l in self.L) + \
#                      m.sum(self.c_PV[k]*w[l,k] for l in self.L for k in self.K)
        
#         self._C_op = self.fator_vp * m.sum(self.c_e[t]*E[l,t] for l in self.L for t in self.T)
        
#         self._f_trans = m.sum(x[l]*self.rho[l]*self.beta[l] for l in self.L)





#         # === DEBUG: VERIFICAR TIPOS ===
#         print(f"\n🔍 DEBUG:")
#         print(f"   Tipo self.L[0]: {type(self.L[0])}")
#         print(f"   self.L: {self.L}")
#         print(f"   self.L_i[0]: {self.L_i[0]}")
#         print(f"   Tipo self.L_i[0][0]: {type(self.L_i[0][0])}")
#         print(f"   x.keys(): {list(x.keys())}")
#         print(f"   0 in x: {0 in x}")
#         print(f"   self.L_i[0][0] in x: {self.L_i[0][0] in x}")







        
#         # === RESTRIÇÕES ===
#         num_restricoes = 0
        
#         # ✅ (10) COBERTURA ESPACIAL - NOVA RESTRIÇÃO
#         for i in self.L:
#             m.add_constraint(
#                 m.sum(x[j] for j in self.L_i[i]) >= 1,
#                 ctname=f'cobertura_espacial_{i}'
#             )
#             num_restricoes += 1
#         print(f"✅ (10) Cobertura espacial: {num_restricoes} restrições")
        
#         # (1) Linearização demanda efetiva COM DEMANDA AGREGADA
#         E_d_max = max(self.E_d_agregada.values())  # MUDANÇA: usar demanda agregada
#         for l in self.L:
#             for t in self.T:
#                 Ed_agr = self.E_d_agregada.get((l,t), 0)  # MUDANÇA
#                 m.add_constraint(E_d_eff[l,t] <= E_d_max * x[l])
#                 m.add_constraint(E_d_eff[l,t] <= Ed_agr)
#                 m.add_constraint(E_d_eff[l,t] >= Ed_agr - E_d_max*(1-x[l]))
#                 num_restricoes += 3
#         print(f"✅ (1) Demanda efetiva agregada: {3*len(self.L)*len(self.T)} restrições")
        
#         # (4) Balanço energético
#         for l in self.L:
#             for t in self.T:
#                 m.add_constraint(
#                     E_pv[l,t] + E_minus_nm[l,t] + E[l,t] == E_d_eff[l,t] + E_plus_nm[l,t],
#                     ctname=f'balanco_energia_{l}_{t}'
#                 )
#                 num_restricoes += 1
#         print(f"✅ (4) Balanço energético: {len(self.L)*len(self.T)} restrições")
        
#         # (5) Geração PV
#         for l in self.L:
#             for t in self.T:
#                 m.add_constraint(
#                     E_pv[l,t] == m.sum(self.P_k[k]*self.sh.get((l,t),0)*w[l,k] for k in self.K),
#                     ctname=f'geracao_pv_{l}_{t}'
#                 )
#                 num_restricoes += 1
#         print(f"✅ (5) Geração PV: {len(self.L)*len(self.T)} restrições")
        
#         # (6) Limite importação net-metering
#         for l in self.L:
#             for idx, t in enumerate(self.T):
#                 if idx > 0:
#                     m.add_constraint(E_minus_nm[l,t] <= E_nm[self.T[idx-1]])
#                 else:
#                     m.add_constraint(E_minus_nm[l,t] == 0)
#                 num_restricoes += 1
#         print(f"✅ (6) Limite importação: {len(self.L)*len(self.T)} restrições")
        
#         # (7) Balanço acumulativo créditos
#         for idx, t in enumerate(self.T):
#             if idx == 0:
#                 m.add_constraint(E_nm[t] == m.sum(E_plus_nm[l,t] - E_minus_nm[l,t] for l in self.L))
#             else:
#                 m.add_constraint(E_nm[t] == E_nm[self.T[idx-1]] + 
#                                 m.sum(E_plus_nm[l,t] - E_minus_nm[l,t] for l in self.L))
#             num_restricoes += 1
#         print(f"✅ (7) Balanço créditos: {len(self.T)} restrições")
        
#         # (8) Linearização E_lot
#         for l in self.L:
#             for t in self.T:
#                 m.add_constraint(E_lot[l,t] >= E_pv[l,t] - E_d_eff[l,t])
#                 m.add_constraint(E_lot[l,t] <= self.BIG_M * x_aux[l,t])
#                 m.add_constraint(E_lot[l,t] <= E_pv[l,t] - E_d_eff[l,t] + self.BIG_M*(1-x_aux[l,t]))
#                 num_restricoes += 3
#         print(f"✅ (8) Linearização: {3*len(self.L)*len(self.T)} restrições")
        
#         # (9) Limite exportação
#         for l in self.L:
#             for t in self.T:
#                 m.add_constraint(E_plus_nm[l,t] <= E_lot[l,t])
#                 num_restricoes += 1
#         print(f"✅ (9) Limite exportação: {len(self.L)*len(self.T)} restrições")
        
#         # (11) Área carport
#         for l in self.L:
#             m.add_constraint(m.sum(self.a_k[k]*w[l,k] for k in self.K) <= self.cp[l]*self.a)
#             num_restricoes += 1
#         print(f"✅ (11) Área carport: {len(self.L)} restrições")
        
#         # (12) Carport requer estação
#         for l in self.L:
#             m.add_constraint(m.sum(w[l,k] for k in self.K) <= x[l])
#             num_restricoes += 1
#         print(f"✅ (12) Carport requer estação: {len(self.L)} restrições")
        
#         print(f"\n✅ TOTAL: {num_restricoes} restrições")
#         print(f"{'='*80}")
        
#         self.modelo = m
#         self._vars = {'x': x, 'w': w, 'E': E, 'E_pv': E_pv, 'E_minus_nm': E_minus_nm,
#                       'E_plus_nm': E_plus_nm, 'E_nm': E_nm, 'E_d_eff': E_d_eff}
        
#     def resolver(self):
#         """Resolve modelo usando método lexicográfico"""
#         if not self.modelo:
#             self.construir()
        
#         self.modelo.parameters.mip.tolerances.mipgap = self.mip_gap
#         self.modelo.parameters.timelimit = self.time_limit
#         self.modelo.parameters.threads = 0
        
#         tempo_total = 0
        
#         # PASSO 1: Maximizar benefícios
#         print(f"\n{'='*80}\n📊 PASSO 1: MAXIMIZANDO BENEFÍCIOS\n{'='*80}")
#         self.modelo.maximize(self._f_trans)
        
#         t0 = time.time()
#         sol1 = self.modelo.solve(log_output=self.log_output)
#         tempo1 = time.time() - t0
#         tempo_total += tempo1
        
#         if not sol1:
#             print(f"\n❌ PASSO 1 INFACTÍVEL")
#             return False
        
#         f_trans_otimo = sol1.objective_value
#         print(f"\n✅ PASSO 1: Benefício = {f_trans_otimo:.2f} | Tempo = {tempo1:.2f}s")
        
#         # PASSO 2: Minimizar custos
#         print(f"\n{'='*80}\n💰 PASSO 2: MINIMIZANDO CUSTOS\n{'='*80}")
#         self.modelo.add_constraint(self._f_trans >= f_trans_otimo, ctname='lexicografica')
#         self.modelo.minimize(self._C_in + self._C_op)
        
#         t0 = time.time()
#         sol2 = self.modelo.solve(log_output=self.log_output)
#         tempo2 = time.time() - t0
#         tempo_total += tempo2
        
#         if not sol2:
#             print(f"\n❌ PASSO 2 INFACTÍVEL")
#             return False
        
#         print(f"\n✅ PASSO 2: Custo = R$ {sol2.objective_value:,.2f} | Tempo = {tempo2:.2f}s")
        
#         self._extrair_solucao(tempo_total, f_trans_otimo)
#         self._imprimir_resultados()
        
#         return True
    
#     def _extrair_solucao(self, tempo: float, f_trans_otimo: float):
#         """Extrai solução"""
#         x = self._vars['x']
#         w = self._vars['w']
#         E = self._vars['E']
#         E_pv = self._vars['E_pv']
#         E_nm = self._vars['E_nm']
#         E_plus_nm = self._vars['E_plus_nm']
#         E_minus_nm = self._vars['E_minus_nm']
        
#         est = [l for l in self.L if x[l].solution_value > 0.5]
#         cp_inst = {l: k for l in est for k in self.K if w[l,k].solution_value > 0.5}
        
#         custo_inv = sum(self.c_CS[l] for l in est) + sum(self.c_PV[k] for k in cp_inst.values())
#         custo_op = self.fator_vp * sum(self.c_e[t]*E[l,t].solution_value for l in est for t in self.T)
        
#         # NOVO: Calcular links cobertos
#         links_cobertos = set()
#         for i in self.L:
#             for j in est:
#                 if j in self.L_i[i]:
#                     links_cobertos.add(i)
#                     break
        
#         self.solucao = {
#             'tempo_s': tempo,
#             'gap_%': self.modelo.solve_details.mip_relative_gap * 100,
#             'valor_objetivo': self.modelo.objective_value,
#             'estacoes_instaladas': est,
#             'num_estacoes': len(est),
#             'links_cobertos': sorted(links_cobertos),
#             'num_links_cobertos': len(links_cobertos),
#             'taxa_cobertura_%': (len(links_cobertos) / len(self.L)) * 100,
#             'carports_instalados': cp_inst,
#             'custo_investimento': custo_inv,
#             'custo_operacao_vp': custo_op,
#             'custo_total': custo_inv + custo_op,
#             'beneficio_transporte': f_trans_otimo,
#             'energia_comprada_kwh': sum(E[l,t].solution_value for l in est for t in self.T),
#             'energia_pv_kwh': sum(E_pv[l,t].solution_value for l in est for t in self.T),
#             'energia_exportada_kwh': sum(E_plus_nm[l,t].solution_value for l in est for t in self.T),
#             'energia_importada_kwh': sum(E_minus_nm[l,t].solution_value for l in est for t in self.T),
#             'creditos_finais_kwh': E_nm[self.T[-1]].solution_value
#         }
        
#     def _imprimir_resultados(self):
#         """Imprime resultados"""
#         s = self.solucao
#         print(f"\n{'='*80}\n📊 SOLUÇÃO FINAL (MODELO COMPLETO)\n{'='*80}")
#         print(f"⏱️  Tempo: {s['tempo_s']:.2f}s | Gap: {s['gap_%']:.2f}%")
#         print(f"💰 Custo: R$ {s['custo_total']:,.2f} | Benefício: {s['beneficio_transporte']:.2f}\n")
        
#         print(f"🗺️  COBERTURA ESPACIAL:")
#         print(f"   ⚡ Estações: {s['num_estacoes']} → {s['estacoes_instaladas']}")
#         print(f"   📍 Links cobertos: {s['num_links_cobertos']}/{len(self.L)} ({s['taxa_cobertura_%']:.0f}%)")
#         print(f"   🎯 Lista: {s['links_cobertos']}\n")
        
#         print(f"💰 CUSTOS:")
#         print(f"   🏗️  Investimento: R$ {s['custo_investimento']:,.2f}")
#         print(f"   ⚡ Operação VP: R$ {s['custo_operacao_vp']:,.2f}\n")
        
#         print(f"⚡ ENERGIA:")
#         print(f"   🔌 Comprada: {s['energia_comprada_kwh']:,.0f} kWh")
#         print(f"   ☀️  Gerada PV: {s['energia_pv_kwh']:,.0f} kWh")
#         print(f"   📤 Exportada: {s['energia_exportada_kwh']:,.0f} kWh")
#         print(f"   📥 Importada: {s['energia_importada_kwh']:,.0f} kWh")
#         print(f"{'='*80}")


# def resolver_problema(pasta: str) -> FCSA_MILP:
#     """Resolve problema FCSA MILP completo"""
#     modelo = FCSA_MILP(pasta)
#     modelo.resolver()
#     return modelo


# if __name__ == '__main__':
#     modelo = resolver_problema('dados/problema0')









"""
Modelo FCSA MILP - Versão Completa
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
        self._calcular_fator_vp()  # ✅ ORDEM CORRETA: VP primeiro
        self._calcular_subconjuntos_cobertura()
        self._calcular_demanda_agregada()
        self._calcular_big_m()  # ✅ Big-M por último (usa demanda agregada)
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
        
        # NOVO: Raio de cobertura
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
        
        # Conjuntos - garantir int
        self.L = [int(x) for x in links['link_id'].tolist()]
        self.T = list(range(24))
        self.K = [int(x) for x in custos_pv['tipo_pv'].tolist()]
        
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
        
        # Guardar DataFrames com coordenadas geográficas
        self.df_links = links
        self.coordenadas = links.set_index('link_id')[['latitude', 'longitude']].to_dict('index')
        
    def _haversine(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calcula distância entre dois pontos geográficos (fórmula de Haversine)
        
        Returns:
            Distância em quilômetros
        """
        # Converter para radianos
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        # Fórmula de Haversine
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        # Raio da Terra em km
        r = 6371
        
        return c * r
    
    def _calcular_subconjuntos_cobertura(self):
        """
        Calcula subconjuntos L_i e I_j baseados em distância geográfica
        
        L_i: Links que podem COBRIR o link i (para restrição 10)
        I_j: Links que o link j PODE COBRIR (para demanda agregada)
        """
        print(f"\n🗺️  Calculando subconjuntos de cobertura (raio: {self.raio_cobertura_km} km)...")
        
        self.L_i = {i: [] for i in self.L}  # Links que cobrem i
        self.I_j = {j: [] for j in self.L}  # Links cobertos por j
        
        # PRIMEIRO: Garantir auto-cobertura (cada link cobre a si mesmo)
        for i in self.L:
            self.L_i[i].append(i)
            self.I_j[i].append(i)
        
        # SEGUNDO: Adicionar links vizinhos dentro do raio
        for i in self.L:
            lat_i = self.coordenadas[i]['latitude']
            lon_i = self.coordenadas[i]['longitude']
            
            for j in self.L:
                if i == j:  # Já adicionado acima
                    continue
                    
                lat_j = self.coordenadas[j]['latitude']
                lon_j = self.coordenadas[j]['longitude']
                
                dist_km = self._haversine(lat_i, lon_i, lat_j, lon_j)
                
                # Se j está dentro do raio de i
                if dist_km <= self.raio_cobertura_km:
                    self.L_i[i].append(j)  # j pode cobrir i
                    self.I_j[j].append(i)  # j pode atender i
        
        # Estatísticas
        avg_cobertores = np.mean([len(self.L_i[i]) for i in self.L])
        avg_cobertos = np.mean([len(self.I_j[j]) for j in self.L])
        
        print(f"   ✓ Média de cobertores por link: {avg_cobertores:.1f}")
        print(f"   ✓ Média de links cobertos por estação: {avg_cobertos:.1f}")
        
        # Salvar para visualização posterior
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
    
    def _calcular_demanda_agregada(self):
        """
        Calcula demanda agregada para cada link:
        E_d_agregada[j,t] = Σ_{i ∈ I_j} E_d[i,t]
        """
        print(f"\n📊 Calculando demanda agregada...")
        
        self.E_d_agregada = {}
        
        for j in self.L:
            for t in self.T:
                # Somar demandas de todos os links que j pode atender
                demanda_total = sum(self.E_d.get((i, t), 0) for i in self.I_j[j])
                self.E_d_agregada[(j, t)] = demanda_total
        
        # Estatísticas
        demanda_original_total = sum(self.E_d.values())
        demanda_agregada_max = max(self.E_d_agregada.values())
        
        print(f"   ✓ Demanda original total/dia: {demanda_original_total:,.0f} kWh")
        print(f"   ✓ Demanda agregada máxima (link+vizinhos): {demanda_agregada_max:,.0f} kWh")
    
    def _calcular_fator_vp(self):
        """Calcula fator de valor presente"""
        num = (1 + self.alpha)**self.Delta_h - 1
        den = self.alpha * (1 + self.alpha)**self.h * (1 + self.alpha)**self.Delta_h
        self.fator_vp = num / den
        
    def _calcular_big_m(self):
        """
        Calcula Big-M baseado em DEMANDA AGREGADA (máxima)
        CRÍTICO: Deve ser chamado APÓS _calcular_demanda_agregada()
        """
        # Máxima geração PV possível
        max_pv = max(self.P_k[k] * self.sh.get((l, t), 0) 
                     for l in self.L for t in self.T for k in self.K)
        
        # ✅ CORREÇÃO: Usar demanda AGREGADA (já calculada)
        max_dem_agregada = max(self.E_d_agregada.values())
        
        self.BIG_M = max(max_pv, max_dem_agregada) * 1.5
        
        print(f"\n🔢 Parâmetros derivados:")
        print(f"   ✓ Fator VP ({self.Delta_h} anos): {self.fator_vp:.4f}")
        print(f"   ✓ Máx PV possível: {max_pv:,.0f} kWh")
        print(f"   ✓ Máx demanda agregada: {max_dem_agregada:,.0f} kWh")
        print(f"   ✓ Big-M calculado: {self.BIG_M:,.0f} kWh")
        
    def construir(self):
        """Constrói modelo MILP com TODAS as restrições (incluindo 10 e demanda agregada)"""
        print(f"\n{'='*80}\n🔧 CONSTRUINDO MODELO FCSA MILP COMPLETO\n{'='*80}")
        print(f"📊 L={len(self.L)} | T={len(self.T)} | K={len(self.K)} | "
              f"γ={self.gamma} | α={self.alpha*100:.0f}% | r={self.raio_cobertura_km}km")
        
        m = Model('FCSA_MILP_Completo')
        
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
        
        # === RESTRIÇÕES ===
        num_restricoes = 0
        
        # ✅ (10) COBERTURA ESPACIAL
        for i in self.L:
            m.add_constraint(
                m.sum(x[j] for j in self.L_i[i]) >= 1,
                ctname=f'cobertura_espacial_{i}'
            )
            num_restricoes += 1
        print(f"✅ (10) Cobertura espacial: {num_restricoes} restrições")
        
        # (1) Linearização demanda efetiva COM DEMANDA AGREGADA
        E_d_max = max(self.E_d_agregada.values())
        for l in self.L:
            for t in self.T:
                Ed_agr = self.E_d_agregada.get((l,t), 0)
                m.add_constraint(E_d_eff[l,t] <= E_d_max * x[l])
                m.add_constraint(E_d_eff[l,t] <= Ed_agr)
                m.add_constraint(E_d_eff[l,t] >= Ed_agr - E_d_max*(1-x[l]))
                num_restricoes += 3
        print(f"✅ (1) Demanda efetiva agregada: {3*len(self.L)*len(self.T)} restrições")
        
        # (4) Balanço energético
        for l in self.L:
            for t in self.T:
                m.add_constraint(
                    E_pv[l,t] + E_minus_nm[l,t] + E[l,t] == E_d_eff[l,t] + E_plus_nm[l,t],
                    ctname=f'balanco_energia_{l}_{t}'
                )
                num_restricoes += 1
        print(f"✅ (4) Balanço energético: {len(self.L)*len(self.T)} restrições")
        
        # (5) Geração PV
        for l in self.L:
            for t in self.T:
                m.add_constraint(
                    E_pv[l,t] == m.sum(self.P_k[k]*self.sh.get((l,t),0)*w[l,k] for k in self.K),
                    ctname=f'geracao_pv_{l}_{t}'
                )
                num_restricoes += 1
        print(f"✅ (5) Geração PV: {len(self.L)*len(self.T)} restrições")
        
        # (6) Limite importação net-metering
        for l in self.L:
            for idx, t in enumerate(self.T):
                if idx > 0:
                    m.add_constraint(E_minus_nm[l,t] <= E_nm[self.T[idx-1]])
                else:
                    m.add_constraint(E_minus_nm[l,t] == 0)
                num_restricoes += 1
        print(f"✅ (6) Limite importação: {len(self.L)*len(self.T)} restrições")
        
        # (7) Balanço acumulativo créditos
        for idx, t in enumerate(self.T):
            if idx == 0:
                m.add_constraint(E_nm[t] == m.sum(E_plus_nm[l,t] - E_minus_nm[l,t] for l in self.L))
            else:
                m.add_constraint(E_nm[t] == E_nm[self.T[idx-1]] + 
                                m.sum(E_plus_nm[l,t] - E_minus_nm[l,t] for l in self.L))
            num_restricoes += 1
        print(f"✅ (7) Balanço créditos: {len(self.T)} restrições")
        
        # (8) Linearização E_lot
        for l in self.L:
            for t in self.T:
                m.add_constraint(E_lot[l,t] >= E_pv[l,t] - E_d_eff[l,t])
                m.add_constraint(E_lot[l,t] <= self.BIG_M * x_aux[l,t])
                m.add_constraint(E_lot[l,t] <= E_pv[l,t] - E_d_eff[l,t] + self.BIG_M*(1-x_aux[l,t]))
                num_restricoes += 3
        print(f"✅ (8) Linearização: {3*len(self.L)*len(self.T)} restrições")
        
        # (9) Limite exportação
        for l in self.L:
            for t in self.T:
                m.add_constraint(E_plus_nm[l,t] <= E_lot[l,t])
                num_restricoes += 1
        print(f"✅ (9) Limite exportação: {len(self.L)*len(self.T)} restrições")
        
        # (11) Área carport
        for l in self.L:
            m.add_constraint(m.sum(self.a_k[k]*w[l,k] for k in self.K) <= self.cp[l]*self.a)
            num_restricoes += 1
        print(f"✅ (11) Área carport: {len(self.L)} restrições")
        
        # (12) Carport requer estação
        for l in self.L:
            m.add_constraint(m.sum(w[l,k] for k in self.K) <= x[l])
            num_restricoes += 1
        print(f"✅ (12) Carport requer estação: {len(self.L)} restrições")
        
        print(f"\n✅ TOTAL: {num_restricoes} restrições")
        print(f"{'='*80}")
        
        self.modelo = m
        self._vars = {'x': x, 'w': w, 'E': E, 'E_pv': E_pv, 'E_minus_nm': E_minus_nm,
                      'E_plus_nm': E_plus_nm, 'E_nm': E_nm, 'E_d_eff': E_d_eff}
        
    def resolver(self):
        """Resolve modelo usando método lexicográfico"""
        if not self.modelo:
            self.construir()
        
        self.modelo.parameters.mip.tolerances.mipgap = self.mip_gap
        self.modelo.parameters.timelimit = self.time_limit
        self.modelo.parameters.threads = 0
        
        tempo_total = 0
        
        # PASSO 1: Maximizar benefícios
        print(f"\n{'='*80}\n📊 PASSO 1: MAXIMIZANDO BENEFÍCIOS\n{'='*80}")
        self.modelo.maximize(self._f_trans)
        
        t0 = time.time()
        sol1 = self.modelo.solve(log_output=self.log_output)
        tempo1 = time.time() - t0
        tempo_total += tempo1
        
        if not sol1:
            print(f"\n❌ PASSO 1 INFACTÍVEL")
            return False
        
        f_trans_otimo = sol1.objective_value
        print(f"\n✅ PASSO 1: Benefício = {f_trans_otimo:.2f} | Tempo = {tempo1:.2f}s")
        
        # PASSO 2: Minimizar custos
        print(f"\n{'='*80}\n💰 PASSO 2: MINIMIZANDO CUSTOS\n{'='*80}")
        self.modelo.add_constraint(self._f_trans >= f_trans_otimo, ctname='lexicografica')
        self.modelo.minimize(self._C_in + self._C_op)
        
        t0 = time.time()
        sol2 = self.modelo.solve(log_output=self.log_output)
        tempo2 = time.time() - t0
        tempo_total += tempo2
        
        if not sol2:
            print(f"\n❌ PASSO 2 INFACTÍVEL")
            return False
        
        print(f"\n✅ PASSO 2: Custo = R$ {sol2.objective_value:,.2f} | Tempo = {tempo2:.2f}s")
        
        self._extrair_solucao(tempo_total, f_trans_otimo)
        self._imprimir_resultados()
        
        return True
    
    def _extrair_solucao(self, tempo: float, f_trans_otimo: float):
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
            'estacoes_instaladas': est,
            'num_estacoes': len(est),
            'links_cobertos': sorted(links_cobertos),
            'num_links_cobertos': len(links_cobertos),
            'taxa_cobertura_%': (len(links_cobertos) / len(self.L)) * 100,
            'carports_instalados': cp_inst,
            'custo_investimento': custo_inv,
            'custo_operacao_vp': custo_op,
            'custo_total': custo_inv + custo_op,
            'beneficio_transporte': f_trans_otimo,
            'energia_comprada_kwh': sum(E[l,t].solution_value for l in est for t in self.T),
            'energia_pv_kwh': sum(E_pv[l,t].solution_value for l in est for t in self.T),
            'energia_exportada_kwh': sum(E_plus_nm[l,t].solution_value for l in est for t in self.T),
            'energia_importada_kwh': sum(E_minus_nm[l,t].solution_value for l in est for t in self.T),
            'creditos_finais_kwh': E_nm[self.T[-1]].solution_value
        }
        
    def _imprimir_resultados(self):
        """Imprime resultados"""
        s = self.solucao
        print(f"\n{'='*80}\n📊 SOLUÇÃO FINAL (MODELO COMPLETO)\n{'='*80}")
        print(f"⏱️  Tempo: {s['tempo_s']:.2f}s | Gap: {s['gap_%']:.2f}%")
        print(f"💰 Custo: R$ {s['custo_total']:,.2f} | Benefício: {s['beneficio_transporte']:.2f}\n")
        
        print(f"🗺️  COBERTURA ESPACIAL:")
        print(f"   ⚡ Estações: {s['num_estacoes']} → {s['estacoes_instaladas']}")
        print(f"   📍 Links cobertos: {s['num_links_cobertos']}/{len(self.L)} ({s['taxa_cobertura_%']:.0f}%)")
        print(f"   🎯 Lista: {s['links_cobertos']}\n")
        
        print(f"💰 CUSTOS:")
        print(f"   🏗️  Investimento: R$ {s['custo_investimento']:,.2f}")
        print(f"   ⚡ Operação VP: R$ {s['custo_operacao_vp']:,.2f}\n")
        
        print(f"⚡ ENERGIA:")
        print(f"   🔌 Comprada: {s['energia_comprada_kwh']:,.0f} kWh")
        print(f"   ☀️  Gerada PV: {s['energia_pv_kwh']:,.0f} kWh")
        print(f"   📤 Exportada: {s['energia_exportada_kwh']:,.0f} kWh")
        print(f"   📥 Importada: {s['energia_importada_kwh']:,.0f} kWh")
        print(f"{'='*80}")


def resolver_problema(pasta: str) -> FCSA_MILP:
    """Resolve problema FCSA MILP completo"""
    modelo = FCSA_MILP(pasta)
    modelo.resolver()
    return modelo


if __name__ == '__main__':
    modelo = resolver_problema('dados/problema0')