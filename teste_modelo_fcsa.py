# """
# Script de validação do modelo FCSA MILP
# Testa o modelo com dados sintéticos de complexidade crescente
# """

# import sys
# import os

# # Adicionar diretório raiz ao path
# sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# from modelos.modelo_Caio import ModeloFCSA_MILP
# from dados.dados_fcsa_sintetico import (
#     obter_dados_fcsa_simplificado,
#     obter_dados_fcsa_medio,
#     imprimir_sumario_dados
# )

# def teste_modelo_simplificado():
#     """Teste com caso simplificado (3 links)"""
#     print("\n" + "="*80)
#     print("🧪 TESTE 1: MODELO SIMPLIFICADO (3 links, 24 períodos)")
#     print("="*80)
    
#     # Carregar dados
#     dados = obter_dados_fcsa_simplificado()
#     imprimir_sumario_dados(dados)
    
#     # Criar e resolver modelo
#     modelo = ModeloFCSA_MILP(
#         L=dados['L'],
#         T=dados['T'],
#         K=dados['K'],
#         parametros=dados['parametros']
#     )
    
#     # Construir e resolver
#     modelo.construir_modelo()
#     sucesso = modelo.resolver(time_limit=300, mip_gap=0.02, log_output=True)
    
#     if sucesso:
#         modelo.imprimir_resultados()
#         return modelo
#     else:
#         print("\n❌ Teste falhou: modelo infactível")
#         return None


# def teste_modelo_medio():
#     """Teste com caso médio (5 links)"""
#     print("\n" + "="*80)
#     print("🧪 TESTE 2: MODELO MÉDIO (5 links, 24 períodos)")
#     print("="*80)
    
#     # Carregar dados
#     dados = obter_dados_fcsa_medio()
#     imprimir_sumario_dados(dados)
    
#     # Criar e resolver modelo
#     modelo = ModeloFCSA_MILP(
#         L=dados['L'],
#         T=dados['T'],
#         K=dados['K'],
#         parametros=dados['parametros']
#     )
    
#     # Construir e resolver
#     modelo.construir_modelo()
#     sucesso = modelo.resolver(time_limit=600, mip_gap=0.02, log_output=True)
    
#     if sucesso:
#         modelo.imprimir_resultados()
#         return modelo
#     else:
#         print("\n❌ Teste falhou: modelo infactível")
#         return None


# def teste_sensibilidade_gamma():
#     """Teste de sensibilidade ao parâmetro gamma"""
#     print("\n" + "="*80)
#     print("🧪 TESTE 3: ANÁLISE DE SENSIBILIDADE - PARÂMETRO γ")
#     print("="*80)
    
#     dados = obter_dados_fcsa_simplificado()
    
#     # Testar diferentes valores de gamma
#     gammas = [0, 50, 100, 200, 500]
#     resultados = []
    
#     for gamma in gammas:
#         print(f"\n--- Testando γ = {gamma} ---")
        
#         dados['parametros']['gamma'] = gamma
        
#         modelo = ModeloFCSA_MILP(
#             L=dados['L'],
#             T=dados['T'],
#             K=dados['K'],
#             parametros=dados['parametros']
#         )
        
#         modelo.construir_modelo()
#         sucesso = modelo.resolver(time_limit=180, mip_gap=0.03, log_output=False)
        
#         if sucesso:
#             resumo = modelo.obter_resumo()
#             resultados.append({
#                 'gamma': gamma,
#                 'estacoes': resumo['estacoes_instaladas'],
#                 'custo_total': resumo['valor_objetivo'],
#                 'beneficio': resumo['beneficio_transporte']
#             })
#             print(f"   ✓ Estações: {resumo['estacoes_instaladas']}, "
#                   f"Custo: R$ {resumo['valor_objetivo']:,.0f}, "
#                   f"Benefício: {resumo['beneficio_transporte']:.1f}")
#         else:
#             print(f"   ❌ Infactível")
    
#     # Imprimir tabela de resultados
#     print("\n" + "="*80)
#     print("📊 RESUMO DA ANÁLISE DE SENSIBILIDADE")
#     print("="*80)
#     print(f"{'γ':>10} | {'Estações':>10} | {'Custo Total':>20} | {'Benefício':>15}")
#     print("-"*80)
#     for r in resultados:
#         print(f"{r['gamma']:>10} | {r['estacoes']:>10} | R$ {r['custo_total']:>16,.2f} | {r['beneficio']:>15.1f}")
#     print("="*80)


# def main():
#     """Executa todos os testes"""
#     print("\n" + "🚀"*40)
#     print("VALIDAÇÃO DO MODELO FCSA MILP LINEARIZADO")
#     print("🚀"*40)
    
#     try:
#         # Teste 1: Modelo simplificado
#         modelo1 = teste_modelo_simplificado()
        
#         if modelo1:
#             input("\n⏸️  Pressione ENTER para continuar com o Teste 2...")
            
#             # Teste 2: Modelo médio
#             modelo2 = teste_modelo_medio()
            
#             if modelo2:
#                 input("\n⏸️  Pressione ENTER para continuar com o Teste 3...")
                
#                 # Teste 3: Sensibilidade
#                 teste_sensibilidade_gamma()
        
#         print("\n" + "="*80)
#         print("✅ TODOS OS TESTES CONCLUÍDOS COM SUCESSO")
#         print("="*80)
        
#     except Exception as e:
#         print(f"\n❌ ERRO DURANTE OS TESTES: {str(e)}")
#         import traceback
#         traceback.print_exc()


# if __name__ == "__main__":
#     main()





"""
Script de teste para modelo FCSA MILP
Versão simplificada - Usa modelo compacto
"""

from modelos.modelo_Caio import resolver_problema
import sys


def main():
    """Executa teste do modelo FCSA MILP"""
    
    print("="*80)
    print("🧪 TESTE DO MODELO FCSA MILP - PROBLEMA 0")
    print("="*80)
    
    try:
        # Resolver problema 0
        modelo = resolver_problema('dados/problema0')
        
        # Verificar solução
        if modelo.solucao:
            print("\n✅ TESTE CONCLUÍDO COM SUCESSO")
            print(f"\n📊 RESUMO:")
            print(f"   - Estações instaladas: {modelo.solucao['num_estacoes']}")
            print(f"   - Valor objetivo: R$ {modelo.solucao['valor_objetivo']:,.2f}")
            print(f"   - Tempo de solução: {modelo.solucao['tempo_s']:.2f}s")
            print(f"   - Gap de otimalidade: {modelo.solucao['gap_%']:.2f}%")
            
            return 0  # Sucesso
        else:
            print("\n❌ TESTE FALHOU: Modelo infactível")
            return 1  # Erro
            
    except FileNotFoundError as e:
        print(f"\n❌ ERRO: Arquivo não encontrado")
        print(f"   {e}")
        print(f"\n💡 Certifique-se de que a pasta 'dados/problema0' existe")
        print(f"   e contém todos os arquivos necessários.")
        return 1
        
    except Exception as e:
        print(f"\n❌ ERRO INESPERADO: {type(e).__name__}")
        print(f"   {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())