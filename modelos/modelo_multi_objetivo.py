"""
Modelo de localização de eletropostos com múltiplos objetivos
"""

import numpy as np
from docplex.mp.model import Model
import time

class ModeloEletropostosMultiObjetivo:
    def __init__(self, coordenadas, demandas, capacidades_eletropostos, custos_instalacao, 
                 distancia_maxima=50, tipo_objetivo='minimizar_custo', orcamento_maximo=None, 
                 pesos=(0.6, 0.4)):
        """
        Inicializa o modelo multi-objetivo de eletropostos
        
        Args:
            coordenadas: Lista de tuplas (x, y) com coordenadas dos nós
            demandas: Lista com demanda de cada nó
            capacidades_eletropostos: Lista com capacidade específica de cada possível eletroposto
            custos_instalacao: Lista com custo de instalação específico de cada eletroposto
            distancia_maxima: Distância máxima de atendimento (km)
            tipo_objetivo: 'minimizar_custo', 'maximizar_cobertura', 'multi_objetivo'
            orcamento_maximo: Orçamento máximo disponível (para maximizar cobertura)
            pesos: (peso_cobertura, peso_custo) para multi-objetivo
        """
        self.coordenadas = coordenadas
        self.demandas = demandas
        self.capacidades = capacidades_eletropostos
        self.custos_instalacao = custos_instalacao
        self.distancia_maxima = distancia_maxima
        self.tipo_objetivo = tipo_objetivo
        self.orcamento_maximo = orcamento_maximo
        self.pesos = pesos
        self.n_nos = len(coordenadas)
        
        # Validações
        assert len(demandas) == self.n_nos, "Número de demandas deve coincidir com número de nós"
        assert len(capacidades_eletropostos) == self.n_nos, "Número de capacidades deve coincidir com número de nós"
        assert len(custos_instalacao) == self.n_nos, "Número de custos deve coincidir com número de nós"
        
        if tipo_objetivo == 'maximizar_cobertura' and orcamento_maximo is None:
            raise ValueError("Orçamento máximo requerido para maximizar cobertura")
        
        if tipo_objetivo == 'multi_objetivo':
            assert len(pesos) == 2 and abs(sum(pesos) - 1.0) < 0.01, "Pesos devem somar 1.0"
        
        # Calcular matriz de distâncias e conectividade
        self.distancias = self._calcular_distancias()
        self.conectividade = self._calcular_matriz_conectividade()
        
        # Normalização para multi-objetivo
        self.demanda_total = sum(demandas)
        self.custo_total_maximo = sum(custos_instalacao)
        
        # Variáveis para resultados
        self.modelo = None
        self.eletropostos_instalados = []
        self.atribuicoes = {}
        self.custo_total = 0
        self.cobertura_total = 0
        self.cobertura_percentual = 0
        self.tempo_solucao = 0
        self.valor_objetivo = 0
    
    def _calcular_distancias(self):
        """Calcula matriz de distâncias euclidianas entre todos os nós"""
        n = self.n_nos
        distancias = np.zeros((n, n))
        
        for i in range(n):
            for j in range(n):
                x1, y1 = self.coordenadas[i]
                x2, y2 = self.coordenadas[j]
                distancias[i][j] = np.sqrt((x1-x2)**2 + (y1-y2)**2)
        
        return distancias
    
    def _calcular_matriz_conectividade(self):
        """Calcula quais nós podem ser atendidos por cada eletroposto"""
        conectividade = np.zeros((self.n_nos, self.n_nos), dtype=int)
        
        for i in range(self.n_nos):
            for j in range(self.n_nos):
                if self.distancias[i][j] <= self.distancia_maxima:
                    conectividade[i][j] = 1
        
        return conectividade
    
    def resolver(self):
        """Resolve o modelo conforme o tipo de objetivo selecionado"""
        print(f"\n RESOLVENDO MODELO: {self.tipo_objetivo.upper()}")
        
        if self.tipo_objetivo == 'minimizar_custo':
            return self._resolver_minimizar_custo()
        elif self.tipo_objetivo == 'maximizar_cobertura':
            return self._resolver_maximizar_cobertura()
        elif self.tipo_objetivo == 'multi_objetivo':
            return self._resolver_multi_objetivo()
        else:
            raise ValueError(f"Tipo de objetivo não válido: {self.tipo_objetivo}")
    
    def _resolver_minimizar_custo(self):
        """Minimiza custo de instalação atendendo toda a demanda"""
        inicio = time.time()
        
        self.modelo = Model('Eletropostos_MinCusto')
        
        # Variáveis de decisão
        x = self.modelo.binary_var_dict(range(self.n_nos), name='x')
        
        variaveis_y = {}
        for i in range(self.n_nos):
            for j in range(self.n_nos):
                if self.conectividade[i][j] == 1:
                    variaveis_y[(i, j)] = self.modelo.binary_var(name=f'y_{i}_{j}')
        
        # Função objetivo: minimizar custo
        self.modelo.minimize(
            self.modelo.sum(self.custos_instalacao[j] * x[j] for j in range(self.n_nos))
        )
        
        # Restrições
        self._adicionar_restricoes_basicas(x, variaveis_y)
        
        # Resolver
        solucao = self.modelo.solve()
        self.tempo_solucao = time.time() - inicio
        
        if solucao:
            self._extrair_resultados(x, variaveis_y)
            self.valor_objetivo = self.custo_total
            return True
        return False
    
    def _resolver_maximizar_cobertura(self):
        """Maximiza cobertura de demanda com orçamento limitado"""
        inicio = time.time()
        
        self.modelo = Model('Eletropostos_MaxCobertura')
        
        # Variáveis de decisão
        x = self.modelo.binary_var_dict(range(self.n_nos), name='x')
        
        # Variável para demanda atendida por nó
        z = self.modelo.binary_var_dict(range(self.n_nos), name='z')
        
        variaveis_y = {}
        for i in range(self.n_nos):
            for j in range(self.n_nos):
                if self.conectividade[i][j] == 1:
                    variaveis_y[(i, j)] = self.modelo.binary_var(name=f'y_{i}_{j}')
        
        # Função objetivo: maximizar demanda atendida
        self.modelo.maximize(
            self.modelo.sum(self.demandas[i] * z[i] for i in range(self.n_nos))
        )
        
        # Restrições
        
        # 1. Orçamento máximo
        self.modelo.add_constraint(
            self.modelo.sum(self.custos_instalacao[j] * x[j] for j in range(self.n_nos)) <= self.orcamento_maximo,
            ctname='orcamento_maximo'
        )
        
        # 2. Um nó está atendido se algum eletroposto o atende
        for i in range(self.n_nos):
            conexoes_possiveis = []
            for j in range(self.n_nos):
                if self.conectividade[i][j] == 1:
                    conexoes_possiveis.append(variaveis_y[(i, j)])
            
            if conexoes_possiveis:
                self.modelo.add_constraint(
                    z[i] <= self.modelo.sum(conexoes_possiveis),
                    ctname=f'atendimento_no_{i}'
                )
        
        # 3. Só pode atender de eletropostos instalados
        for i in range(self.n_nos):
            for j in range(self.n_nos):
                if self.conectividade[i][j] == 1:
                    self.modelo.add_constraint(
                        variaveis_y[(i, j)] <= x[j],
                        ctname=f'instalacao_{i}_{j}'
                    )
        
        # 4. Restrição de capacidade
        for j in range(self.n_nos):
            demandas_atendidas = []
            for i in range(self.n_nos):
                if self.conectividade[i][j] == 1:
                    demandas_atendidas.append(self.demandas[i] * variaveis_y[(i, j)])
            
            if demandas_atendidas:
                self.modelo.add_constraint(
                    self.modelo.sum(demandas_atendidas) <= self.capacidades[j],
                    ctname=f'capacidade_{j}'
                )
        
        # Resolver
        solucao = self.modelo.solve()
        self.tempo_solucao = time.time() - inicio
        
        if solucao:
            self._extrair_resultados_cobertura(x, variaveis_y, z)
            self.valor_objetivo = self.cobertura_total
            return True
        return False
    
    def _resolver_multi_objetivo(self):
        """Resolve modelo com função objetivo ponderada"""
        inicio = time.time()
        
        self.modelo = Model('Eletropostos_MultiObjetivo')
        
        # Variáveis de decisão
        x = self.modelo.binary_var_dict(range(self.n_nos), name='x')
        z = self.modelo.binary_var_dict(range(self.n_nos), name='z')
        
        variaveis_y = {}
        for i in range(self.n_nos):
            for j in range(self.n_nos):
                if self.conectividade[i][j] == 1:
                    variaveis_y[(i, j)] = self.modelo.binary_var(name=f'y_{i}_{j}')
        
        # Função objetivo ponderada (normalizada)
        peso_cobertura, peso_custo = self.pesos
        
        cobertura_normalizada = self.modelo.sum(self.demandas[i] * z[i] for i in range(self.n_nos)) / self.demanda_total
        custo_normalizado = self.modelo.sum(self.custos_instalacao[j] * x[j] for j in range(self.n_nos)) / self.custo_total_maximo
        
        # Maximizar cobertura e minimizar custo
        self.modelo.maximize(
            peso_cobertura * cobertura_normalizada - peso_custo * custo_normalizado
        )
        
        # Restrições similares a maximizar cobertura mas sem limite de orçamento
        
        # 1. Um nó está atendido se algum eletroposto o atende
        for i in range(self.n_nos):
            conexoes_possiveis = []
            for j in range(self.n_nos):
                if self.conectividade[i][j] == 1:
                    conexoes_possiveis.append(variaveis_y[(i, j)])
            
            if conexoes_possiveis:
                self.modelo.add_constraint(
                    z[i] <= self.modelo.sum(conexoes_possiveis),
                    ctname=f'atendimento_no_{i}'
                )
        
        # 2. Só pode atender de eletropostos instalados
        for i in range(self.n_nos):
            for j in range(self.n_nos):
                if self.conectividade[i][j] == 1:
                    self.modelo.add_constraint(
                        variaveis_y[(i, j)] <= x[j],
                        ctname=f'instalacao_{i}_{j}'
                    )
        
        # 3. Restrição de capacidade
        for j in range(self.n_nos):
            demandas_atendidas = []
            for i in range(self.n_nos):
                if self.conectividade[i][j] == 1:
                    demandas_atendidas.append(self.demandas[i] * variaveis_y[(i, j)])
            
            if demandas_atendidas:
                self.modelo.add_constraint(
                    self.modelo.sum(demandas_atendidas) <= self.capacidades[j],
                    ctname=f'capacidade_{j}'
                )
        
        # Resolver
        solucao = self.modelo.solve()
        self.tempo_solucao = time.time() - inicio
        
        if solucao:
            self._extrair_resultados_cobertura(x, variaveis_y, z)
            self.valor_objetivo = peso_cobertura * (self.cobertura_total / self.demanda_total) - peso_custo * (self.custo_total / self.custo_total_maximo)
            return True
        return False
    
    def _adicionar_restricoes_basicas(self, x, variaveis_y):
        """Adiciona restrições básicas para minimizar custo"""
        # 1. Todo nó deve ser atendido
        for i in range(self.n_nos):
            conexoes_possiveis = []
            for j in range(self.n_nos):
                if self.conectividade[i][j] == 1:
                    conexoes_possiveis.append(variaveis_y[(i, j)])
            
            if conexoes_possiveis:
                self.modelo.add_constraint(
                    self.modelo.sum(conexoes_possiveis) == 1,
                    ctname=f'atendimento_no_{i}'
                )
        
        # 2. Só pode atender de eletropostos instalados
        for i in range(self.n_nos):
            for j in range(self.n_nos):
                if self.conectividade[i][j] == 1:
                    self.modelo.add_constraint(
                        variaveis_y[(i, j)] <= x[j],
                        ctname=f'instalacao_{i}_{j}'
                    )
        
        # 3. Restrição de capacidade
        for j in range(self.n_nos):
            demandas_atendidas = []
            for i in range(self.n_nos):
                if self.conectividade[i][j] == 1:
                    demandas_atendidas.append(self.demandas[i] * variaveis_y[(i, j)])
            
            if demandas_atendidas:
                self.modelo.add_constraint(
                    self.modelo.sum(demandas_atendidas) <= self.capacidades[j],
                    ctname=f'capacidade_{j}'
                )
    
    def _extrair_resultados(self, x, variaveis_y):
        """Extrai resultados para minimizar custo"""
        # Eletropostos instalados
        self.eletropostos_instalados = []
        for j in range(self.n_nos):
            if x[j].solution_value > 0.5:
                self.eletropostos_instalados.append(j)
        
        # Atribuições
        self.atribuicoes = {}
        for j in self.eletropostos_instalados:
            self.atribuicoes[j] = []
            
            for i in range(self.n_nos):
                if self.conectividade[i][j] == 1 and variaveis_y[(i, j)].solution_value > 0.5:
                    self.atribuicoes[j].append(i)
        
        # Cálculos
        self.custo_total = self.modelo.objective_value
        self.cobertura_total = self.demanda_total  # 100% cobertura
        self.cobertura_percentual = 100.0
    
    def _extrair_resultados_cobertura(self, x, variaveis_y, z):
        """Extrai resultados para maximizar cobertura ou multi-objetivo"""
        # Eletropostos instalados
        self.eletropostos_instalados = []
        for j in range(self.n_nos):
            if x[j].solution_value > 0.5:
                self.eletropostos_instalados.append(j)
        
        # Atribuições
        self.atribuicoes = {}
        for j in self.eletropostos_instalados:
            self.atribuicoes[j] = []
            
            for i in range(self.n_nos):
                if self.conectividade[i][j] == 1 and variaveis_y[(i, j)].solution_value > 0.5:
                    self.atribuicoes[j].append(i)
        
        # Cálculos
        self.custo_total = sum(self.custos_instalacao[j] for j in self.eletropostos_instalados)
        
        # Cobertura
        nos_atendidos = []
        for i in range(self.n_nos):
            if z[i].solution_value > 0.5:
                nos_atendidos.append(i)
        
        self.cobertura_total = sum(self.demandas[i] for i in nos_atendidos)
        self.cobertura_percentual = (self.cobertura_total / self.demanda_total) * 100
    
    def obter_resumo(self):
        """Retorna resumo dos resultados"""
        return {
            'tipo_objetivo': self.tipo_objetivo,
            'eletropostos_instalados': len(self.eletropostos_instalados),
            'custo_total': self.custo_total,
            'cobertura_total': self.cobertura_total,
            'cobertura_percentual': self.cobertura_percentual,
            'tempo_solucao': self.tempo_solucao,
            'valor_objetivo': self.valor_objetivo,
            'localizacoes': self.eletropostos_instalados,
            'atribuicoes': self.atribuicoes
        }
    
    def imprimir_resultados(self):
        """Imprime resultados detalhados"""
        print(f"\n{'='*60}")
        print(f"📊 RESULTADOS - {self.tipo_objetivo.upper()}")
        print(f"{'='*60}")
        
        print(f"⚡ Eletropostos instalados: {len(self.eletropostos_instalados)}")
        print(f"�� Custo total: R\$ {self.custo_total:,.0f}")
        print(f"📊 Cobertura: {self.cobertura_total:.1f} unidades ({self.cobertura_percentual:.1f}%)")
        print(f"⏱️  Tempo de solução: {self.tempo_solucao:.2f} segundos")
        
        if self.tipo_objetivo == 'multi_objetivo':
            print(f"⚖️  Pesos: Cobertura {self.pesos[0]:.1%}, Custo {self.pesos[1]:.1%}")
            print(f"🎯 Valor objetivo: {self.valor_objetivo:.3f}")
        
        print(f"\n📍 LOCALIZAÇÕES:")
        for j in self.eletropostos_instalados:
            nos_atendidos = self.atribuicoes[j]
            demanda_atendida = sum(self.demandas[i] for i in nos_atendidos)
            print(f"   Eletroposto {j}: atende {nos_atendidos} (demanda: {demanda_atendida:.1f})")
        
        print(f"{'='*60}")