# """
# Modelo FCSA (Fast Charging Station Allocation) - MILP Linearizado
# Artículo 1: Modelo MINLP convertido a MILP usando linearización manuscrita
# Basado en la tesis de Caio dos Santos (Unicamp, 2021)

# VERSIÓN CORRIGIDA: Linearización con demanda efectiva (x_l * E_d)
# """

# import numpy as np
# from docplex.mp.model import Model
# import time
# from typing import List, Dict, Optional

# class ModeloFCSA_MILP:
#     def __init__(self,
#                  L: List[int],
#                  T: List[int],
#                  K: List[int],
#                  parametros: Dict):
#         """
#         Inicializa o modelo FCSA MILP linearizado
        
#         Args:
#             L: Lista de IDs de links (aristas da rede)
#             T: Lista de períodos de tempo (0, 1, ..., 23 para horas)
#             K: Lista de tipos de carport PV (0, 1, 2, ...)
#             parametros: {dict com todos os parâmetros}
#         """
#         self.L = L
#         self.T = T
#         self.K = K
#         self.params = parametros
        
#         # Extrair parâmetros
#         self.c_CS = parametros['c_CS_l']
#         self.c_PV = parametros['c_PV_k']
#         self.c_e = parametros['c_e_t']
#         self.P_k = parametros['P_k']
#         self.sh = parametros['sh_lt']
#         self.a_k = parametros['a_k']
#         self.cp = parametros['cp_l']
#         self.a = parametros.get('a', 1.0)
#         self.E_d = parametros['E_d_lt']
#         self.rho = parametros['rho_l']
#         self.beta = parametros['beta_l']
#         self.alpha = parametros['alpha']
#         self.Delta_h = parametros['Delta_h']
#         self.h = parametros.get('h', 1)
#         self.gamma = parametros['gamma']
        
#         # Calcular BIG_M se não fornecido
#         if parametros.get('BIG_M') is None:
#             self.BIG_M = self._calcular_big_m()
#         else:
#             self.BIG_M = parametros['BIG_M']
        
#         # Calcular fator de valor presente
#         self.fator_vp = self._calcular_fator_valor_presente()
        
#         # Resultados
#         self.modelo = None
#         self.estacoes_instaladas = []
#         self.carports_instalados = {}
#         self.custo_investimento = 0
#         self.custo_operacao_vp = 0
#         self.beneficio_transporte = 0
#         self.valor_objetivo = 0
#         self.tempo_solucao = 0
#         self.gap_otimalidade = 0
    
#     def _calcular_big_m(self) -> float:
#         """Calcula Big-M como a máxima geração PV possível + margem"""
#         max_geracao_pv = max(
#             self.P_k[k] * self.sh.get((l, t), 0)
#             for l in self.L
#             for t in self.T
#             for k in self.K
#         )
#         # Adicionar margem de segurança (50%)
#         return max_geracao_pv * 1.5
    
#     def _calcular_fator_valor_presente(self) -> float:
#         """
#         Calcula fator de conversão a valor presente:
#         fator = [(1+α)^Δh - 1] / [α · (1+α)^h · (1+α)^Δh]
#         """
#         alpha = self.alpha
#         Delta_h = self.Delta_h
#         h = self.h
        
#         numerador = (1 + alpha)**Delta_h - 1
#         denominador = alpha * (1 + alpha)**h * (1 + alpha)**Delta_h
        
#         return numerador / denominador
    
#     def construir_modelo(self):
#         """Constrói o modelo MILP linearizado"""
#         print("\n" + "="*80)
#         print("🔧 CONSTRUINDO MODELO FCSA MILP LINEARIZADO (v2 - CORRIGIDO)")
#         print("="*80)
#         print(f"📊 Links: {len(self.L)} | Períodos: {len(self.T)} | Tipos PV: {len(self.K)}")
#         print(f"💰 Horizonte: {self.Delta_h} anos | Taxa: {self.alpha*100:.1f}%")
#         print(f"🔢 Big-M: {self.BIG_M:.2f} | Fator VP: {self.fator_vp:.4f}")
#         print("="*80)
        
#         self.modelo = Model('FCSA_MILP_Linearizado_v2')
        
#         # ==================== VARIÁVEIS DE DECISÃO ====================
#         print("\n📝 Criando variáveis de decisão...")
        
#         # (12) x_l: Instalar estação de carga no link l
#         x = self.modelo.binary_var_dict(self.L, name='x')
#         print(f"   ✓ x_l: {len(self.L)} variáveis binárias (instalação de estação)")
        
#         # (12) w_{l,k}: Instalar carport PV tipo k no link l
#         w = {}
#         for l in self.L:
#             for k in self.K:
#                 w[(l, k)] = self.modelo.binary_var(name=f'w_{l}_{k}')
#         print(f"   ✓ w_lk: {len(self.L)*len(self.K)} variáveis binárias (carport PV)")
        
#         # (13) E_{l,t}: Energia suprida ao link l no período t
#         E = self.modelo.continuous_var_dict(
#             [(l, t) for l in self.L for t in self.T],
#             lb=0,
#             name='E'
#         )
        
