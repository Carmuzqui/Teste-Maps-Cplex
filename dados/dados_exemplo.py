# """
# Dados de exemplo para o modelo de electropostos
# """

# def obter_dados_exemplo():
#     """
#     Retorna dados para exemplo pequeno (5 nodos)
#     """
#     # Coordenadas dos nodos (x, y) em km
#     coordenadas = [
#         (0, 0),      # Nodo 0
#         (10, 5),     # Nodo 1  
#         (15, 15),    # Nodo 2
#         (5, 20),     # Nodo 3
#         (25, 10)     # Nodo 4
#     ]
    
#     # Demanda de cada nodo (unidades de energia por día)
#     demandas = [45, 30, 60, 25, 40]  # Total: 200 unidades
    
#     # Capacidad específica de cada posible electroposto
#     capacidades_electropostos = [80, 70, 120, 60, 100]  # Capacidades variadas
    
#     # Costo específico de instalación de cada electroposto
#     custos_instalacao = [100000, 85000, 150000, 75000, 120000]  # Costos variados
    
#     # Parámetros del modelo
#     max_distancia = 25             # Máximo 25 km de distancia
    
#     return {
#         'coordenadas': coordenadas,
#         'demandas': demandas,
#         'capacidades_electropostos': capacidades_electropostos,
#         'custos_instalacao': custos_instalacao,
#         'max_distancia': max_distancia
#     }

# def obter_dados_teste_grande():
#     """
#     Retorna dados para teste grande (20 nodos)
#     """
#     import random
#     random.seed(42)  # Para resultados reproducibles
    
#     # Generar coordenadas aleatorias en una región de 50x50 km
#     coordenadas = []
#     for i in range(20):
#         x = random.uniform(0, 50)
#         y = random.uniform(0, 50)
#         coordenadas.append((x, y))
    
#     # Generar demandas aleatorias entre 20 y 80 unidades
#     demandas = []
#     for i in range(20):
#         demanda = random.uniform(20, 80)
#         demandas.append(round(demanda, 1))
    
#     # Generar capacidades aleatorias entre 60 y 200 unidades
#     capacidades_electropostos = []
#     for i in range(20):
#         capacidad = random.uniform(60, 200)
#         capacidades_electropostos.append(round(capacidad, 1))
    
#     # Generar costos proporcionales a la capacidad (500-800 por unidad de capacidad)
#     custos_instalacao = []
#     for capacidad in capacidades_electropostos:
#         costo_por_unidad = random.uniform(500, 800)
#         costo_total = capacidad * costo_por_unidad
#         custos_instalacao.append(round(costo_total, 0))
    
#     # Parámetros del modelo
#     max_distancia = 20             # Máximo 20 km de distancia
    
#     return {
#         'coordenadas': coordenadas,
#         'demandas': demandas,
#         'capacidades_electropostos': capacidades_electropostos,
#         'custos_instalacao': custos_instalacao,
#         'max_distancia': max_distancia
#     }

# def imprimir_dados(dados, nome=""):
#     """
#     Imprime os dados de forma organizada
#     """
#     print(f"\n📋 DADOS DO PROBLEMA {nome}")
#     print("="*50)
#     print(f"🏢 Número de nodos: {len(dados['coordenadas'])}")
#     print(f"📏 Distância máxima: {dados['max_distancia']} km")
    
#     demanda_total = sum(dados['demandas'])
#     capacidad_total_disponible = sum(dados['capacidades_electropostos'])
#     costo_total_maximo = sum(dados['custos_instalacao'])
    
#     print(f"📊 Demanda total: {demanda_total:.1f} unidades")
#     print(f"🔋 Capacidad total disponible: {capacidad_total_disponible:.1f} unidades")
#     print(f"💰 Costo total máximo: ${costo_total_maximo:,.0f}")
#     print(f"📈 Demanda promedio por nodo: {demanda_total/len(dados['demandas']):.1f} unidades")
#     print(f"⚡ Capacidad promedio por electroposto: {capacidad_total_disponible/len(dados['capacidades_electropostos']):.1f} unidades")
    
#     print(f"\n📍 DETALLE POR NODO:")
#     for i, (coord, demanda, capacidad, costo) in enumerate(zip(
#         dados['coordenadas'], 
#         dados['demandas'], 
#         dados['capacidades_electropostos'],
#         dados['custos_instalacao']
#     )):
#         costo_por_unidad = costo / capacidad
#         print(f"   Nodo {i}: {coord} | Demanda: {demanda} | Capacidad: {capacidad} | Costo: ${costo:,.0f} (${costo_por_unidad:.0f}/unidad)")
    
