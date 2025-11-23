"""
Dados sintéticos para validação do modelo FCSA MILP
Caso simplificado: 3 links, 24 períodos, 3 tipos de PV
"""

import numpy as np
import math

def obter_dados_fcsa_simplificado():
    """
    Retorna dados sintéticos simplificados para teste do modelo FCSA
    
    Caso: 3 links em área metropolitana
    - Link 0: Centro urbano (alta demanda)
    - Link 1: Zona industrial (média demanda)
    - Link 2: Área residencial (baixa demanda)
    """
    
    # Conjuntos básicos
    L = [0, 1, 2]  # 3 links
    T = list(range(24))  # 24 períodos horários (0-23h)
    K = [0, 1, 2]  # 3 tipos de carport PV
    
    # ==================== CUSTOS ====================
    
    # Custo de instalação de estação por link (R$)
    c_CS_l = {
        0: 150000,  # Centro - mais caro (infraestrutura)
        1: 120000,  # Industrial - médio
        2: 100000   # Residencial - mais barato
    }
    
    # Custo de carport PV por tipo (R$)
    c_PV_k = {
        0: 100000,  # Pequeno: 30 kW
        1: 180000,  # Médio: 60 kW
        2: 250000   # Grande: 100 kW
    }
    
    # Potência nominal dos carports PV (kW)
    P_k = {
        0: 30,
        1: 60,
        2: 100
    }
    
    # Área dos carports (m²)
    a_k = {
        0: 150,  # 30 kW → ~150 m² (5 m²/kW)
        1: 300,  # 60 kW → ~300 m²
        2: 500   # 100 kW → ~500 m²
    }
    
    # Área disponível por link (m²)
    cp_l = {
        0: 600,  # Centro - espaço limitado mas pode acomodar grande
        1: 800,  # Industrial - mais espaço
        2: 400   # Residencial - espaço médio
    }
    
    # ==================== PARÂMETROS ENERGÉTICOS ====================
    
    # Tarifa de energia por período (R$/kWh)
    # Simplificado: pico (17-21h) e fora-pico (resto)
    c_e_t = {}
    for t in T:
        if 17 <= t <= 21:
            c_e_t[t] = 0.85  # Tarifa pico
        else:
            c_e_t[t] = 0.45  # Tarifa fora-pico
    
    # Irradiação solar normalizada [0,1] - perfil típico
    # 0h-5h: sem sol, 6h-18h: sol crescente/decrescente, 19h-23h: sem sol
    def irradiacao_hora(h):
        if h < 6 or h > 18:
            return 0.0
        elif 6 <= h < 12:
            # Crescente (manhã)
            return ((h - 6) / 6) * 0.95
        elif h == 12:
            # Pico ao meio-dia
            return 1.0
        else:
            # Decrescente (tarde)
            return ((18 - h) / 6) * 0.95
    
    # sh_{l,t}: Fator de sombreamento por link e hora
    # Assumir mesmo perfil solar para todos os links (simplificação)
    sh_lt = {}
    for l in L:
        for t in T:
            sh_lt[(l, t)] = irradiacao_hora(t)
    
    # Demanda energética por link e período (kWh)
    # Baseada em número de veículos × energia por veículo
    
    # Perfil de demanda de veículos ao longo do dia
    def demanda_veiculos_hora(h, perfil='centro'):
        """Retorna número de veículos carregando na hora h"""
        if perfil == 'centro':
            # Centro: picos manhã e tarde
            if 7 <= h <= 9:
                return 15  # Pico manhã
            elif 17 <= h <= 19:
                return 20  # Pico tarde (maior)
            elif 10 <= h <= 16:
                return 8   # Durante dia
            else:
                return 2   # Noite/madrugada
        
        elif perfil == 'industrial':
            # Industrial: demanda durante horário comercial
            if 8 <= h <= 17:
                return 12
            else:
                return 3
        
        elif perfil == 'residencial':
            # Residencial: demanda noturna e fins de semana
            if 18 <= h <= 22:
                return 10
            elif 6 <= h <= 8:
                return 5
            else:
                return 2
    
    # Energia por veículo: ~30 kWh para carga rápida (assumir 50 kW × 0.6h)
    energia_por_veiculo = 30  # kWh
    
    E_d_lt = {}
    perfis = {0: 'centro', 1: 'industrial', 2: 'residencial'}
    
    for l in L:
        for t in T:
            veiculos = demanda_veiculos_hora(t, perfis[l])
            E_d_lt[(l, t)] = veiculos * energia_por_veiculo
    
    # ==================== PARÂMETROS DE TRANSPORTE ====================
    
    # Fluxo agregado de veículos por link (veículos/dia)
    rho_l = {
        0: 150,  # Centro - alto tráfego
        1: 100,  # Industrial - médio
        2: 80    # Residencial - menor
    }
    
    # Fator de benefício de transporte (adimensional)
    # Representa importância estratégica do link
    beta_l = {
        0: 1.5,  # Centro - alta prioridade
        1: 1.2,  # Industrial - média prioridade
        2: 1.0   # Residencial - prioridade normal
    }
    
    # ==================== PARÂMETROS FINANCEIROS ====================
    
    alpha = 0.10  # Taxa de juros anual: 10%
    Delta_h = 10  # Horizonte de planejamento: 10 anos
    h = 1         # Intervalo de tempo: 1 hora
    
    # ==================== PARÂMETROS DE OTIMIZAÇÃO ====================
    
    gamma = 100  # Peso dos benefícios de transporte (ajustar conforme necessário)
    a = 1.0      # Fator de área
    
    # Big-M será calculado automaticamente pelo modelo
    
    # ==================== DADOS CONSOLIDADOS ====================
    
    dados = {
        'L': L,
        'T': T,
        'K': K,
        'parametros': {
            'c_CS_l': c_CS_l,
            'c_PV_k': c_PV_k,
            'c_e_t': c_e_t,
            'P_k': P_k,
            'sh_lt': sh_lt,
            'a_k': a_k,
            'cp_l': cp_l,
            'a': a,
            'E_d_lt': E_d_lt,
            'rho_l': rho_l,
            'beta_l': beta_l,
            'alpha': alpha,
            'Delta_h': Delta_h,
            'h': h,
            'BIG_M': None,  # Calculado automaticamente
            'gamma': gamma
        }
    }
    
    return dados


