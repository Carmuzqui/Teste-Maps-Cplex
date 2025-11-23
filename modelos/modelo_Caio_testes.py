"""
Modelo FCSA (Fast Charging Station Allocation) - MILP Linearizado
Artigo 1: Modelo MINLP convertido em MILP usando linearização manuscrita
Baseado na tese de Caio dos Santos (Unicamp, 2021)

VERSÃO v7 - BALANÇO ENERGÉTICO CORRIGIDO:
- Balanço energético CORRETO: E^pv + E^-nm + E = E^d_eff + E^+nm
- E (compra) agora está do lado esquerdo (ENTRADAS)
- Net-metering completo com créditos acumulativos
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
        Inicializa o modelo FCSA MILP linearizado
        
        Args:
            L: Lista de IDs de links (arestas da rede)
            T: Lista de períodos de tempo (0, 1, ..., 23 para horas)
            K: Lista de tipos de carport PV (0, 1, 2, ...)
            parametros: Dicionário completo de parâmetros
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
        """Calcula Big-M adequado para linearização"""
        max_geracao_pv = max(
            self.P_k[k] * self.sh.get((l, t), 0)
            for l in self.L
            for t in self.T
            for k in self.K
        )
        max_demanda = max(self.E_d.values()) if self.E_d else 1000
        
        # Big-M deve cobrir o máximo entre geração e demanda
        return max(max_geracao_pv, max_demanda) * 1.5
    
    def _calcular_fator_valor_presente(self) -> float:
        """
        Calcula fator de conversão a valor presente:
        fator = [(1+α)^Δh - 1] / [α · (1+α)^h · (1+α)^Δh]
        """
        alpha = self.alpha
        Delta_h = self.Delta_h
        h = self.h
        
        numerador = (1 + alpha)**Delta_h - 1
        denominador = alpha * (1 + alpha)**h * (1 + alpha)**Delta_h
        
        return numerador / denominador
    
    def construir_modelo(self):
        """Constrói o modelo MILP linearizado com net-metering"""
        print("\n" + "="*80)
        print("🔧 CONSTRUINDO MODELO FCSA MILP (v7 - BALANÇO CORRIGIDO)")
        print("="*80)
        print(f"📊 Links: {len(self.L)} | Períodos: {len(self.T)} | Tipos PV: {len(self.K)}")
        print(f"💰 Horizonte: {self.Delta_h} anos | Taxa: {self.alpha*100:.1f}%")
        print(f"🔢 Big-M: {self.BIG_M:.2f} | Fator VP: {self.fator_vp:.4f}")
        print(f"🎯 γ (transporte): {self.gamma} | Mín. estações: {self.min_estacoes}")
        print("="*80)
        
        self.modelo = Model('FCSA_MILP_v7')
        
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
        
        # E_{l,t}: Energia COMPRADA da rede
        E = self.modelo.continuous_var_dict(
            [(l, t) for l in self.L for t in self.T],
            lb=0,
            name='E'
        )
        
        # E^{pv}_{l,t}: Geração PV
        E_pv = self.modelo.continuous_var_dict(
            [(l, t) for l in self.L for t in self.T],
            lb=0,
            name='E_pv'
        )
        
        # E^{-nm}_{l,t}: Energia importada (usando créditos)
        E_minus_nm = self.modelo.continuous_var_dict(
            [(l, t) for l in self.L for t in self.T],
            lb=0,
            name='E_minus_nm'
        )
        
        # E^{+nm}_{l,t}: Energia exportada (gerando créditos)
        E_plus_nm = self.modelo.continuous_var_dict(
            [(l, t) for l in self.L for t in self.T],
            lb=0,
            name='E_plus_nm'
        )
        
        # E^{lot}_{l,t}: Energia excedente disponível para exportação
        E_lot = self.modelo.continuous_var_dict(
            [(l, t) for l in self.L for t in self.T],
            lb=0,
            name='E_lot'
        )
        
        # E^{nm}_t: Créditos acumulados disponíveis no período t
        E_nm = self.modelo.continuous_var_dict(self.T, lb=0, name='E_nm')
        
        print(f"   ✓ Variáveis energéticas: {6*len(self.L)*len(self.T) + len(self.T)} contínuas")
        
        # E_d_eff_{l,t}: Demanda efetiva = x_l * E_d_{l,t}
        E_d_eff = self.modelo.continuous_var_dict(
            [(l, t) for l in self.L for t in self.T],
            lb=0,
            name='E_d_eff'
        )
        
        # x_aux_{l,t}: Variável auxiliar para linearização de max{0, E_pv - E_d_eff}
        x_aux = self.modelo.binary_var_dict(
            [(l, t) for l in self.L for t in self.T],
            name='x_aux'
        )
        print(f"   ✓ Variáveis auxiliares: {len(self.L)*len(self.T)} contínuas + {len(self.L)*len(self.T)} binárias")
        
        total_vars = self.modelo.number_of_variables
        print(f"\n✅ Total de variáveis: {total_vars}")
        
        # ==================== FUNÇÃO OBJETIVO (3) ====================
        print("\n🎯 Construindo função objetivo (3 componentes)...")
        
        # C_in: Custos de investimento (estações + carports)
        C_in = self.modelo.sum(
            self.c_CS[l] * x[l] for l in self.L
        ) + self.modelo.sum(
            self.c_PV[k] * w[(l, k)]
            for l in self.L
            for k in self.K
        )
        print(f"   ✓ C_in: Custos de investimento")
        
        # C_op: Custos de operação (energia comprada da rede)
        C_op = self.fator_vp * self.modelo.sum(
            self.c_e[t] * E[(l, t)]
            for l in self.L
            for t in self.T
        )
        print(f"   ✓ C_op: Custos operacionais (VP {self.Delta_h} anos)")
        
        # f: Benefícios de transporte
        f_transporte = self.gamma * self.modelo.sum(
            x[l] * self.rho[l] * self.beta[l]
            for l in self.L
        )
        print(f"   ✓ f: Benefícios de transporte (γ={self.gamma})")
        
        # Minimizar: custos - benefícios
        self.modelo.minimize(C_in + C_op - f_transporte)
        print(f"\n🎯 FO: min [C_in + C_op - γ·Σ(x_l·ρ_l·β_l)]")
        
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
                
                # E_d_eff ≤ E_d_max * x_l
                self.modelo.add_constraint(
                    E_d_eff[(l, t)] <= E_d_max * x[l],
                    ctname=f'demanda_ub1_{l}_{t}'
                )
                
                # E_d_eff ≤ E_d_lt
                self.modelo.add_constraint(
                    E_d_eff[(l, t)] <= E_d_lt,
                    ctname=f'demanda_ub2_{l}_{t}'
                )
                
                # E_d_eff ≥ E_d_lt - E_d_max * (1 - x_l)
                self.modelo.add_constraint(
                    E_d_eff[(l, t)] >= E_d_lt - E_d_max * (1 - x[l]),
                    ctname=f'demanda_lb_{l}_{t}'
                )
        print(f"   ✓ (1) Linearização E_d_eff = x_l * E_d: {3*len(self.L)*len(self.T)} restrições")
        
        # ✓✓✓ (4) BALANÇO ENERGÉTICO CORRETO - v7 ✓✓✓
        # ENTRADAS = SAÍDAS
        # E^pv + E^-nm + E = E^d_eff + E^+nm
        # (PV + Créditos usados + Compra) = (Demanda + Exportação)
        for l in self.L:
            for t in self.T:
                self.modelo.add_constraint(
                    E_pv[(l, t)] + E_minus_nm[(l, t)] + E[(l, t)]
                    == E_d_eff[(l, t)] + E_plus_nm[(l, t)],
                    ctname=f'balanco_energia_{l}_{t}'
                )
        print(f"   ✓ (4) Balanço energético: E^pv + E^-nm + E = E^d + E^+nm: {len(self.L)*len(self.T)} restrições")
        
        # (5) Geração PV: E^pv = Σ_k P_k · sh · w_k
        for l in self.L:
            for t in self.T:
                self.modelo.add_constraint(
                    E_pv[(l, t)] == self.modelo.sum(
                        self.P_k[k] * self.sh.get((l, t), 0) * w[(l, k)]
                        for k in self.K
                    ),
                    ctname=f'geracao_pv_{l}_{t}'
                )
        print(f"   ✓ (5) Geração PV: {len(self.L)*len(self.T)} restrições")
        
        # (6) Limite de importação: E^-nm ≤ E^nm do período anterior
        for l in self.L:
            for idx, t in enumerate(self.T):
                if idx > 0:
                    t_anterior = self.T[idx - 1]
                    self.modelo.add_constraint(
                        E_minus_nm[(l, t)] <= E_nm[t_anterior],
                        ctname=f'limite_importacao_{l}_{t}'
                    )
                else:
                    # No período inicial, não há créditos disponíveis
                    self.modelo.add_constraint(
                        E_minus_nm[(l, t)] == 0,
                        ctname=f'sem_creditos_iniciais_{l}_{t}'
                    )
        print(f"   ✓ (6) Limite de importação: {len(self.L)*len(self.T)} restrições")
        
        # (7) BALANÇO ACUMULATIVO DE CRÉDITOS
        # E^nm_t = E^nm_{t-1} + Σ_l (E^+nm_{l,t} - E^-nm_{l,t})
        for idx, t in enumerate(self.T):
            if idx == 0:
                # Período inicial: créditos = exportação - importação
                self.modelo.add_constraint(
                    E_nm[t] == self.modelo.sum(
                        E_plus_nm[(l, t)] - E_minus_nm[(l, t)]
                        for l in self.L
                    ),
                    ctname=f'balanco_nm_inicial_{t}'
                )
            else:
                # Períodos seguintes: acumula créditos
                t_anterior = self.T[idx - 1]
                self.modelo.add_constraint(
                    E_nm[t] == E_nm[t_anterior] + self.modelo.sum(
                        E_plus_nm[(l, t)] - E_minus_nm[(l, t)]
                        for l in self.L
                    ),
                    ctname=f'balanco_nm_acumulativo_{t}'
                )
        print(f"   ✓ (7) Balanço acumulativo net-metering: {len(self.T)} restrições")
        
        # (8) LINEARIZAÇÃO: E^lot = max{0, E^pv - E_d_eff}
        print(f"\n   🔧 Aplicando linearização manuscrita (Big-M)...")
        
        for l in self.L:
            for t in self.T:
                # (L2) E^lot ≥ E^pv - E_d_eff
                self.modelo.add_constraint(
                    E_lot[(l, t)] >= E_pv[(l, t)] - E_d_eff[(l, t)],
                    ctname=f'lin_L2_{l}_{t}'
                )
                
                # (L3) E^lot ≤ BIG_M · x_aux
                self.modelo.add_constraint(
                    E_lot[(l, t)] <= self.BIG_M * x_aux[(l, t)],
                    ctname=f'lin_L3_{l}_{t}'
                )
                
                # (L4) E^lot ≤ (E^pv - E_d_eff) + BIG_M · (1 - x_aux)
                self.modelo.add_constraint(
                    E_lot[(l, t)] <= (E_pv[(l, t)] - E_d_eff[(l, t)]) + self.BIG_M * (1 - x_aux[(l, t)]),
                    ctname=f'lin_L4_{l}_{t}'
                )
        
        print(f"   ✓ (8-Lin) Linearização max{{0, E^pv - E_d_eff}}: {3*len(self.L)*len(self.T)} restrições")
        
        # (9) Limite de exportação: E^+nm ≤ E^lot
        for l in self.L:
            for t in self.T:
                self.modelo.add_constraint(
                    E_plus_nm[(l, t)] <= E_lot[(l, t)],
                    ctname=f'limite_exportacao_{l}_{t}'
                )
        print(f"   ✓ (9) Limite de exportação: {len(self.L)*len(self.T)} restrições")
        
        # (10) Restrição de área do carport
        for l in self.L:
            self.modelo.add_constraint(
                self.modelo.sum(
                    self.a_k[k] * w[(l, k)]
                    for k in self.K
                ) <= self.cp[l] * self.a,
                ctname=f'area_carport_{l}'
            )
        print(f"   ✓ (10) Área de carport: {len(self.L)} restrições")
        
        # (11) Carport requer estação
        for l in self.L:
            self.modelo.add_constraint(
                self.modelo.sum(w[(l, k)] for k in self.K) <= x[l],
                ctname=f'carport_requer_estacao_{l}'
            )
        print(f"   ✓ (11) Carport requer estação: {len(self.L)} restrições")
        
        total_restricoes = self.modelo.number_of_constraints
        print(f"\n✅ Total de restrições: {total_restricoes}")
        
        # Salvar variáveis
        self._vars = {
            'x': x,
            'w': w,
            'E': E,
            'E_pv': E_pv,
            'E_minus_nm': E_minus_nm,
            'E_plus_nm': E_plus_nm,
            'E_lot': E_lot,
            'E_nm': E_nm,
            'E_d_eff': E_d_eff,
            'x_aux': x_aux
        }
        
        print("\n" + "="*80)
        print(f"✅ MODELO CONSTRUÍDO (v7 - BALANÇO ENERGÉTICO CORRIGIDO)")
        print(f"📊 Variáveis: {total_vars} | Restrições: {total_restricoes}")
        print(f"🔋 Net-metering completo + Balanço corrigido")
        print("="*80)
    
    def resolver(self, time_limit: int = 600, mip_gap: float = 0.01, log_output: bool = True):
        """
        Resolve o modelo MILP
        
        Args:
            time_limit: Limite de tempo em segundos (padrão: 600)
            mip_gap: Gap de otimalidade MIP (padrão: 0.01 = 1%)
            log_output: Exibir log do solver (padrão: True)
        
        Returns:
            bool: True se solução encontrada, False caso contrário
        """
        if self.modelo is None:
            self.construir_modelo()
        
        print("\n" + "="*80)
        print("🚀 RESOLVENDO MODELO FCSA MILP COM NET-METERING")
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
        E = self._vars['E']
        E_pv = self._vars['E_pv']
        E_nm = self._vars['E_nm']
        E_plus_nm = self._vars['E_plus_nm']
        E_minus_nm = self._vars['E_minus_nm']
        
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
        
        # Custos de operação (energia comprada)
        custo_energia_anual = sum(
            self.c_e[t] * E[(l, t)].solution_value
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
            E[(l, t)].solution_value
            for l in self.estacoes_instaladas
            for t in self.T
        )
        
        self.energia_total_gerada_pv = sum(
            E_pv[(l, t)].solution_value
            for l in self.estacoes_instaladas
            for t in self.T
        )
        
        self.energia_exportada_total = sum(
            E_plus_nm[(l, t)].solution_value
            for l in self.estacoes_instaladas
            for t in self.T
        )
        
        self.energia_importada_total = sum(
            E_minus_nm[(l, t)].solution_value
            for l in self.estacoes_instaladas
            for t in self.T
        )
        
        self.creditos_finais = E_nm[self.T[-1]].solution_value if self.T else 0
    
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
            'energia_gerada_pv': getattr(self, 'energia_total_gerada_pv', 0),
            'energia_exportada': getattr(self, 'energia_exportada_total', 0),
            'energia_importada': getattr(self, 'energia_importada_total', 0),
            'creditos_finais': getattr(self, 'creditos_finais', 0)
        }
    
    def imprimir_resultados(self):
        """Imprime resultados detalhados"""
        print("\n" + "="*80)
        print("📊 RESULTADOS FINAIS - MODELO FCSA MILP COM NET-METERING")
        print("="*80)
        
        print(f"\n🏗️  INVESTIMENTO:")
        print(f"   ⚡ Estações instaladas: {len(self.estacoes_instaladas)}")
        print(f"   📍 Localizações: {self.estacoes_instaladas}")
        print(f"   ☀️  Carports PV instalados: {len(self.carports_instalados)}")
        print(f"   💰 Custo total: R$ {self.custo_investimento:,.2f}")
        
        print(f"\n💡 OPERAÇÃO:")
        print(f"   💰 Custo VP ({self.Delta_h} anos): R$ {self.custo_operacao_vp:,.2f}")
        print(f"   🔌 Energia comprada da rede: {self.energia_total_comprada:,.1f} kWh")
        print(f"   ☀️  Energia gerada PV: {self.energia_total_gerada_pv:,.1f} kWh")
        
        print(f"\n🔋 NET-METERING:")
        print(f"   📤 Energia exportada (créditos gerados): {self.energia_exportada_total:,.1f} kWh")
        print(f"   📥 Energia importada (créditos usados): {self.energia_importada_total:,.1f} kWh")
        print(f"   💾 Créditos finais acumulados: {self.creditos_finais:,.1f} kWh")
        
        # Calcular economia com net-metering
        if self.energia_exportada_total > 0:
            taxa_aproveitamento = (self.energia_importada_total / self.energia_exportada_total) * 100
            print(f"   📊 Taxa de aproveitamento: {taxa_aproveitamento:.1f}%")
        
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
                print(f"      - Benefício transporte: {beneficio:.1f}")
                print(f"      - Total: R$ {custo_est + custo_pv:,.0f}")
            else:
                print(f"   Link {l}:")
                print(f"      - Estação: R$ {custo_est:,.0f} (sem PV)")
                print(f"      - Benefício transporte: {beneficio:.1f}")
        
        print("\n" + "="*80)