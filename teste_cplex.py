"""
Teste principal do modelo de otimização de eletropostos
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dados.dados_exemplo import obter_dados_exemplo, obter_dados_teste_grande
from modelos.modelo_basico import ModeloEletropostos

def teste_basico():
    """
    Executa teste com problema pequeno
    """
    print("🚀 INICIANDO TESTE BÁSICO")
    print("-" * 40)
    
    # Carregar dados
    dados = obter_dados_exemplo()
    
    # Criar e resolver modelo
    modelo = ModeloEletropostos(dados)
    
    print("📝 Criando modelo...")
    modelo.criar_modelo()
    
    print("⚡ Resolvendo otimização...")
    sucesso = modelo.resolver(limite_tempo=30, verbose=True)
    
    if sucesso:
        print("✅ Solução encontrada!")
        resultados = modelo.obter_resultados()
        modelo.imprimir_relatorio(resultados)
        return True
    else:
        print("❌ Falha na otimização")
        return False

def teste_performance():
    """
    Executa teste com problema maior para avaliar performance
    """
    print("\n\n🚀 INICIANDO TESTE DE PERFORMANCE")
    print("-" * 40)
    
    # Carregar dados maiores
    dados = obter_dados_teste_grande()
    
    print(f"📊 Problema: {len(dados['custos_fixos'])} eletropostos candidatos, "
          f"{len(dados['demanda_nos'])} nós de demanda")
    
    # Criar e resolver modelo
    modelo = ModeloEletropostos(dados)
    
    print("📝 Criando modelo...")
    modelo.criar_modelo()
    
    print("⚡ Resolvendo otimização...")
    sucesso = modelo.resolver(limite_tempo=120, verbose=False)
    
    if sucesso:
        print("✅ Solução encontrada!")
        resultados = modelo.obter_resultados()
        modelo.imprimir_relatorio(resultados)
        return True
    else:
        print("❌ Falha na otimização")
        return False

def verificar_cplex():
    """
    Verifica se CPLEX está funcionando corretamente
    """
    try:
        import docplex
        from docplex.mp.model import Model
        
        print("✅ DOcplex importado com sucesso")
        print(f"   Versão: {docplex.__version__}")
        
        # Teste simples
        m = Model(name="teste")
        x = m.continuous_var(name="x")
        m.maximize(x)
        m.add_constraint(x <= 10)
        
        sol = m.solve()
        if sol and abs(sol.objective_value - 10) < 1e-6:
            print("✅ CPLEX funcionando corretamente")
            return True
        else:
            print("❌ Problema na execução do CPLEX")
            return False
            
    except ImportError as e:
        print(f"❌ Erro ao importar DOcplex: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro no teste CPLEX: {e}")
        return False

if __name__ == "__main__":
    print("🔧 TESTE DE INSTALAÇÃO E PERFORMANCE CPLEX")
    print("=" * 50)
    
    # Verificar instalação
    if not verificar_cplex():
        print("\n❌ CPLEX não está funcionando corretamente. Verifique a instalação.")
        sys.exit(1)
    
    # Teste básico
    if not teste_basico():
        print("\n❌ Falha no teste básico")
        sys.exit(1)
    
    # Teste de performance
    resposta = input("\n❓ Deseja executar teste de performance com problema maior? (s/n): ")
    if resposta.lower() in ['s', 'sim', 'y', 'yes']:
        teste_performance()
    
    print("\n🎉 TODOS OS TESTES CONCLUÍDOS COM SUCESSO!")
    print("✅ CPLEX está pronto para problemas maiores")