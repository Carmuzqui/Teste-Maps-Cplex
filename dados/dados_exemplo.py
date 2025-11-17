# """
# Dados de exemplo para teste do modelo de otimização de eletropostos
# """

# def obter_dados_exemplo():
#     """
#     Retorna dados sintéticos para teste do modelo
#     """
    
#     # Custos de instalação por eletroposto (em R\$)
#     custos_fixos = [15000, 18000, 12000, 20000, 16000]
    
#     # Custo variável por capacidade (R\$ por nó atendível)
#     custo_por_capacidade = 2000
    
#     # Demanda por nó (número de veículos/dia)
#     demanda_nos = [10, 15, 8, 12, 20, 5, 18, 9, 14, 11]
    
#     # Matriz de conectividade (eletroposto i pode atender nó j)
#     # 1 = pode atender, 0 = não pode atender
#     conectividade = [
#         [1, 1, 1, 0, 0, 0, 0, 0, 0, 0],  # Eletroposto 0 pode atender nós 0,1,2
#         [0, 1, 1, 1, 1, 0, 0, 0, 0, 0],  # Eletroposto 1 pode atender nós 1,2,3,4
#         [0, 0, 0, 1, 1, 1, 1, 0, 0, 0],  # Eletroposto 2 pode atender nós 3,4,5,6
#         [0, 0, 0, 0, 0, 1, 1, 1, 1, 0],  # Eletroposto 3 pode atender nós 5,6,7,8
#         [0, 0, 0, 0, 0, 0, 0, 1, 1, 1],  # Eletroposto 4 pode atender nós 7,8,9
#     ]
    
#     # Capacidade máxima por eletroposto (número de nós que pode atender)
#     capacidades_max = [4, 4, 4, 4, 4]
    
#     # Parâmetros do modelo
#     parametros = {
#         'orcamento_total': 50000,  # R\$
#         'peso_cobertura': 0.7,     # w1
#         'peso_custo': 0.3,         # w2
#     }
    
#     # Nomes para identificação
#     nomes_eletropostos = [f"Eletroposto_{i}" for i in range(len(custos_fixos))]
#     nomes_nos = [f"No_Demanda_{i}" for i in range(len(demanda_nos))]
    
#     return {
#         'custos_fixos': custos_fixos,
#         'custo_por_capacidade': custo_por_capacidade,
#         'demanda_nos': demanda_nos,
#         'conectividade': conectividade,
#         'capacidades_max': capacidades_max,
#         'parametros': parametros,
#         'nomes_eletropostos': nomes_eletropostos,
#         'nomes_nos': nomes_nos
#     }

# def obter_dados_teste_grande():
#     """
#     Retorna dados para teste de performance com problema maior
#     """
#     import random
#     random.seed(42)  # Para resultados reproduzíveis
    
#     num_eletropostos = 20
#     num_nos = 50
    
#     # Custos aleatórios
#     custos_fixos = [random.randint(10000, 25000) for _ in range(num_eletropostos)]
#     custo_por_capacidade = 1500
    
#     # Demanda aleatória
#     demanda_nos = [random.randint(5, 25) for _ in range(num_nos)]
    
#     # Matriz de conectividade esparsa (cada eletroposto atende ~30% dos nós)
#     conectividade = []
#     for i in range(num_eletropostos):
#         linha = [1 if random.random() < 0.3 else 0 for _ in range(num_nos)]
#         # Garantir que cada eletroposto atende pelo menos 3 nós
#         if sum(linha) < 3:
#             indices = random.sample(range(num_nos), 3)
#             for idx in indices:
#                 linha[idx] = 1
#         conectividade.append(linha)
    
#     # Capacidades
#     capacidades_max = [random.randint(8, 15) for _ in range(num_eletropostos)]
    
#     parametros = {
#         'orcamento_total': 200000,
#         'peso_cobertura': 0.7,
#         'peso_custo': 0.3,
#     }
    
#     nomes_eletropostos = [f"Eletroposto_{i}" for i in range(num_eletropostos)]
#     nomes_nos = [f"No_Demanda_{i}" for i in range(num_nos)]
    
#     return {
#         'custos_fixos': custos_fixos,
#         'custo_por_capacidade': custo_por_capacidade,
#         'demanda_nos': demanda_nos,
#         'conectividade': conectividade,
#         'capacidades_max': capacidades_max,
#         'parametros': parametros,
#         'nomes_eletropostos': nomes_eletropostos,
#         'nomes_nos': nomes_nos
#     }









