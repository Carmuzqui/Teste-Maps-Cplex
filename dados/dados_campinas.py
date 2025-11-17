"""
Dados reais da região metropolitana de Campinas para eletropostos
"""

def obter_dados_campinas():
    """
    Retorna dados reais de Campinas com coordenadas geográficas
    Pontos estratégicos da região metropolitana
    """
    
    # Coordenadas (latitude, longitude) de pontos estratégicos em Campinas
    coordenadas = [
        (-22.9056, -47.0608, "Centro de Campinas"),           # Centro histórico
        (-22.8708, -47.0331, "Unicamp"),                      # Universidade
        (-22.9167, -47.0667, "Shopping Iguatemi"),            # Shopping
        (-22.8847, -47.0364, "Aeroporto de Viracopos"),       # Aeroporto
        (-22.9275, -47.0486, "Terminal Rodoviário"),          # Rodoviária
        (-22.8583, -47.0792, "Barão Geraldo"),                # Bairro residencial
        (-22.9444, -47.0889, "Shopping Parque Dom Pedro"),    # Shopping
        (-22.9056, -47.0264, "PUC Campinas"),                 # Universidade
        (-22.8889, -47.1167, "Hortolândia Centro"),           # Cidade vizinha
        (-22.8167, -47.0667, "Paulínia Centro"),              # Cidade vizinha
        (-22.9833, -47.0833, "Sumaré Centro"),                # Cidade vizinha
        (-22.7333, -47.1167, "Jaguariúna Centro"),            # Cidade vizinha
        (-22.9667, -47.1333, "Nova Odessa"),                  # Cidade vizinha
        (-22.8333, -47.1833, "Americana Centro"),             # Cidade vizinha
        (-22.7167, -47.0333, "Pedreira"),                     # Cidade vizinha
    ]
    
    # Demandas estimadas baseadas na população e atividade econômica (veículos elétricos por dia)
    demandas = [
        120,  # Centro - alta densidade comercial
        80,   # Unicamp - universidade, movimento estudantil
        150,  # Shopping Iguatemi - alto fluxo
        200,  # Aeroporto - muito alto fluxo
        90,   # Rodoviária - transporte
        70,   # Barão Geraldo - residencial
        140,  # Shopping Dom Pedro - alto fluxo
        60,   # PUC - universidade menor
        85,   # Hortolândia - cidade média
        95,   # Paulínia - industrial
        75,   # Sumaré - residencial
        50,   # Jaguariúna - menor
        45,   # Nova Odessa - menor
        110,  # Americana - industrial
        35,   # Pedreira - menor
    ]
    
    # Capacidades específicas baseadas no potencial de cada localização
    capacidades_eletropostos = [
        200,  # Centro - grande potencial
        150,  # Unicamp - médio-grande
        250,  # Shopping Iguatemi - muito grande
        300,  # Aeroporto - máximo potencial
        180,  # Rodoviária - grande
        120,  # Barão Geraldo - médio
        240,  # Shopping Dom Pedro - muito grande
        100,  # PUC - médio
        160,  # Hortolândia - médio-grande
        180,  # Paulínia - grande (industrial)
        140,  # Sumaré - médio
        90,   # Jaguariúna - médio-pequeno
        80,   # Nova Odessa - médio-pequeno
        190,  # Americana - grande (industrial)
        70,   # Pedreira - pequeno
    ]
    
    # Custos de instalação baseados na complexidade da localização
    custos_instalacao = [
        180000,  # Centro - alto (infraestrutura urbana complexa)
        140000,  # Unicamp - médio (terreno disponível)
        200000,  # Shopping Iguatemi - muito alto (localização premium)
        250000,  # Aeroporto - máximo (regulamentações especiais)
        170000,  # Rodoviária - alto (infraestrutura de transporte)
        120000,  # Barão Geraldo - médio (residencial)
        210000,  # Shopping Dom Pedro - muito alto (premium)
        110000,  # PUC - médio-baixo (parceria educacional)
        130000,  # Hortolândia - médio
        160000,  # Paulínia - médio-alto (zona industrial)
        125000,  # Sumaré - médio
        100000,  # Jaguariúna - baixo (cidade menor)
        95000,   # Nova Odessa - baixo
        150000,  # Americana - médio-alto (industrial)
        85000,   # Pedreira - baixo
    ]
    
    # Parâmetros específicos para Campinas
    distancia_maxima = 15  # 15 km - região metropolitana compacta
    
    return {
        'coordenadas': coordenadas,
        'demandas': demandas,
        'capacidades_eletropostos': capacidades_eletropostos,
        'custos_instalacao': custos_instalacao,
        'max_distancia': distancia_maxima
    }