#         # (5) E^{pv}_{l,t}: Geração PV no link l, período t
#         E_pv = self.modelo.continuous_var_dict(
#             [(l, t) for l in self.L for t in self.T],
#             lb=0,
#             name='E_pv'
#         )
        
#         # (14) E^{-nm}_{l,t}: Energia importada (net-metering) no link l, período t
#         E_minus_nm = self.modelo.continuous_var_dict(
#             [(l, t) for l in self.L for t in self.T],
#             lb=0,
#             name='E_minus_nm'
#         )
        
#         # (14) E^{+nm}_{l,t}: Energia exportada (net-metering) no link l, período t
#         E_plus_nm = self.modelo.continuous_var_dict(
#             [(l, t) for l in self.L for t in self.T],
#             lb=0,
#             name='E_plus_nm'
#         )
        
#         # (15) E^{lot}_{l,t}: Energia excedente disponível para exportação
#         E_lot = self.modelo.continuous_var_dict(
#             [(l, t) for l in self.L for t in self.T],
#             lb=0,
#             name='E_lot'
#         )
        
#         # (7) E^{nm}_t: Balance total de energia net-metering no período t
#         E_nm = self.modelo.continuous_var_dict(self.T, lb=-self.BIG_M*10, name='E_nm')
        
#         # VARIABLE AUXILIAR: Demanda efectiva E_d_eff = x_l * E_d_lt
#         E_d_eff = self.modelo.continuous_var_dict(
#             [(l, t) for l in self.L for t in self.T],
#             lb=0,
#             name='E_d_eff'
#         )
#         print(f"   ✓ E_d_eff_lt: {len(self.L)*len(self.T)} variáveis contínuas (demanda efetiva)")
        
#         # VARIÁVEL AUXILIAR PARA LINEARIZAÇÃO (manuscrito)
#         x_aux = self.modelo.binary_var_dict(
#             [(l, t) for l in self.L for t in self.T],
#             name='x_aux'
#         )
#         print(f"   ✓ x_aux_lt: {len(self.L)*len(self.T)} variáveis binárias (linearização)")
        
#         total_vars = self.modelo.number_of_variables
#         print(f"\n✅ Total de variáveis: {total_vars}")
        
#         # ==================== FUNÇÃO OBJETIVO (3) ====================
#         print("\n🎯 Construindo função objetivo (3 componentes)...")
        
#         # C_in: Custos de investimento
#         C_in = self.modelo.sum(
#             self.c_CS[l] * x[l] for l in self.L
#         ) + self.modelo.sum(
#             self.c_PV[k] * w[(l, k)]
#             for l in self.L
#             for k in self.K
#         )
#         print(f"   ✓ C_in: Custos de investimento (estações + carports)")
        
#         # C_op: Custos de operação (valor presente)
#         C_op = self.fator_vp * self.modelo.sum(
#             self.c_e[t] * E[(l, t)]
#             for l in self.L
#             for t in self.T
#         )
#         print(f"   ✓ C_op: Custos de operação a valor presente (fator={self.fator_vp:.4f})")
        
#         # f: Benefícios de transporte (maximizar = minimizar negativo)
#         f_transporte = -self.gamma * self.modelo.sum(
#             x[l] * self.rho[l] * self.beta[l]
#             for l in self.L
#         )
#         print(f"   ✓ f: Benefícios de transporte (γ={self.gamma})")
        
#         # Função objetivo total
#         self.modelo.minimize(C_in + C_op + f_transporte)
#         print(f"\n🎯 Função objetivo: min [C_in + C_op - γ·Σ(x_l·ρ_l·β_l)]")
        
#         # ==================== RESTRIÇÕES ====================
#         print("\n⚙️  Adicionando restrições...")
        
#         # NOVO: Linearização de E_d_eff = x_l * E_d_lt
#         E_d_max = max(self.E_d.values()) if self.E_d else 1000
#         for l in self.L:
#             for t in self.T:
#                 E_d_lt = self.E_d.get((l, t), 0)
                
#                 # Se x_l = 0: E_d_eff = 0
#                 # Se x_l = 1: E_d_eff = E_d_lt
                
#                 # E_d_eff ≤ E_d_max * x_l
#                 self.modelo.add_constraint(
#                     E_d_eff[(l, t)] <= E_d_max * x[l],
#                     ctname=f'demanda_eff_ub_{l}_{t}'
#                 )
                
#                 # E_d_eff ≤ E_d_lt (sempre)
#                 self.modelo.add_constraint(
#                     E_d_eff[(l, t)] <= E_d_lt,
#                     ctname=f'demanda_eff_ub2_{l}_{t}'
#                 )
                