def obter_dados_fcsa_medio():
    """
    Retorna dados sintéticos de médio porte para teste do modelo FCSA
    
    Caso: 5 links, 24 períodos, 3 tipos de PV
    """
    
    # Conjuntos básicos
    L = [0, 1, 2, 3, 4]  # 5 links
    T = list(range(24))  # 24 períodos horários
    K = [0, 1, 2]        # 3 tipos de carport PV
    
    # Custos de instalação (R$)
    c_CS_l = {
        0: 180000,  # Centro principal
        1: 150000,  # Centro secundário
        2: 130000,  # Zona comercial
        3: 120000,  # Zona industrial
        4: 110000   # Zona residencial
    }
    
    # Custos de carport PV (R$)
    c_PV_k = {
        0: 100000,  # 30 kW
        1: 180000,  # 60 kW
        2: 250000   # 100 kW
    }
    
    # Potências PV (kW)
    P_k = {0: 30, 1: 60, 2: 100}
    
    # Áreas (m²)
    a_k = {0: 150, 1: 300, 2: 500}
    cp_l = {0: 700, 1: 600, 2: 550, 3: 800, 4: 450}
    
    # Tarifas de energia (R$/kWh)
    c_e_t = {}
    for t in T:
        if 17 <= t <= 21:
            c_e_t[t] = 0.85
        else:
            c_e_t[t] = 0.45
    
    # Irradiação solar
    def irradiacao_hora(h):
        if h < 6 or h > 18:
            return 0.0
        elif 6 <= h < 12:
            return ((h - 6) / 6) * 0.95
        elif h == 12:
            return 1.0
        else:
            return ((18 - h) / 6) * 0.95
    
    sh_lt = {(l, t): irradiacao_hora(t) for l in L for t in T}
    
    # Demanda energética (kWh)
    perfis_demanda = {
        0: [2, 2, 1, 1, 3, 8, 15, 20, 15, 10, 8, 8, 10, 12, 15, 18, 22, 25, 20, 15, 10, 6, 4, 3],
        1: [2, 1, 1, 2, 5, 10, 18, 15, 12, 10, 9, 9, 11, 13, 14, 16, 20, 18, 12, 8, 6, 4, 3, 2],
        2: [1, 1, 1, 1, 2, 5, 10, 12, 10, 8, 7, 7, 8, 10, 12, 14, 16, 14, 10, 8, 5, 3, 2, 1],
        3: [3, 2, 2, 2, 4, 6, 8, 12, 15, 14, 14, 13, 13, 14, 15, 14, 10, 6, 4, 3, 3, 3, 3, 3],
        4: [2, 2, 1, 1, 3, 6, 8, 10, 8, 6, 5, 5, 6, 7, 8, 10, 12, 15, 18, 14, 10, 6, 4, 3]
    }
    
    E_d_lt = {(l, t): perfis_demanda[l][t] * 30 for l in L for t in T}
    
    # Parâmetros de transporte
    rho_l = {0: 200, 1: 150, 2: 120, 3: 100, 4: 90}
    beta_l = {0: 1.8, 1: 1.5, 2: 1.3, 3: 1.2, 4: 1.0}
    
    # Parâmetros financeiros
    alpha = 0.10
    Delta_h = 10
    h = 1
    gamma = 150
    a = 1.0
    
    dados = {
        'L': L,
        'T': T,
        'K': K,
        'parametros': {
            'c_CS_l': c_CS_l,
            'c_PV_k': c_PV_k,
            'c_e_t': c_e_t,
            'P_k': P_k,
            'sh_lt': sh_lt,
            'a_k': a_k,
            'cp_l': cp_l,
            'a': a,
            'E_d_lt': E_d_lt,
            'rho_l': rho_l,
            'beta_l': beta_l,
            'alpha': alpha,
            'Delta_h': Delta_h,
            'h': h,
            'BIG_M': None,
            'gamma': gamma
        }
    }
    
    return dados


