"""
Dados de exemplo para teste do modelo de otimização de eletropostos
"""

def obter_dados_exemplo():
    """
    Retorna dados sintéticos para teste do modelo
    """
    
    # Custos de instalação por eletroposto (em R\$)
    custos_fixos = [15000, 18000, 12000, 20000, 16000]
    
    # Custo variável por capacidade (R\$ por nó atendível)
    custo_por_capacidade = 2000
    
    # Demanda por nó (número de veículos/dia)
    demanda_nos = [10, 15, 8, 12, 20, 5, 18, 9, 14, 11]
    
    # Matriz de conectividade (eletroposto i pode atender nó j)
    # 1 = pode atender, 0 = não pode atender
    conectividade = [
        [1, 1, 1, 0, 0, 0, 0, 0, 0, 0],  # Eletroposto 0 pode atender nós 0,1,2
        [0, 1, 1, 1, 1, 0, 0, 0, 0, 0],  # Eletroposto 1 pode atender nós 1,2,3,4
        [0, 0, 0, 1, 1, 1, 1, 0, 0, 0],  # Eletroposto 2 pode atender nós 3,4,5,6
        [0, 0, 0, 0, 0, 1, 1, 1, 1, 0],  # Eletroposto 3 pode atender nós 5,6,7,8
        [0, 0, 0, 0, 0, 0, 0, 1, 1, 1],  # Eletroposto 4 pode atender nós 7,8,9
    ]
    
    # Capacidade máxima por eletroposto (número de nós que pode atender)
    capacidades_max = [4, 4, 4, 4, 4]
    
    # Parâmetros do modelo
    parametros = {
        'orcamento_total': 50000,  # R\$
        'peso_cobertura': 0.7,     # w1
        'peso_custo': 0.3,         # w2
    }
    
    # Nomes para identificação
    nomes_eletropostos = [f"Eletroposto_{i}" for i in range(len(custos_fixos))]
    nomes_nos = [f"No_Demanda_{i}" for i in range(len(demanda_nos))]
    
    return {
        'custos_fixos': custos_fixos,
        'custo_por_capacidade': custo_por_capacidade,
        'demanda_nos': demanda_nos,
        'conectividade': conectividade,
        'capacidades_max': capacidades_max,
        'parametros': parametros,
        'nomes_eletropostos': nomes_eletropostos,
        'nomes_nos': nomes_nos
    }

def obter_dados_teste_grande():
    """
    Retorna dados para teste de performance com problema maior
    """
    import random
    random.seed(42)  # Para resultados reproduzíveis
    
    num_eletropostos = 20
    num_nos = 50
    
    # Custos aleatórios
    custos_fixos = [random.randint(10000, 25000) for _ in range(num_eletropostos)]
    custo_por_capacidade = 1500
    
    # Demanda aleatória
    demanda_nos = [random.randint(5, 25) for _ in range(num_nos)]
    
    # Matriz de conectividade esparsa (cada eletroposto atende ~30% dos nós)
    conectividade = []
    for i in range(num_eletropostos):
        linha = [1 if random.random() < 0.3 else 0 for _ in range(num_nos)]
        # Garantir que cada eletroposto atende pelo menos 3 nós
        if sum(linha) < 3:
            indices = random.sample(range(num_nos), 3)
            for idx in indices:
                linha[idx] = 1
        conectividade.append(linha)
    
    # Capacidades
    capacidades_max = [random.randint(8, 15) for _ in range(num_eletropostos)]
    
    parametros = {
        'orcamento_total': 200000,
        'peso_cobertura': 0.7,
        'peso_custo': 0.3,
    }
    
    nomes_eletropostos = [f"Eletroposto_{i}" for i in range(num_eletropostos)]
    nomes_nos = [f"No_Demanda_{i}" for i in range(num_nos)]
    
    return {
        'custos_fixos': custos_fixos,
        'custo_por_capacidade': custo_por_capacidade,
        'demanda_nos': demanda_nos,
        'conectividade': conectividade,
        'capacidades_max': capacidades_max,
        'parametros': parametros,
        'nomes_eletropostos': nomes_eletropostos,
        'nomes_nos': nomes_nos
    }