#                 # E_d_eff ≥ E_d_lt - E_d_max * (1 - x_l)
#                 # Se x_l = 1: E_d_eff ≥ E_d_lt
#                 # Se x_l = 0: E_d_eff ≥ E_d_lt - E_d_max (relaxado, pero E_d_eff ≤ 0 lo fuerza a 0)
#                 self.modelo.add_constraint(
#                     E_d_eff[(l, t)] >= E_d_lt - E_d_max * (1 - x[l]),
#                     ctname=f'demanda_eff_lb_{l}_{t}'
#                 )
#         print(f"   ✓ (NEW) Linearização E_d_eff = x_l * E_d: {3*len(self.L)*len(self.T)} restrições")
        
#         # (4) Balance energético: E^{pv}_{l,t} + E^{-nm}_{l,t} + E^{+nm}_{l,t} = E_d_eff_{l,t} + E_{l,t}
#         for l in self.L:
#             for t in self.T:
#                 self.modelo.add_constraint(
#                     E_pv[(l, t)] + E_minus_nm[(l, t)] + E_plus_nm[(l, t)]
#                     == E_d_eff[(l, t)] + E[(l, t)],
#                     ctname=f'balance_energia_{l}_{t}'
#                 )
#         print(f"   ✓ (4) Balance energético: {len(self.L)*len(self.T)} restrições")
        
#         # (5) Geração PV: E^{pv}_{l,t} = Σ_k P_k · sh_{l,t} · w_{l,k}
#         for l in self.L:
#             for t in self.T:
#                 self.modelo.add_constraint(
#                     E_pv[(l, t)] == self.modelo.sum(
#                         self.P_k[k] * self.sh.get((l, t), 0) * w[(l, k)]
#                         for k in self.K
#                     ),
#                     ctname=f'geracao_pv_{l}_{t}'
#                 )
#         print(f"   ✓ (5) Geração PV: {len(self.L)*len(self.T)} restrições")
        
#         # (6) Limite de importação: E^{-nm}_{l,t} ≤ E^{nm}_{t-1}
#         for l in self.L:
#             for idx, t in enumerate(self.T):
#                 if idx > 0:  # Para t > 0
#                     t_anterior = self.T[idx - 1]
#                     self.modelo.add_constraint(
#                         E_minus_nm[(l, t)] <= E_nm[t_anterior],
#                         ctname=f'limite_importacao_{l}_{t}'
#                     )
#                 else:  # Para t = 0, não pode importar (sem créditos prévios)
#                     self.modelo.add_constraint(
#                         E_minus_nm[(l, t)] == 0,
#                         ctname=f'sem_creditos_iniciais_{l}_{t}'
#                     )
#         print(f"   ✓ (6) Limite de importação: {len(self.L)*len(self.T)} restrições")
        
#         # (7) Balance total net-metering: E^{nm}_t = Σ_l (E^{+nm}_{l,t} - E^{-nm}_{l,t})
#         for t in self.T:
#             self.modelo.add_constraint(
#                 E_nm[t] == self.modelo.sum(
#                     E_plus_nm[(l, t)] - E_minus_nm[(l, t)]
#                     for l in self.L
#                 ),
#                 ctname=f'balance_nm_total_{t}'
#             )
#         print(f"   ✓ (7) Balance total net-metering: {len(self.T)} restrições")
        
#         # (8) LINEARIZAÇÃO CORRIGIDA: E^{lot}_{l,t} = max{0, E^{pv}_{l,t} - E_d_eff_{l,t}}
#         # Usando técnica do manuscrito com Big-M único
#         print(f"\n   🔧 APLICANDO LINEARIZAÇÃO MANUSCRITA (Big-M único) - VERSÃO CORRIGIDA...")
        
#         for l in self.L:
#             for t in self.T:
#                 # Ahora usamos E_d_eff en lugar de E_d_lt directamente
                
#                 # (L1) E^{lot} ≥ 0  [já garantido por lower bound]
                
#                 # (L2) E^{lot} ≥ E^{pv} - E_d_eff
#                 self.modelo.add_constraint(
#                     E_lot[(l, t)] >= E_pv[(l, t)] - E_d_eff[(l, t)],
#                     ctname=f'lin_L2_{l}_{t}'
#                 )
                
#                 # (L3) E^{lot} ≤ BIG_M · x_aux
#                 # Se x_aux=0 (não há excedente), força E^{lot}=0
#                 self.modelo.add_constraint(
#                     E_lot[(l, t)] <= self.BIG_M * x_aux[(l, t)],
#                     ctname=f'lin_L3_{l}_{t}'
#                 )
                
#                 # (L4) E^{lot} ≤ (E^{pv} - E_d_eff) + BIG_M · (1 - x_aux)
#                 # Se x_aux=1 (há excedente), força E^{lot} ≤ E^{pv} - E_d_eff
#                 self.modelo.add_constraint(
#                     E_lot[(l, t)] <= (E_pv[(l, t)] - E_d_eff[(l, t)]) + self.BIG_M * (1 - x_aux[(l, t)]),
#                     ctname=f'lin_L4_{l}_{t}'
#                 )
        
#         print(f"   ✓ (8-Lin) Linearização max{{0, E^pv - E_d_eff}}: {4*len(self.L)*len(self.T)} restrições")
        