"""
Dados de exemplo para o modelo de electropostos
"""

def obter_dados_exemplo():
    """
    Retorna dados para exemplo pequeno (5 nodos)
    """
    # Coordenadas dos nodos (x, y) em km
    coordenadas = [
        (0, 0),      # Nodo 0
        (10, 5),     # Nodo 1  
        (15, 15),    # Nodo 2
        (5, 20),     # Nodo 3
        (25, 10)     # Nodo 4
    ]
    
    # Demanda de cada nodo (unidades de energia por día)
    demandas = [45, 30, 60, 25, 40]  # Total: 200 unidades
    
    # Capacidad específica de cada posible electroposto
    capacidades_electropostos = [80, 70, 120, 60, 100]  # Capacidades variadas
    
    # Costo específico de instalación de cada electroposto
    custos_instalacao = [100000, 85000, 150000, 75000, 120000]  # Costos variados
    
    # Parámetros del modelo
    max_distancia = 25             # Máximo 25 km de distancia
    
    return {
        'coordenadas': coordenadas,
        'demandas': demandas,
        'capacidades_electropostos': capacidades_electropostos,
        'custos_instalacao': custos_instalacao,
        'max_distancia': max_distancia
    }

def obter_dados_teste_grande():
    """
    Retorna dados para teste grande (20 nodos)
    """
    import random
    random.seed(42)  # Para resultados reproducibles
    
    # Generar coordenadas aleatorias en una región de 50x50 km
    coordenadas = []
    for i in range(20):
        x = random.uniform(0, 50)
        y = random.uniform(0, 50)
        coordenadas.append((x, y))
    
    # Generar demandas aleatorias entre 20 y 80 unidades
    demandas = []
    for i in range(20):
        demanda = random.uniform(20, 80)
        demandas.append(round(demanda, 1))
    
    # Generar capacidades aleatorias entre 60 y 200 unidades
    capacidades_electropostos = []
    for i in range(20):
        capacidad = random.uniform(60, 200)
        capacidades_electropostos.append(round(capacidad, 1))
    
    # Generar costos proporcionales a la capacidad (500-800 por unidad de capacidad)
    custos_instalacao = []
    for capacidad in capacidades_electropostos:
        costo_por_unidad = random.uniform(500, 800)
        costo_total = capacidad * costo_por_unidad
        custos_instalacao.append(round(costo_total, 0))
    
    # Parámetros del modelo
    max_distancia = 20             # Máximo 20 km de distancia
    
    return {
        'coordenadas': coordenadas,
        'demandas': demandas,
        'capacidades_electropostos': capacidades_electropostos,
        'custos_instalacao': custos_instalacao,
        'max_distancia': max_distancia
    }

def imprimir_dados(dados, nome=""):
    """
    Imprime os dados de forma organizada
    """
    print(f"\n📋 DADOS DO PROBLEMA {nome}")
    print("="*50)
    print(f"🏢 Número de nodos: {len(dados['coordenadas'])}")
    print(f"📏 Distância máxima: {dados['max_distancia']} km")
    
    demanda_total = sum(dados['demandas'])
    capacidad_total_disponible = sum(dados['capacidades_electropostos'])
    costo_total_maximo = sum(dados['custos_instalacao'])
    
    print(f"📊 Demanda total: {demanda_total:.1f} unidades")
    print(f"🔋 Capacidad total disponible: {capacidad_total_disponible:.1f} unidades")
    print(f"💰 Costo total máximo: ${costo_total_maximo:,.0f}")
    print(f"📈 Demanda promedio por nodo: {demanda_total/len(dados['demandas']):.1f} unidades")
    print(f"⚡ Capacidad promedio por electroposto: {capacidad_total_disponible/len(dados['capacidades_electropostos']):.1f} unidades")
    
    print(f"\n📍 DETALLE POR NODO:")
    for i, (coord, demanda, capacidad, costo) in enumerate(zip(
        dados['coordenadas'], 
        dados['demandas'], 
        dados['capacidades_electropostos'],
        dados['custos_instalacao']
    )):
        costo_por_unidad = costo / capacidad
        print(f"   Nodo {i}: {coord} | Demanda: {demanda} | Capacidad: {capacidad} | Costo: ${costo:,.0f} (${costo_por_unidad:.0f}/unidad)")
    
    print("="*50)