def imprimir_sumario_dados(dados):
    """Imprime sumário dos dados sintéticos"""
    L = dados['L']
    T = dados['T']
    K = dados['K']
    p = dados['parametros']
    
    print("\n" + "="*80)
    print("📊 SUMÁRIO DOS DADOS SINTÉTICOS FCSA")
    print("="*80)
    
    print(f"\n🌐 DIMENSÕES DO PROBLEMA:")
    print(f"   Links (L): {len(L)}")
    print(f"   Períodos (T): {len(T)}")
    print(f"   Tipos PV (K): {len(K)}")
    print(f"   Variáveis estimadas: ~{len(L)*(1 + len(K)) + len(L)*len(T)*(7) + len(T)}")
    
    print(f"\n💰 CUSTOS:")
    print(f"   Estações: R$ {min(p['c_CS_l'].values()):,.0f} - R$ {max(p['c_CS_l'].values()):,.0f}")
    print(f"   Carports PV: R$ {min(p['c_PV_k'].values()):,.0f} - R$ {max(p['c_PV_k'].values()):,.0f}")
    print(f"   Energia pico: R$ {max(p['c_e_t'].values()):.2f}/kWh")
    print(f"   Energia fora-pico: R$ {min(p['c_e_t'].values()):.2f}/kWh")
    
    print(f"\n⚡ CAPACIDADES PV:")
    for k in K:
        print(f"   Tipo {k}: {p['P_k'][k]} kW ({p['a_k'][k]} m²) - R$ {p['c_PV_k'][k]:,.0f}")
    
    print(f"\n🔋 DEMANDA ENERGÉTICA:")
    demanda_total_dia = sum(p['E_d_lt'][(l, t)] for l in L for t in T)
    demanda_media_hora = demanda_total_dia / (len(L) * len(T))
    print(f"   Total diário: {demanda_total_dia:,.0f} kWh")
    print(f"   Média por link/hora: {demanda_media_hora:.1f} kWh")
    
    demandas_por_link = {l: sum(p['E_d_lt'][(l, t)] for t in T) for l in L}
    for l in L:
        print(f"   Link {l}: {demandas_por_link[l]:,.0f} kWh/dia")
    
    print(f"\n🚗 TRANSPORTE:")
    for l in L:
        beneficio = p['rho_l'][l] * p['beta_l'][l]
        print(f"   Link {l}: ρ={p['rho_l'][l]} veíc/dia, β={p['beta_l'][l]} → benefício={beneficio:.1f}")
    
    print(f"\n💵 PARÂMETROS FINANCEIROS:")
    print(f"   Taxa de juros (α): {p['alpha']*100:.1f}%")
    print(f"   Horizonte (Δh): {p['Delta_h']} anos")
    print(f"   Peso transporte (γ): {p['gamma']}")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    # Teste dos dados sintéticos
    print("\n🧪 TESTANDO DADOS SINTÉTICOS SIMPLIFICADOS:")
    dados_simples = obter_dados_fcsa_simplificado()
    imprimir_sumario_dados(dados_simples)
    
    print("\n\n🧪 TESTANDO DADOS SINTÉTICOS MÉDIOS:")
    dados_medio = obter_dados_fcsa_medio()
    imprimir_sumario_dados(dados_medio)