#         # (9) Limite de exportação: E^{+nm}_{l,t} ≤ E^{lot}_{l,t}
#         for l in self.L:
#             for t in self.T:
#                 self.modelo.add_constraint(
#                     E_plus_nm[(l, t)] <= E_lot[(l, t)],
#                     ctname=f'limite_exportacao_{l}_{t}'
#                 )
#         print(f"   ✓ (9) Limite de exportação: {len(self.L)*len(self.T)} restrições")
        
#         # (10) Restrição de área do carport: Σ_k a_k · w_{l,k} ≤ cp_l · a
#         for l in self.L:
#             self.modelo.add_constraint(
#                 self.modelo.sum(
#                     self.a_k[k] * w[(l, k)]
#                     for k in self.K
#                 ) <= self.cp[l] * self.a,
#                 ctname=f'area_carport_{l}'
#             )
#         print(f"   ✓ (10) Restrição de área: {len(self.L)} restrições")
        
#         # (11) Carport requer estação: Σ_k w_{l,k} ≤ x_l
#         for l in self.L:
#             self.modelo.add_constraint(
#                 self.modelo.sum(w[(l, k)] for k in self.K) <= x[l],
#                 ctname=f'carport_requer_estacao_{l}'
#             )
#         print(f"   ✓ (11) Carport requer estação: {len(self.L)} restrições")
        
#         total_restricoes = self.modelo.number_of_constraints
#         print(f"\n✅ Total de restrições: {total_restricoes}")
        
#         # Salvar variáveis para extração de resultados
#         self._vars = {
#             'x': x,
#             'w': w,
#             'E': E,
#             'E_pv': E_pv,
#             'E_minus_nm': E_minus_nm,
#             'E_plus_nm': E_plus_nm,
#             'E_lot': E_lot,
#             'E_nm': E_nm,
#             'E_d_eff': E_d_eff,
#             'x_aux': x_aux
#         }
        
#         print("\n" + "="*80)
#         print(f"✅ MODELO CONSTRUÍDO COM SUCESSO (v2 - CORRIGIDO)")
#         print(f"📊 Variáveis: {total_vars} | Restrições: {total_restricoes}")
#         print(f"🔢 Variáveis binárias: {len(self.L) + len(self.L)*len(self.K) + len(self.L)*len(self.T)}")
#         print(f"🔢 Variáveis contínuas: {total_vars - (len(self.L) + len(self.L)*len(self.K) + len(self.L)*len(self.T))}")
#         print("="*80)
    
#     def resolver(self, time_limit: int = 600, mip_gap: float = 0.01, log_output: bool = True):
#         """Resolve o modelo MILP"""
#         if self.modelo is None:
#             self.construir_modelo()
        
#         print("\n" + "="*80)
#         print("🚀 RESOLVENDO MODELO FCSA MILP")
#         print("="*80)
#         print(f"⏱️  Limite de tempo: {time_limit}s")
#         print(f"🎯 Gap MIP: {mip_gap*100}%")
#         print("="*80)
        
#         # Configurar parâmetros do solver
#         self.modelo.parameters.mip.tolerances.mipgap = mip_gap
#         self.modelo.parameters.timelimit = time_limit
#         self.modelo.parameters.threads = 0  # Usar todos os threads disponíveis
        
#         # Resolver
#         inicio = time.time()
#         solucao = self.modelo.solve(log_output=log_output)
#         self.tempo_solucao = time.time() - inicio
        
#         if solucao:
#             self.gap_otimalidade = self.modelo.solve_details.mip_relative_gap * 100
#             print("\n" + "="*80)
#             print("✅ SOLUÇÃO ENCONTRADA")
#             print("="*80)
#             print(f"⏱️  Tempo: {self.tempo_solucao:.2f}s")
#             print(f"🎯 Gap: {self.gap_otimalidade:.2f}%")
#             print(f"📊 Valor objetivo: R$ {self.modelo.objective_value:,.2f}")
#             print("="*80)
            
#             self._extrair_resultados()
#             return True
#         else:
#             print("\n" + "="*80)
#             print("❌ MODELO INFACTÍVEL OU SEM SOLUÇÃO")
#             print("="*80)
#             print(f"⏱️  Tempo decorrido: {self.tempo_solucao:.2f}s")
#             print("="*80)
#             return False
    
#     def _extrair_resultados(self):
#         """Extrai resultados da solução"""
#         x = self._vars['x']
#         w = self._vars['w']
#         E = self._vars['E']
#         E_nm = self._vars['E_nm']
        
#         # Estações instaladas
#         self.estacoes_instaladas = [l for l in self.L if x[l].solution_value > 0.5]
        
#         # Carports instalados
#         self.carports_instalados = {}
#         for l in self.estacoes_instaladas:
#             for k in self.K:
#                 if w[(l, k)].solution_value > 0.5:
#                     self.carports_instalados[l] = k
#                     break
        
#         # Custos de investimento
#         self.custo_investimento = sum(
#             self.c_CS[l] for l in self.estacoes_instaladas
#         ) + sum(
#             self.c_PV[k] for l, k in self.carports_instalados.items()
#         )
        