#     print("="*50)





"""
Dados de exemplo para o modelo de eletropostos
"""

def obter_dados_exemplo():
    """
    Retorna dados para exemplo pequeno (5 nós)
    """
    # Coordenadas dos nós (x, y) em km
    coordenadas = [
        (0, 0),      # Nó 0
        (10, 5),     # Nó 1  
        (15, 15),    # Nó 2
        (5, 20),     # Nó 3
        (25, 10)     # Nó 4
    ]
    
    # Demanda de cada nó (unidades de energia por dia)
    demandas = [45, 30, 60, 25, 40]  # Total: 200 unidades
    
    # Capacidade específica de cada possível eletroposto
    capacidades_eletropostos = [80, 70, 120, 60, 100]  # Capacidades variadas
    
    # Custo específico de instalação de cada eletroposto
    custos_instalacao = [100000, 85000, 150000, 75000, 120000]  # Custos variados
    
    # Parâmetros do modelo
    max_distancia = 25             # Máximo 25 km de distância
    
    return {
        'coordenadas': coordenadas,
        'demandas': demandas,
        'capacidades_eletropostos': capacidades_eletropostos,
        'custos_instalacao': custos_instalacao,
        'max_distancia': max_distancia
    }

def obter_dados_teste_grande():
    """
    Retorna dados para teste grande (20 nós)
    """
    import random
    random.seed(42)  # Para resultados reproduzíveis
    
    # Gerar coordenadas aleatórias em uma região de 50x50 km
    coordenadas = []
    for i in range(20):
        x = random.uniform(0, 50)
        y = random.uniform(0, 50)
        coordenadas.append((x, y))
    
    # Gerar demandas aleatórias entre 20 e 80 unidades
    demandas = []
    for i in range(20):
        demanda = random.uniform(20, 80)
        demandas.append(round(demanda, 1))
    
    # Gerar capacidades aleatórias entre 60 e 200 unidades
    capacidades_eletropostos = []
    for i in range(20):
        capacidade = random.uniform(60, 200)
        capacidades_eletropostos.append(round(capacidade, 1))
    
    # Gerar custos proporcionais à capacidade (500-800 por unidade de capacidade)
    custos_instalacao = []
    for capacidade in capacidades_eletropostos:
        custo_por_unidade = random.uniform(500, 800)
        custo_total = capacidade * custo_por_unidade
        custos_instalacao.append(round(custo_total, 0))
    
    # Parâmetros do modelo
    max_distancia = 20             # Máximo 20 km de distância
    
    return {
        'coordenadas': coordenadas,
        'demandas': demandas,
        'capacidades_eletropostos': capacidades_eletropostos,
        'custos_instalacao': custos_instalacao,
        'max_distancia': max_distancia
    }

def imprimir_dados(dados, nome=""):
    """
    Imprime os dados de forma organizada
    """
    print(f"\n📋 DADOS DO PROBLEMA {nome}")
    print("="*50)
    print(f"🏢 Número de nós: {len(dados['coordenadas'])}")
    print(f"📏 Distância máxima: {dados['max_distancia']} km")
    
    demanda_total = sum(dados['demandas'])
    capacidade_total_disponivel = sum(dados['capacidades_eletropostos'])
    custo_total_maximo = sum(dados['custos_instalacao'])
    
    print(f"📊 Demanda total: {demanda_total:.1f} unidades")
    print(f"🔋 Capacidade total disponível: {capacidade_total_disponivel:.1f} unidades")
    print(f"💰 Custo total máximo: R$ {custo_total_maximo:,.0f}")
    print(f"📈 Demanda média por nó: {demanda_total/len(dados['demandas']):.1f} unidades")
    print(f"⚡ Capacidade média por eletroposto: {capacidade_total_disponivel/len(dados['capacidades_eletropostos']):.1f} unidades")
    
    print(f"\n📍 DETALHE POR NÓ:")
    for i, (coord, demanda, capacidade, custo) in enumerate(zip(
        dados['coordenadas'], 
        dados['demandas'], 
        dados['capacidades_eletropostos'],
        dados['custos_instalacao']
    )):
        custo_por_unidade = custo / capacidade
        print(f"   Nó {i}: {coord} | Demanda: {demanda} | Capacidade: {capacidade} | Custo: R$ {custo:,.0f} (R$ {custo_por_unidade:.0f}/unidade)")
    
    print("="*50)