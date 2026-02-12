"""
Modelo de localización de electropostos con matriz de conectividad
"""

import numpy as np
from docplex.mp.model import Model
import time

class ModeloEletropostos:
    def __init__(self, coordenadas, demandas, capacidades_electropostos, custos_instalacao, max_distancia=50):
        """
        Inicializa el modelo de electropostos
        
        Args:
            coordenadas: Lista de tuplas (x, y) con coordenadas de los nodos
            demandas: Lista con demanda de cada nodo
            capacidades_electropostos: Lista con capacidad específica de cada posible electroposto
            custos_instalacao: Lista con costo de instalación específico de cada electroposto
            max_distancia: Distancia máxima de servicio (km)
        """
        self.coordenadas = coordenadas
        self.demandas = demandas
        self.capacidades = capacidades_electropostos
        self.custos_instalacao = custos_instalacao
        self.max_distancia = max_distancia
        self.n_nodos = len(coordenadas)
        
        # Validaciones
        assert len(demandas) == self.n_nodos, "Número de demandas debe coincidir con número de nodos"
        assert len(capacidades_electropostos) == self.n_nodos, "Número de capacidades debe coincidir con número de nodos"
        assert len(custos_instalacao) == self.n_nodos, "Número de costos debe coincidir con número de nodos"
        
        # Calcular matriz de distancias
        self.distancias = self._calcular_distancias()
        
        # Calcular matriz de conectividad
        self.conectividad = self._calcular_matriz_conectividad()
        
        # Variables para resultados
        self.modelo = None
        self.electropostos_instalados = []
        self.asignaciones = {}
        self.costo_total = 0
        self.tiempo_solucion = 0
    
    def _calcular_distancias(self):
        """Calcula matriz de distancias euclidianas entre todos los nodos"""
        n = self.n_nodos
        distancias = np.zeros((n, n))
        
        for i in range(n):
            for j in range(n):
                x1, y1 = self.coordenadas[i]
                x2, y2 = self.coordenadas[j]
                distancias[i][j] = np.sqrt((x1-x2)**2 + (y1-y2)**2)
        
        return distancias
    
    def _calcular_matriz_conectividad(self):
        """Calcula qué nodos puede atender cada electroposto"""
        conectividad = np.zeros((self.n_nodos, self.n_nodos), dtype=int)
        
        for i in range(self.n_nodos):
            for j in range(self.n_nodos):
                # Por ahora: distancia euclidiana
                # Después: Google Maps API
                if self.distancias[i][j] <= self.max_distancia:
                    conectividad[i][j] = 1
        
        print(f"\n🔗 MATRIZ DE CONECTIVIDAD:")
        print(f"   • Conexiones posibles: {np.sum(conectividad)} de {self.n_nodos * self.n_nodos}")
        print(f"   • Porcentaje conectividad: {(np.sum(conectividad) / (self.n_nodos * self.n_nodos)) * 100:.1f}%")
        
        return conectividad
    
    def resolver(self):
        """Resuelve el modelo de optimización"""
        inicio = time.time()
        
        # Crear modelo
        self.modelo = Model('Electropostos')
        
        # Variables de decisión
        # x[j] = 1 si se instala electroposto en nodo j
        x = self.modelo.binary_var_dict(range(self.n_nodos), name='x')
        
        # y[i,j] = 1 si nodo i es atendido por electroposto en j
        # Solo crear variables para conexiones factibles
        variables_y = {}
        for i in range(self.n_nodos):
            for j in range(self.n_nodos):
                if self.conectividad[i][j] == 1:
                    variables_y[(i, j)] = self.modelo.binary_var(name=f'y_{i}_{j}')
        
        # Función objetivo: minimizar costo total de instalación
        self.modelo.minimize(
            self.modelo.sum(self.custos_instalacao[j] * x[j] for j in range(self.n_nodos))
        )
        
        # Restricciones
        
        # 1. Todo nodo debe ser atendido por exactamente un electroposto
        for i in range(self.n_nodos):
            conexiones_posibles = []
            for j in range(self.n_nodos):
                if self.conectividad[i][j] == 1:
                    conexiones_posibles.append(variables_y[(i, j)])
            
            if conexiones_posibles:
                self.modelo.add_constraint(
                    self.modelo.sum(conexiones_posibles) == 1,
                    ctname=f'atendimento_nodo_{i}'
                )
            else:
                print(f"⚠️  ADVERTENCIA: Nodo {i} no puede ser atendido por ningún electroposto")
        
        # 2. Solo se puede atender desde electropostos instalados
        for i in range(self.n_nodos):
            for j in range(self.n_nodos):
                if self.conectividad[i][j] == 1:
                    self.modelo.add_constraint(
                        variables_y[(i, j)] <= x[j],
                        ctname=f'instalacao_{i}_{j}'
                    )
        
        # 3. Restricción de capacidad específica por electroposto
        for j in range(self.n_nodos):
            demandas_atendidas = []
            for i in range(self.n_nodos):
                if self.conectividad[i][j] == 1:
                    demandas_atendidas.append(self.demandas[i] * variables_y[(i, j)])
            
            if demandas_atendidas:
                self.modelo.add_constraint(
                    self.modelo.sum(demandas_atendidas) <= self.capacidades[j],
                    ctname=f'capacidad_especifica_{j}'
                )
        
        # Resolver
        print(f"\n🔍 RESOLVIENDO MODELO:")
        print(f"   • Variables binarias: {len(x) + len(variables_y)}")
        print(f"   • Restricciones: ~{len(x) + len(variables_y) + self.n_nodos}")
        
        solucion = self.modelo.solve()
        
        self.tiempo_solucion = time.time() - inicio
        
        if solucion:
            self._extraer_resultados(x, variables_y)
            return True
        else:
            print("❌ No se encontró solución factible")
            self._diagnosticar_infactibilidad()
            return False
    
    def _extraer_resultados(self, x, variables_y):
        """Extrae los resultados de la solución"""
        # Electropostos instalados
        self.electropostos_instalados = []
        for j in range(self.n_nodos):
            if x[j].solution_value > 0.5:
                self.electropostos_instalados.append(j)
        
        # Asignaciones
        self.asignaciones = {}
        for j in self.electropostos_instalados:
            self.asignaciones[j] = []
            demanda_atendida = 0
            
            for i in range(self.n_nodos):
                if self.conectividad[i][j] == 1 and variables_y[(i, j)].solution_value > 0.5:
                    self.asignaciones[j].append(i)
                    demanda_atendida += self.demandas[i]
            
            print(f"📍 Electroposto {j}: atiende nodos {self.asignaciones[j]} "
                  f"(demanda: {demanda_atendida:.1f}/{self.capacidades[j]})")
        
        # Costo total
        self.costo_total = self.modelo.objective_value
    
    def _diagnosticar_infactibilidad(self):
        """Diagnostica por qué el modelo puede ser infactible"""
        print(f"\n🔍 DIAGNÓSTICO DE INFACTIBILIDAD:")
        
        demanda_total = sum(self.demandas)
        capacidad_total = sum(self.capacidades)
        
        print(f"   • Demanda total: {demanda_total:.1f}")
        print(f"   • Capacidad total disponible: {capacidad_total:.1f}")
        print(f"   • Balance: {'✅ Suficiente' if capacidad_total >= demanda_total else '❌ Insuficiente'}")
        
        # Verificar nodos aislados
        nodos_aislados = []
        for i in range(self.n_nodos):
            if np.sum(self.conectividad[i, :]) == 0:
                nodos_aislados.append(i)
        
        if nodos_aislados:
            print(f"   • Nodos aislados: {nodos_aislados}")
            print(f"   • Sugerencia: Aumentar max_distancia o revisar coordenadas")
    
    def imprimir_resultados(self):
        """Imprime un resumen de los resultados"""
        print("\n" + "="*60)
        print("📊 RESULTADOS DE LA OPTIMIZACIÓN")
        print("="*60)
        
        print(f"⚡ Electropostos instalados: {len(self.electropostos_instalados)}")
        print(f"💰 Costo total: ${self.costo_total:,.0f}")
        print(f"⏱️  Tiempo de solución: {self.tiempo_solucion:.2f} segundos")
        print(f"📏 Distancia máxima: {self.max_distancia} km")
        
        print(f"\n📍 UBICACIONES Y ASIGNACIONES:")
        demanda_total_sistema = sum(self.demandas)
        capacidad_total_instalada = sum(self.capacidades[j] for j in self.electropostos_instalados)
        
        for j in self.electropostos_instalados:
            nodos_atendidos = self.asignaciones[j]
            demanda_atendida = sum(self.demandas[i] for i in nodos_atendidos)
            utilizacion = (demanda_atendida / self.capacidades[j]) * 100
            
            print(f"\n   Electroposto en nodo {j}:")
            print(f"   • Coordenadas: {self.coordenadas[j]}")
            print(f"   • Capacidad: {self.capacidades[j]} unidades")
            print(f"   • Costo instalación: ${self.custos_instalacao[j]:,}")
            print(f"   • Nodos atendidos: {nodos_atendidos}")
            print(f"   • Demanda atendida: {demanda_atendida:.1f} unidades")
            print(f"   • Utilización: {utilizacion:.1f}%")
            
            # Mostrar distancias
            distancias_str = []
            for i in nodos_atendidos:
                dist = self.distancias[i][j]
                distancias_str.append(f"nodo {i}: {dist:.1f}km")
            print(f"   • Distancias: {', '.join(distancias_str)}")
        
        print(f"\n📈 ESTADÍSTICAS GENERALES:")
        print(f"   • Demanda total del sistema: {demanda_total_sistema:.1f} unidades")
        print(f"   • Capacidad total instalada: {capacidad_total_instalada:.1f} unidades")
        print(f"   • Utilización promedio del sistema: {(demanda_total_sistema / capacidad_total_instalada * 100):.1f}%")
        
        print("="*60)