#         # Custos de operação (valor presente)
#         custo_energia_anual = sum(
#             self.c_e[t] * E[(l, t)].solution_value
#             for l in self.estacoes_instaladas
#             for t in self.T
#         )
#         self.custo_operacao_vp = self.fator_vp * custo_energia_anual
        
#         # Benefícios de transporte
#         self.beneficio_transporte = sum(
#             self.rho[l] * self.beta[l]
#             for l in self.estacoes_instaladas
#         )
        
#         # Valor objetivo
#         self.valor_objetivo = self.modelo.objective_value
    
#     def obter_resumo(self) -> Dict:
#         """Retorna resumo dos resultados"""
#         return {
#             'estacoes_instaladas': len(self.estacoes_instaladas),
#             'localizacoes': self.estacoes_instaladas,
#             'carports_instalados': self.carports_instalados,
#             'custo_investimento': self.custo_investimento,
#             'custo_operacao_vp': self.custo_operacao_vp,
#             'beneficio_transporte': self.beneficio_transporte,
#             'valor_objetivo': self.valor_objetivo,
#             'tempo_solucao': self.tempo_solucao,
#             'gap_otimalidade': self.gap_otimalidade
#         }
    
#     def imprimir_resultados(self):
#         """Imprime resultados detalhados"""
#         print("\n" + "="*80)
#         print("📊 RESULTADOS FINAIS - MODELO FCSA MILP")
#         print("="*80)
        
#         print(f"\n🏗️  INVESTIMENTO:")
#         print(f"   ⚡ Estações instaladas: {len(self.estacoes_instaladas)}")
#         print(f"   ☀️  Carports PV instalados: {len(self.carports_instalados)}")
#         print(f"   💰 Custo total de investimento: R$ {self.custo_investimento:,.2f}")
        
#         print(f"\n💡 OPERAÇÃO:")
#         print(f"   💰 Custo de operação (VP {self.Delta_h} anos): R$ {self.custo_operacao_vp:,.2f}")
        
#         print(f"\n🚗 TRANSPORTE:")
#         print(f"   📊 Benefício de transporte: {self.beneficio_transporte:.2f}")
#         print(f"   ⚖️  Peso γ: {self.gamma}")
        
#         print(f"\n🎯 OTIMIZAÇÃO:")
#         print(f"   💰 Valor objetivo total: R$ {self.valor_objetivo:,.2f}")
#         print(f"   ⏱️  Tempo de solução: {self.tempo_solucao:.2f}s")
#         print(f"   🎯 Gap de otimalidade: {self.gap_otimalidade:.2f}%")
        
#         print(f"\n📍 DETALHES DAS ESTAÇÕES:")
#         for l in self.estacoes_instaladas:
#             tipo_pv = self.carports_instalados.get(l, None)
#             if tipo_pv is not None:
#                 potencia = self.P_k[tipo_pv]
#                 print(f"   Link {l}: Estação + Carport PV Tipo {tipo_pv} ({potencia} kW)")
#             else:
#                 print(f"   Link {l}: Estação (sem carport PV)")
        
#         print("\n" + "="*80)










"""
Modelo FCSA (Fast Charging Station Allocation) - MILP Linearizado
Versión SIMPLIFICADA sin net-metering para validación
Basado en la tesis de Caio dos Santos (Unicamp, 2021)

VERSIÓN v5 - SIMPLIFICADA:
- Balance energético simplificado (sin net-metering)
- Permite validar estructura básica del modelo
- Una vez validado, agregar net-metering
"""

import numpy as np
from docplex.mp.model import Model
import time
from typing import List, Dict, Optional

