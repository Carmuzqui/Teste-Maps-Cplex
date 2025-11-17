"""
Teste do modelo com dados reais de Campinas
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dados.dados_campinas import obter_dados_campinas, imprimir_dados_campinas, obter_coordenadas_simples
from modelos.modelo_multi_objetivo import ModeloEletropostosMultiObjetivo

def teste_campinas_completo():
    """
    Testa o modelo com dados reais de Campinas
    """
    print("🏙️ TESTE COM DADOS REAIS DE CAMPINAS")
    print("="*80)
    
    # Mostrar dados
    imprimir_dados_campinas()
    
    # Obter dados
    dados = obter_dados_campinas()
    
    # Converter coordenadas geográficas para coordenadas simples para o modelo
    coordenadas_simples = obter_coordenadas_simples()
    
    print(f"\n🧪 EXECUTANDO OTIMIZAÇÃO...")
    
    resultados = {}
    
    # 1. Minimizar Custo
    print("\n1️⃣ ESTRATÉGIA: MINIMIZAR CUSTO")
    modelo1 = ModeloEletropostosMultiObjetivo(
        coordenadas=coordenadas_simples,
        demandas=dados['demandas'],
        capacidades_eletropostos=dados['capacidades_eletropostos'],
        custos_instalacao=dados['custos_instalacao'],
        distancia_maxima=dados['max_distancia'],
        tipo_objetivo='minimizar_custo'
    )
    
    if modelo1.resolver():
        resultados['minimizar_custo'] = modelo1.obter_resumo()
        print(f"✅ Solução encontrada!")
        imprimir_resultados_campinas(modelo1, dados)
    else:
        print("❌ Não foi possível encontrar solução")
    
    # 2. Maximizar Cobertura
    print("\n2️⃣ ESTRATÉGIA: MAXIMIZAR COBERTURA")
    orcamento_limitado = 800000  # R\$ 800.000 de orçamento
    modelo2 = ModeloEletropostosMultiObjetivo(
        coordenadas=coordenadas_simples,
        demandas=dados['demandas'],
        capacidades_eletropostos=dados['capacidades_eletropostos'],
        custos_instalacao=dados['custos_instalacao'],
        distancia_maxima=dados['max_distancia'],
        tipo_objetivo='maximizar_cobertura',
        orcamento_maximo=orcamento_limitado
    )
    
    print(f"💰 Orçamento disponível: R\$ {orcamento_limitado:,.0f}")
    
    if modelo2.resolver():
        resultados['maximizar_cobertura'] = modelo2.obter_resumo()
        print(f"✅ Solução encontrada!")
        imprimir_resultados_campinas(modelo2, dados)
    else:
        print("❌ Não foi possível encontrar solução")
    
    # 3. Multi-Objetivo
    print("\n3️⃣ ESTRATÉGIA: MULTI-OBJETIVO (70% cobertura, 30% custo)")
    modelo3 = ModeloEletropostosMultiObjetivo(
        coordenadas=coordenadas_simples,
        demandas=dados['demandas'],
        capacidades_eletropostos=dados['capacidades_eletropostos'],
        custos_instalacao=dados['custos_instalacao'],
        distancia_maxima=dados['max_distancia'],
        tipo_objetivo='multi_objetivo',
        pesos=(0.7, 0.3)
    )
    
    if modelo3.resolver():
        resultados['multi_objetivo'] = modelo3.obter_resumo()
        print(f"✅ Solução encontrada!")
        imprimir_resultados_campinas(modelo3, dados)
    else:
        print("❌ Não foi possível encontrar solução")
    
    # Comparação final
    if resultados:
        imprimir_comparacao_estrategias(resultados, dados)
    
    return resultados

def imprimir_resultados_campinas(modelo, dados):
    """
    Imprime resultados específicos para Campinas com nomes dos locais
    """
    nomes = [nome for _, _, nome in dados['coordenadas']]
    
    print(f"\n📍 ELETROPOSTOS SELECIONADOS:")
    for j in modelo.eletropostos_instalados:
        nos_atendidos = modelo.atribuicoes[j]
        demanda_atendida = sum(modelo.demandas[i] for i in nos_atendidos)
        utilizacao = (demanda_atendida / modelo.capacidades[j]) * 100
        
        print(f"   🔌 {nomes[j]}")
        print(f"      • Capacidade: {modelo.capacidades[j]} veículos/dia")
        print(f"      • Demanda atendida: {demanda_atendida:.0f} veículos/dia")
        print(f"      • Utilização: {utilizacao:.1f}%")
        print(f"      • Custo: R\$ {modelo.custos_instalacao[j]:,.0f}")
        
        # Mostrar quais locais atende
        locais_atendidos = [nomes[i] for i in nos_atendidos]
        print(f"      • Atende: {', '.join(locais_atendidos[:3])}" + 
              (f" + {len(locais_atendidos)-3} outros" if len(locais_atendidos) > 3 else ""))
        print()

def imprimir_comparacao_estrategias(resultados, dados):
    """
    Imprime comparação entre as estratégias
    """
    print(f"\n📊 COMPARAÇÃO DE ESTRATÉGIAS - CAMPINAS")
    print("="*90)
    print(f"{'Estratégia':<20} {'Eletropostos':<12} {'Custo Total':<15} {'Cobertura':<12} {'Eficiência':<10}")
    print("-"*90)
    
    for nome, resultado in resultados.items():
        eficiencia = resultado['cobertura_total'] / resultado['custo_total'] * 1000
        nome_display = nome.replace('_', ' ').title()
        
        print(f"{nome_display:<20} {resultado['eletropostos_instalados']:<12} "
              f"R\$ {resultado['custo_total']:>10,.0f} "
              f"{resultado['cobertura_percentual']:>8.1f}% "
              f"{eficiencia:>8.2f}")
    
    print("-"*90)
    print("* Eficiência = Cobertura / Custo × 1000")
    print("="*90)

if __name__ == "__main__":
    teste_campinas_completo()