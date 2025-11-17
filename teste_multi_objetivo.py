"""
Teste do modelo multi-objetivo
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dados.dados_exemplo import obter_dados_exemplo
from modelos.modelo_multi_objetivo import ModeloEletropostosMultiObjetivo

def comparar_objetivos():
    """Compara os 3 tipos de objetivo"""
    print("🚀 COMPARANDO OBJETIVOS")
    print("="*80)
    
    # Obter dados
    dados = obter_dados_exemplo()
    
    resultados = {}
    
    # 1. Minimizar Custo
    print("\n1️⃣ MINIMIZAR CUSTO")
    modelo1 = ModeloEletropostosMultiObjetivo(
        coordenadas=dados['coordenadas'],
        demandas=dados['demandas'],
        capacidades_eletropostos=dados['capacidades_eletropostos'],
        custos_instalacao=dados['custos_instalacao'],
        distancia_maxima=dados['max_distancia'],
        tipo_objetivo='minimizar_custo'
    )
    
    if modelo1.resolver():
        resultados['minimizar_custo'] = modelo1.obter_resumo()
        modelo1.imprimir_resultados()
    
    # 2. Maximizar Cobertura
    print("\n2️⃣ MAXIMIZAR COBERTURA")
    orcamento = 300000  # Orçamento limitado
    modelo2 = ModeloEletropostosMultiObjetivo(
        coordenadas=dados['coordenadas'],
        demandas=dados['demandas'],
        capacidades_eletropostos=dados['capacidades_eletropostos'],
        custos_instalacao=dados['custos_instalacao'],
        distancia_maxima=dados['max_distancia'],
        tipo_objetivo='maximizar_cobertura',
        orcamento_maximo=orcamento
    )
    
    if modelo2.resolver():
        resultados['maximizar_cobertura'] = modelo2.obter_resumo()
        modelo2.imprimir_resultados()
    
    # 3. Multi-Objetivo
    print("\n3️⃣ MULTI-OBJETIVO")
    modelo3 = ModeloEletropostosMultiObjetivo(
        coordenadas=dados['coordenadas'],
        demandas=dados['demandas'],
        capacidades_eletropostos=dados['capacidades_eletropostos'],
        custos_instalacao=dados['custos_instalacao'],
        distancia_maxima=dados['max_distancia'],
        tipo_objetivo='multi_objetivo',
        pesos=(0.7, 0.3)  # 70% cobertura, 30% custo
    )
    
    if modelo3.resolver():
        resultados['multi_objetivo'] = modelo3.obter_resumo()
        modelo3.imprimir_resultados()
    
    # Tabela comparativa
    print(f"\n📊 TABELA COMPARATIVA")
    print("="*80)
    print(f"{'Objetivo':<20} {'Eletropostos':<12} {'Custo':<15} {'Cobertura':<10} {'Tempo':<8}")
    print("-"*80)
    
    for nome, resultado in resultados.items():
        print(f"{nome:<20} {resultado['eletropostos_instalados']:<12} "
              f"R\$ {resultado['custo_total']:>10,.0f} {resultado['cobertura_percentual']:>8.1f}% "
              f"{resultado['tempo_solucao']:>6.2f}s")
    
    print("="*80)
    
    return resultados

if __name__ == "__main__":
    comparar_objetivos()