class ModeloFCSA_MILP:
    def __init__(self,
                 L: List[int],
                 T: List[int],
                 K: List[int],
                 parametros: Dict):
        """
        Inicializa o modelo FCSA MILP linearizado (versão simplificada)
        
        Args:
            L: Lista de IDs de links
            T: Lista de períodos de tempo
            K: Lista de tipos de carport PV
            parametros: Dicionário com todos os parâmetros
        """
        self.L = L
        self.T = T
        self.K = K
        self.params = parametros
        
        # Extrair parâmetros
        self.c_CS = parametros['c_CS_l']
        self.c_PV = parametros['c_PV_k']
        self.c_e = parametros['c_e_t']
        self.P_k = parametros['P_k']
        self.sh = parametros['sh_lt']
        self.a_k = parametros['a_k']
        self.cp = parametros['cp_l']
        self.a = parametros.get('a', 1.0)
        self.E_d = parametros['E_d_lt']
        self.rho = parametros['rho_l']
        self.beta = parametros['beta_l']
        self.alpha = parametros['alpha']
        self.Delta_h = parametros['Delta_h']
        self.h = parametros.get('h', 1)
        self.gamma = parametros['gamma']
        self.min_estacoes = parametros.get('min_estacoes', 1)
        
        # Calcular BIG_M
        if parametros.get('BIG_M') is None:
            self.BIG_M = self._calcular_big_m()
        else:
            self.BIG_M = parametros['BIG_M']
        
        # Calcular fator de valor presente
        self.fator_vp = self._calcular_fator_valor_presente()
        
        # Resultados
        self.modelo = None
        self.estacoes_instaladas = []
        self.carports_instalados = {}
        self.custo_investimento = 0
        self.custo_operacao_vp = 0
        self.beneficio_transporte = 0
        self.valor_objetivo = 0
        self.tempo_solucao = 0
        self.gap_otimalidade = 0
    
    def _calcular_big_m(self) -> float:
        """Calcula Big-M como a máxima demanda possível"""
        max_demanda = max(self.E_d.values()) if self.E_d else 1000
        return max_demanda * 1.5
    
    def _calcular_fator_valor_presente(self) -> float:
        """Calcula fator de conversão a valor presente"""
        alpha = self.alpha
        Delta_h = self.Delta_h
        h = self.h
        
        numerador = (1 + alpha)**Delta_h - 1
        denominador = alpha * (1 + alpha)**h * (1 + alpha)**Delta_h
        
        return numerador / denominador
    
    def construir_modelo(self):
        """Constrói o modelo MILP linearizado (versão simplificada)"""
        print("\n" + "="*80)
        print("🔧 CONSTRUINDO MODELO FCSA MILP (v5 - SIMPLIFICADO SEM NET-METERING)")
        print("="*80)
        print(f"📊 Links: {len(self.L)} | Períodos: {len(self.T)} | Tipos PV: {len(self.K)}")
        print(f"💰 Horizonte: {self.Delta_h} anos | Taxa: {self.alpha*100:.1f}%")
        print(f"🔢 Big-M: {self.BIG_M:.2f} | Fator VP: {self.fator_vp:.4f}")
        print(f"🎯 γ (transporte): {self.gamma} | Mín. estações: {self.min_estacoes}")
        print("="*80)
        
        self.modelo = Model('FCSA_MILP_Simplificado_v5')
        
        # ==================== VARIÁVEIS DE DECISÃO ====================
        print("\n📝 Criando variáveis de decisão...")
        
        # x_l: Instalar estação no link l
        x = self.modelo.binary_var_dict(self.L, name='x')
        print(f"   ✓ x_l: {len(self.L)} variáveis binárias (instalação)")
        
        # w_{l,k}: Instalar carport PV tipo k no link l
        w = {}
        for l in self.L:
            for k in self.K:
                w[(l, k)] = self.modelo.binary_var(name=f'w_{l}_{k}')
        print(f"   ✓ w_lk: {len(self.L)*len(self.K)} variáveis binárias (carport PV)")
        
        # E_pv_{l,t}: Geração PV no link l, período t
        E_pv = self.modelo.continuous_var_dict(
            [(l, t) for l in self.L for t in self.T],
            lb=0,
            name='E_pv'
        )
        
        # E_comprada_{l,t}: Energia COMPRADA da rede (pode ser zero se PV suficiente)
        E_comprada = self.modelo.continuous_var_dict(
            [(l, t) for l in self.L for t in self.T],
            lb=0,
            name='E_comprada'
        )
        
        # E_d_eff_{l,t}: Demanda efetiva = x_l * E_d_{l,t}
        E_d_eff = self.modelo.continuous_var_dict(
            [(l, t) for l in self.L for t in self.T],
            lb=0,
            name='E_d_eff'
        )
        print(f"   ✓ E_pv, E_comprada, E_d_eff: {3*len(self.L)*len(self.T)} variáveis contínuas")
        
        total_vars = self.modelo.number_of_variables
        print(f"\n✅ Total de variáveis: {total_vars}")
        
        # ==================== FUNÇÃO OBJETIVO ====================
        print("\n🎯 Construindo função objetivo...")
        
        # Custos de investimento
        C_in = self.modelo.sum(
            self.c_CS[l] * x[l] for l in self.L
        ) + self.modelo.sum(
            self.c_PV[k] * w[(l, k)]
            for l in self.L
            for k in self.K
        )
        
        # Custos de operação (energia comprada)
        C_op = self.fator_vp * self.modelo.sum(
            self.c_e[t] * E_comprada[(l, t)]
            for l in self.L
            for t in self.T
        )
        
        # Benefícios de transporte
        f_transporte = self.gamma * self.modelo.sum(
            x[l] * self.rho[l] * self.beta[l]
            for l in self.L
        )
        
        # Minimizar: custos - benefícios
        self.modelo.minimize(C_in + C_op - f_transporte)
        print(f"   ✓ FO: min [C_inv + C_op - γ·benefícios]")
        
        # ==================== RESTRIÇÕES ====================
        print("\n⚙️  Adicionando restrições...")
        
        # (0) Cobertura mínima
        self.modelo.add_constraint(
            self.modelo.sum(x[l] for l in self.L) >= self.min_estacoes,
            ctname='cobertura_minima'
        )
        print(f"   ✓ (0) Cobertura mínima: >= {self.min_estacoes} estação")
        
        # (1) Linearização: E_d_eff = x_l * E_d_lt
        E_d_max = max(self.E_d.values()) if self.E_d else 1000
        for l in self.L:
            for t in self.T:
                E_d_lt = self.E_d.get((l, t), 0)
                
                self.modelo.add_constraint(
                    E_d_eff[(l, t)] <= E_d_max * x[l],
                    ctname=f'demanda_ub1_{l}_{t}'
                )
                
                self.modelo.add_constraint(
                    E_d_eff[(l, t)] <= E_d_lt,
                    ctname=f'demanda_ub2_{l}_{t}'
                )
                
                self.modelo.add_constraint(
                    E_d_eff[(l, t)] >= E_d_lt - E_d_max * (1 - x[l]),
                    ctname=f'demanda_lb_{l}_{t}'
                )
        print(f"   ✓ (1) Linearização E_d_eff: {3*len(self.L)*len(self.T)} restrições")
        
        # (2) Geração PV: E_pv = Σ_k P_k · sh · w_k
        for l in self.L:
            for t in self.T:
                self.modelo.add_constraint(
                    E_pv[(l, t)] == self.modelo.sum(
                        self.P_k[k] * self.sh.get((l, t), 0) * w[(l, k)]
                        for k in self.K
                    ),
                    ctname=f'geracao_pv_{l}_{t}'
                )
        print(f"   ✓ (2) Geração PV: {len(self.L)*len(self.T)} restrições")
        
        # (3) Balance energético SIMPLIFICADO:
        # E_comprada >= Demanda - Geração PV
        # (Se PV > Demanda, E_comprada pode ser zero, excedente é desperdiçado)
        for l in self.L:
            for t in self.T:
                self.modelo.add_constraint(
                    E_comprada[(l, t)] >= E_d_eff[(l, t)] - E_pv[(l, t)],
                    ctname=f'balance_energia_{l}_{t}'
                )
        print(f"   ✓ (3) Balance energético: {len(self.L)*len(self.T)} restrições")
        
        # (4) Restrição de área do carport
        for l in self.L:
            self.modelo.add_constraint(
                self.modelo.sum(
                    self.a_k[k] * w[(l, k)]
                    for k in self.K
                ) <= self.cp[l] * self.a,
                ctname=f'area_carport_{l}'
            )
        print(f"   ✓ (4) Área de carport: {len(self.L)} restrições")
        
        # (5) Carport requer estação
        for l in self.L:
            self.modelo.add_constraint(
                self.modelo.sum(w[(l, k)] for k in self.K) <= x[l],
                ctname=f'carport_requer_estacao_{l}'
            )
        print(f"   ✓ (5) Carport requer estação: {len(self.L)} restrições")
        
        total_restricoes = self.modelo.number_of_constraints
        print(f"\n✅ Total de restrições: {total_restricoes}")
        
        # Salvar variáveis
        self._vars = {
            'x': x,
            'w': w,
            'E_pv': E_pv,
            'E_comprada': E_comprada,
            'E_d_eff': E_d_eff
        }
        
        print("\n" + "="*80)
        print(f"✅ MODELO CONSTRUÍDO (v5 - SIMPLIFICADO)")
        print(f"📊 Variáveis: {total_vars} | Restrições: {total_restricoes}")
        print("="*80)
    
    def resolver(self, time_limit: int = 600, mip_gap: float = 0.01, log_output: bool = True):
        """Resolve o modelo MILP"""
        if self.modelo is None:
            self.construir_modelo()
        
        print("\n" + "="*80)
        print("🚀 RESOLVENDO MODELO FCSA MILP SIMPLIFICADO")
        print("="*80)
        print(f"⏱️  Limite: {time_limit}s | Gap: {mip_gap*100}%")
        print("="*80)
        
        self.modelo.parameters.mip.tolerances.mipgap = mip_gap
        self.modelo.parameters.timelimit = time_limit
        self.modelo.parameters.threads = 0
        
        inicio = time.time()
        solucao = self.modelo.solve(log_output=log_output)
        self.tempo_solucao = time.time() - inicio
        
        if solucao:
            self.gap_otimalidade = self.modelo.solve_details.mip_relative_gap * 100
            print("\n" + "="*80)
            print("✅ SOLUÇÃO ENCONTRADA")
            print("="*80)
            print(f"⏱️  Tempo: {self.tempo_solucao:.2f}s")
            print(f"🎯 Gap: {self.gap_otimalidade:.2f}%")
            print(f"📊 Valor objetivo: R$ {self.modelo.objective_value:,.2f}")
            print("="*80)
            
            self._extrair_resultados()
            return True
        else:
            print("\n" + "="*80)
            print("❌ MODELO INFACTÍVEL OU SEM SOLUÇÃO")
            print("="*80)
            print(f"⏱️  Tempo: {self.tempo_solucao:.2f}s")
            print("="*80)
            return False
    
    def _extrair_resultados(self):
        """Extrai resultados da solução"""
        x = self._vars['x']
        w = self._vars['w']
        E_comprada = self._vars['E_comprada']
        E_pv = self._vars['E_pv']
        
        # Estações instaladas
        self.estacoes_instaladas = [l for l in self.L if x[l].solution_value > 0.5]
        
        # Carports instalados
        self.carports_instalados = {}
        for l in self.estacoes_instaladas:
            for k in self.K:
                if w[(l, k)].solution_value > 0.5:
                    self.carports_instalados[l] = k
                    break
        
        # Custos de investimento
        self.custo_investimento = sum(
            self.c_CS[l] for l in self.estacoes_instaladas
        ) + sum(
            self.c_PV[k] for l, k in self.carports_instalados.items()
        )
        
        # Custos de operação
        custo_energia_anual = sum(
            self.c_e[t] * E_comprada[(l, t)].solution_value
            for l in self.estacoes_instaladas
            for t in self.T
        )
        self.custo_operacao_vp = self.fator_vp * custo_energia_anual
        
        # Benefícios de transporte
        self.beneficio_transporte = sum(
            self.rho[l] * self.beta[l]
            for l in self.estacoes_instaladas
        )
        
        # Valor objetivo
        self.valor_objetivo = self.modelo.objective_value
        
        # Estatísticas de energia
        self.energia_total_comprada = sum(
            E_comprada[(l, t)].solution_value
            for l in self.estacoes_instaladas
            for t in self.T
        )
        
        self.energia_total_gerada_pv = sum(
            E_pv[(l, t)].solution_value
            for l in self.estacoes_instaladas
            for t in self.T
        )
    
    def obter_resumo(self) -> Dict:
        """Retorna resumo dos resultados"""
        return {
            'estacoes_instaladas': len(self.estacoes_instaladas),
            'localizacoes': self.estacoes_instaladas,
            'carports_instalados': self.carports_instalados,
            'custo_investimento': self.custo_investimento,
            'custo_operacao_vp': self.custo_operacao_vp,
            'beneficio_transporte': self.beneficio_transporte,
            'valor_objetivo': self.valor_objetivo,
            'tempo_solucao': self.tempo_solucao,
            'gap_otimalidade': self.gap_otimalidade,
            'energia_comprada': getattr(self, 'energia_total_comprada', 0),
            'energia_gerada_pv': getattr(self, 'energia_total_gerada_pv', 0)
        }
    
    def imprimir_resultados(self):
        """Imprime resultados detalhados"""
        print("\n" + "="*80)
        print("📊 RESULTADOS FINAIS - MODELO FCSA MILP (SIMPLIFICADO)")
        print("="*80)
        
        print(f"\n🏗️  INVESTIMENTO:")
        print(f"   ⚡ Estações instaladas: {len(self.estacoes_instaladas)}")
        print(f"   📍 Localizações: {self.estacoes_instaladas}")
        print(f"   ☀️  Carports PV instalados: {len(self.carports_instalados)}")
        print(f"   💰 Custo total: R$ {self.custo_investimento:,.2f}")
        
        print(f"\n💡 OPERAÇÃO:")
        print(f"   💰 Custo VP ({self.Delta_h} anos): R$ {self.custo_operacao_vp:,.2f}")
        print(f"   🔌 Energia comprada: {self.energia_total_comprada:,.1f} kWh")
        print(f"   ☀️  Energia gerada PV: {self.energia_total_gerada_pv:,.1f} kWh")
        
        print(f"\n🚗 TRANSPORTE:")
        print(f"   📊 Benefício total: {self.beneficio_transporte:.2f}")
        print(f"   ⚖️  Peso γ: {self.gamma}")
        print(f"   💡 Contribuição FO: R$ {-self.gamma * self.beneficio_transporte:,.2f}")
        
        print(f"\n🎯 OTIMIZAÇÃO:")
        print(f"   💰 Valor objetivo: R$ {self.valor_objetivo:,.2f}")
        print(f"   ⏱️  Tempo: {self.tempo_solucao:.2f}s")
        print(f"   🎯 Gap: {self.gap_otimalidade:.2f}%")
        
        print(f"\n📍 DETALHES DAS ESTAÇÕES:")
        for l in self.estacoes_instaladas:
            tipo_pv = self.carports_instalados.get(l, None)
            custo_est = self.c_CS[l]
            beneficio = self.rho[l] * self.beta[l]
            
            if tipo_pv is not None:
                potencia = self.P_k[tipo_pv]
                custo_pv = self.c_PV[tipo_pv]
                print(f"   Link {l}:")
                print(f"      - Estação: R$ {custo_est:,.0f}")
                print(f"      - Carport PV Tipo {tipo_pv}: {potencia} kW (R$ {custo_pv:,.0f})")
                print(f"      - Benefício: {beneficio:.1f}")
                print(f"      - Total: R$ {custo_est + custo_pv:,.0f}")
            else:
                print(f"   Link {l}:")
                print(f"      - Estação: R$ {custo_est:,.0f} (sem PV)")
                print(f"      - Benefício: {beneficio:.1f}")
        
        print("\n" + "="*80)
        print("⚠️  NOTA: Modelo simplificado SEM net-metering")
        print("   Excedentes PV são desperdiçados (não geram créditos)")
        print("="*80)