"""
Modelo de otimização para localização de eletropostos usando CPLEX
"""

from docplex.mp.model import Model
import time
import numpy as np

class ModeloEletropostos:
    def __init__(self, dados):
        """
        Inicializa o modelo com os dados fornecidos
        """
        self.dados = dados
        self.modelo = None
        self.solucao = None
        self.tempo_execucao = 0
        
    def criar_modelo(self):
        """
        Cria o modelo matemático de otimização
        """
        dados = self.dados
        
        # Criar modelo CPLEX
        self.modelo = Model(name="Otimizacao_Eletropostos")
        
        # Índices
        I = range(len(dados['custos_fixos']))  # Eletropostos candidatos
        J = range(len(dados['demanda_nos']))   # Nós de demanda
        
        # Variáveis de decisão
        # x[i] = 1 se eletroposto i é instalado
        x = self.modelo.binary_var_dict(I, name="instalar_eletroposto")
        
        # y[j] = 1 se nó de demanda j é atendido
        y = self.modelo.binary_var_dict(J, name="no_atendido")
        
        # z[i,j] = 1 se nó j é atendido por eletroposto i
        z = self.modelo.binary_var_dict([(i,j) for i in I for j in J], name="atendimento")
        
        # cap[i] = capacidade instalada no eletroposto i
        cap = self.modelo.continuous_var_dict(I, lb=0, name="capacidade")
        
        # Função objetivo
        cobertura_total = self.modelo.sum(dados['demanda_nos'][j] * y[j] for j in J)
        custo_total = (self.modelo.sum(dados['custos_fixos'][i] * x[i] for i in I) + 
                      self.modelo.sum(dados['custo_por_capacidade'] * cap[i] for i in I))
        
        # Normalização para balanceamento
        demanda_maxima = sum(dados['demanda_nos'])
        custo_maximo = dados['parametros']['orcamento_total']
        
        objetivo = (dados['parametros']['peso_cobertura'] * (cobertura_total / demanda_maxima) - 
                   dados['parametros']['peso_custo'] * (custo_total / custo_maximo))
        
        self.modelo.maximize(objetivo)
        
        # Restrições
        
        # 1. Consistência: nó só pode ser atendido se há eletroposto instalado
        for i in I:
            for j in J:
                self.modelo.add_constraint(z[i,j] <= x[i], 
                                         f"consistencia_eletroposto_{i}_no_{j}")
        
        # 2. Conectividade: só pode atender se há conexão possível
        for i in I:
            for j in J:
                if dados['conectividade'][i][j] == 0:
                    self.modelo.add_constraint(z[i,j] == 0, 
                                             f"conectividade_{i}_{j}")
        
        # 3. Cobertura única: cada nó é atendido por no máximo um eletroposto
        for j in J:
            self.modelo.add_constraint(self.modelo.sum(z[i,j] for i in I) <= 1,
                                     f"cobertura_unica_no_{j}")
        
        # 4. Definição de nó atendido
        for j in J:
            self.modelo.add_constraint(y[j] == self.modelo.sum(z[i,j] for i in I),
                                     f"definicao_atendimento_no_{j}")
        
        # 5. Capacidade: eletroposto não pode exceder sua capacidade
        for i in I:
            self.modelo.add_constraint(self.modelo.sum(z[i,j] for j in J) <= cap[i],
                                     f"limite_capacidade_{i}")
        
        # 6. Capacidade máxima por eletroposto
        for i in I:
            self.modelo.add_constraint(cap[i] <= dados['capacidades_max'][i] * x[i],
                                     f"capacidade_maxima_{i}")
        
        # 7. Restrição de orçamento
        self.modelo.add_constraint(custo_total <= dados['parametros']['orcamento_total'],
                                 "limite_orcamento")
        
        # Armazenar variáveis para acesso posterior
        self.variaveis = {
            'x': x,
            'y': y,
            'z': z,
            'cap': cap
        }
        
        return self.modelo
    
    def resolver(self, limite_tempo=60, verbose=True):
        """
        Resolve o modelo de otimização
        """
        if self.modelo is None:
            self.criar_modelo()
        
        # Configurações do solver
        self.modelo.parameters.timelimit = limite_tempo
        if not verbose:
            self.modelo.parameters.mip.display = 0
        
        # Resolver
        inicio = time.time()
        solucao = self.modelo.solve()
        self.tempo_execucao = time.time() - inicio
        
        if solucao:
            self.solucao = solucao
            return True
        else:
            print("❌ Não foi possível encontrar solução ótima")
            print(f"Status: {self.modelo.solve_details.status}")
            return False
    
    def obter_resultados(self):
        """
        Extrai e organiza os resultados da otimização
        """
        if not self.solucao:
            return None
        
        dados = self.dados
        vars = self.variaveis
        
        # Eletropostos instalados
        eletropostos_instalados = []
        for i in range(len(dados['custos_fixos'])):
            if vars['x'][i].solution_value > 0.5:
                capacidade = vars['cap'][i].solution_value
                eletropostos_instalados.append({
                    'id': i,
                    'nome': dados['nomes_eletropostos'][i],
                    'custo_fixo': dados['custos_fixos'][i],
                    'capacidade_instalada': capacidade,
                    'custo_total': dados['custos_fixos'][i] + dados['custo_por_capacidade'] * capacidade
                })
        
        # Nós atendidos
        nos_atendidos = []
        atendimentos = []
        for j in range(len(dados['demanda_nos'])):
            if vars['y'][j].solution_value > 0.5:
                # Encontrar qual eletroposto atende este nó
                eletroposto_responsavel = None
                for i in range(len(dados['custos_fixos'])):
                    if vars['z'][i,j].solution_value > 0.5:
                        eletroposto_responsavel = i
                        atendimentos.append({
                            'eletroposto_id': i,
                            'eletroposto_nome': dados['nomes_eletropostos'][i],
                            'no_id': j,
                            'no_nome': dados['nomes_nos'][j],
                            'demanda': dados['demanda_nos'][j]
                        })
                        break
                
                nos_atendidos.append({
                    'id': j,
                    'nome': dados['nomes_nos'][j],
                    'demanda': dados['demanda_nos'][j],
                    'eletroposto_responsavel': eletroposto_responsavel
                })
        
        # Métricas
        demanda_total = sum(dados['demanda_nos'])
        demanda_atendida = sum(no['demanda'] for no in nos_atendidos)
        custo_total = sum(ep['custo_total'] for ep in eletropostos_instalados)
        
        resultados = {
            'eletropostos_instalados': eletropostos_instalados,
            'nos_atendidos': nos_atendidos,
            'atendimentos': atendimentos,
            'metricas': {
                'num_eletropostos': len(eletropostos_instalados),
                'num_nos_atendidos': len(nos_atendidos),
                'demanda_total': demanda_total,
                'demanda_atendida': demanda_atendida,
                'cobertura_percentual': (demanda_atendida / demanda_total) * 100,
                'custo_total': custo_total,
                'orcamento_utilizado': (custo_total / dados['parametros']['orcamento_total']) * 100,
                'eficiencia': demanda_atendida / custo_total if custo_total > 0 else 0,
                'tempo_execucao': self.tempo_execucao
            },
            'valor_objetivo': self.solucao.objective_value
        }
        
        return resultados
    
    def imprimir_relatorio(self, resultados):
        """
        Imprime relatório detalhado dos resultados
        """
        if not resultados:
            print("❌ Nenhum resultado disponível")
            return
        
        print("\n" + "="*60)
        print("📊 RELATÓRIO DE OTIMIZAÇÃO DE ELETROPOSTOS")
        print("="*60)
        
        metricas = resultados['metricas']
        
        print(f"\n🎯 MÉTRICAS PRINCIPAIS:")
        print(f"   • Valor objetivo: {resultados['valor_objetivo']:.4f}")
        print(f"   • Tempo de execução: {metricas['tempo_execucao']:.2f} segundos")
        print(f"   • Eletropostos instalados: {metricas['num_eletropostos']}")
        print(f"   • Nós atendidos: {metricas['num_nos_atendidos']}")
        
        print(f"\n📈 COBERTURA:")
        print(f"   • Demanda total: {metricas['demanda_total']} veículos/dia")
        print(f"   • Demanda atendida: {metricas['demanda_atendida']} veículos/dia")
        print(f"   • Cobertura: {metricas['cobertura_percentual']:.1f}%")
        
        print(f"\n💰 CUSTOS:")
        print(f"   • Custo total: R\$ {metricas['custo_total']:,.2f}")
        print(f"   • Orçamento utilizado: {metricas['orcamento_utilizado']:.1f}%")
        print(f"   • Eficiência: {metricas['eficiencia']:.2f} veículos/R\$")
        
        print(f"\n🏗️ ELETROPOSTOS INSTALADOS:")
        for ep in resultados['eletropostos_instalados']:
            print(f"   • {ep['nome']}: Capacidade {ep['capacidade_instalada']:.0f} nós, "
                  f"Custo R\$ {ep['custo_total']:,.2f}")
        
        print(f"\n🎯 ATENDIMENTOS:")
        for atend in resultados['atendimentos']:
            print(f"   • {atend['no_nome']} (demanda: {atend['demanda']}) → {atend['eletroposto_nome']}")
        
        print("\n" + "="*60)