def obter_coordenadas_simples():
    """
    Retorna apenas as coordenadas (lat, lon) sem nomes para cálculos
    """
    dados = obter_dados_campinas()
    return [(lat, lon) for lat, lon, _ in dados['coordenadas']]

def obter_nomes_locais():
    """
    Retorna apenas os nomes dos locais
    """
    dados = obter_dados_campinas()
    return [nome for _, _, nome in dados['coordenadas']]

def calcular_distancia_haversine(coord1, coord2):
    """
    Calcula distância entre duas coordenadas geográficas usando fórmula de Haversine
    
    Args:
        coord1: (lat1, lon1)
        coord2: (lat2, lon2)
    
    Returns:
        Distância em quilômetros
    """
    import math
    
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    
    # Converter para radianos
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Fórmula de Haversine
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Raio da Terra em km
    r = 6371
    
    return c * r

def imprimir_dados_campinas():
    """
    Imprime informações sobre os dados de Campinas
    """
    dados = obter_dados_campinas()
    
    print("\n🏙️ DADOS DA REGIÃO METROPOLITANA DE CAMPINAS")
    print("="*60)
    print(f"📍 Número de localizações: {len(dados['coordenadas'])}")
    print(f"📏 Distância máxima de atendimento: {dados['max_distancia']} km")
    
    demanda_total = sum(dados['demandas'])
    capacidade_total = sum(dados['capacidades_eletropostos'])
    custo_total_max = sum(dados['custos_instalacao'])
    
    print(f"📊 Demanda total estimada: {demanda_total} veículos/dia")
    print(f"🔋 Capacidade total disponível: {capacidade_total} veículos/dia")
    print(f"💰 Investimento total máximo: R$ {custo_total_max:,.0f}")
    
    print(f"\n📍 LOCALIZAÇÕES ESTRATÉGICAS:")
    print("-"*60)
    
    for i, ((lat, lon, nome), demanda, capacidade, custo) in enumerate(zip(
        dados['coordenadas'], 
        dados['demandas'], 
        dados['capacidades_eletropostos'],
        dados['custos_instalacao']
    )):
        eficiencia = custo / capacidade
        print(f"{i:2d}. {nome:<25} | Demanda: {demanda:3d} | Cap: {capacidade:3d} | "
              f"Custo: R$ {custo:>7,.0f} | R$/Cap: {eficiencia:>5.0f}")
    
    print("="*60)
    
    # Estatísticas por tipo de localização
    print(f"\n📈 ANÁLISE POR TIPO:")
    
    tipos = {
        'Shopping/Comercial': [2, 6],  # Iguatemi, Dom Pedro
        'Transporte': [3, 4],          # Aeroporto, Rodoviária
        'Educacional': [1, 7],         # Unicamp, PUC
        'Centros Urbanos': [0, 8, 9, 10, 12, 13, 14],  # Centros das cidades
        'Residencial': [5, 11]         # Barão Geraldo, Jaguariúna
    }
    
    for tipo, indices in tipos.items():
        demanda_tipo = sum(dados['demandas'][i] for i in indices)
        capacidade_tipo = sum(dados['capacidades_eletropostos'][i] for i in indices)
        custo_tipo = sum(dados['custos_instalacao'][i] for i in indices)
        
        print(f"   {tipo:<18}: {len(indices)} locais | "
              f"Demanda: {demanda_tipo:3d} | Capacidade: {capacidade_tipo:3d} | "
              f"Custo: R$ {custo_tipo:>8,.0f}")

if __name__ == "__main__":
    imprimir_dados_campinas()