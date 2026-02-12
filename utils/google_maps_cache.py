"""
Sistema de cache para Google Maps API - distâncias e rotas com controle de limites
"""

import googlemaps
import pickle
import os
import json
import streamlit as st
from typing import List, Tuple, Dict, Optional
import numpy as np
import hashlib
import time

class GoogleMapsCache:
    def __init__(self, api_key: str, cache_dir: str = "cache"):
        """
        Inicializa o sistema de cache do Google Maps
        
        Args:
            api_key: Chave da API do Google Maps
            cache_dir: Diretório para armazenar cache
        """
        self.gmaps = googlemaps.Client(key=api_key)
        self.cache_dir = cache_dir
        self.distances_file = os.path.join(cache_dir, "distances_matrix.pkl")
        self.routes_file = os.path.join(cache_dir, "routes_cache.pkl")
        
        # Configurações para evitar limites da API
        self.max_elements_per_request = 25  # Google Maps permite 25 origens x 25 destinos = 625 elementos
        self.delay_between_requests = 0.1   # Delay entre requisições (100ms)
        self.max_retries = 3               # Máximo de tentativas por requisição
        
        # Criar diretório de cache se não existir
        os.makedirs(cache_dir, exist_ok=True)
        
        # Carregar caches existentes
        self.distances_cache = self._load_distances_cache()
        self.routes_cache = self._load_routes_cache()
    
    def _generate_coords_hash(self, coordenadas: List[Tuple[float, float]]) -> str:
        """Gera hash único para conjunto de coordenadas"""
        coords_str = str(sorted(coordenadas))
        return hashlib.md5(coords_str.encode()).hexdigest()
    
    def _load_distances_cache(self) -> Dict:
        """Carrega cache de distâncias"""
        if os.path.exists(self.distances_file):
            try:
                with open(self.distances_file, 'rb') as f:
                    return pickle.load(f)
            except:
                return {}
        return {}
    
    def _load_routes_cache(self) -> Dict:
        """Carrega cache de rotas"""
        if os.path.exists(self.routes_file):
            try:
                with open(self.routes_file, 'rb') as f:
                    return pickle.load(f)
            except:
                return {}
        return {}
    
    def _save_distances_cache(self):
        """Salva cache de distâncias"""
        with open(self.distances_file, 'wb') as f:
            pickle.dump(self.distances_cache, f)
    
    def _save_routes_cache(self):
        """Salva cache de rotas"""
        with open(self.routes_file, 'wb') as f:
            pickle.dump(self.routes_cache, f)
    
    def _dividir_coordenadas_em_lotes(self, coordenadas: List[Tuple[float, float]]) -> List[List[int]]:
        """
        Divide coordenadas em lotes para não exceder limites da API
        
        Args:
            coordenadas: Lista de coordenadas
            
        Returns:
            Lista de lotes com índices das coordenadas
        """
        n = len(coordenadas)
        lotes = []
        
        # Calcular tamanho do lote baseado no limite de elementos
        max_coords_per_batch = min(self.max_elements_per_request, n)
        
        for i in range(0, n, max_coords_per_batch):
            lote = list(range(i, min(i + max_coords_per_batch, n)))
            lotes.append(lote)
        
        return lotes
    
    def _fazer_requisicao_com_retry(self, origins: List[str], destinations: List[str]) -> Optional[Dict]:
        """
        Faz requisição com retry automático em caso de erro
        
        Args:
            origins: Lista de coordenadas de origem
            destinations: Lista de coordenadas de destino
            
        Returns:
            Resultado da API ou None se falhar
        """
        for tentativa in range(self.max_retries):
            try:
                # Delay entre requisições para evitar rate limiting
                if tentativa > 0:
                    time.sleep(self.delay_between_requests * (2 ** tentativa))  # Backoff exponencial
                
                result = self.gmaps.distance_matrix(
                    origins=origins,
                    destinations=destinations,
                    mode="driving",
                    units="metric",
                    avoid="tolls"
                )
                
                return result
                
            except googlemaps.exceptions.ApiError as e:
                st.warning(f"⚠️ Erro na API (tentativa {tentativa + 1}/{self.max_retries}): {e}")
                if tentativa == self.max_retries - 1:
                    return None
                    
            except Exception as e:
                st.warning(f"⚠️ Erro inesperado (tentativa {tentativa + 1}/{self.max_retries}): {e}")
                if tentativa == self.max_retries - 1:
                    return None
        
        return None
    
    def obter_matriz_distancias(self, coordenadas: List[Tuple[float, float]]) -> np.ndarray:
        """
        Obtém matriz de distâncias reais usando Google Maps com cache e controle de limites
        
        Args:
            coordenadas: Lista de (lat, lon)
            
        Returns:
            Matriz NxN de distâncias em km
        """
        coords_hash = self._generate_coords_hash(coordenadas)
        
        # Verificar se já existe no cache
        if coords_hash in self.distances_cache:
            st.info("📁 Usando distâncias em cache (Google Maps)")
            return self.distances_cache[coords_hash]
        
        n = len(coordenadas)
        matriz_distancias = np.zeros((n, n))
        
        # Verificar se excede limites práticos
        total_elements = n * n
        if total_elements > 2500:  # Limite prático para evitar muitas requisições
            st.warning(f"⚠️ Muitas coordenadas ({n}x{n}={total_elements} elementos). Usando distâncias euclidianas.")
            return self._calcular_matriz_euclidiana(coordenadas)
        
        st.info(f"🌐 Consultando Google Maps API para {n} localizações...")
        
        try:
            # Dividir em lotes
            lotes = self._dividir_coordenadas_em_lotes(coordenadas)
            total_lotes = len(lotes)
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            lote_atual = 0
            
            for i, lote_origem in enumerate(lotes):
                for j, lote_destino in enumerate(lotes):
                    lote_atual += 1
                    
                    # Atualizar progresso
                    progresso = lote_atual / (total_lotes * total_lotes)
                    progress_bar.progress(progresso)
                    status_text.text(f"Processando lote {lote_atual}/{total_lotes * total_lotes}...")
                    
                    # Preparar coordenadas para este lote
                    origins = [f"{coordenadas[idx][0]},{coordenadas[idx][1]}" for idx in lote_origem]
                    destinations = [f"{coordenadas[idx][0]},{coordenadas[idx][1]}" for idx in lote_destino]
                    
                    # Fazer requisição
                    result = self._fazer_requisicao_com_retry(origins, destinations)
                    
                    if result is None:
                        st.warning(f"⚠️ Falha no lote {lote_atual}. Usando distâncias euclidianas para este lote.")
                        # Preencher com distâncias euclidianas
                        for oi, origem_idx in enumerate(lote_origem):
                            for di, destino_idx in enumerate(lote_destino):
                                matriz_distancias[origem_idx][destino_idx] = self._distancia_euclidiana(
                                    coordenadas[origem_idx], coordenadas[destino_idx]
                                )
                        continue
                    
                    # Processar resultados
                    for oi, origem_idx in enumerate(lote_origem):
                        if oi < len(result['rows']):
                            for di, destino_idx in enumerate(lote_destino):
                                if di < len(result['rows'][oi]['elements']):
                                    element = result['rows'][oi]['elements'][di]
                                    if element['status'] == 'OK':
                                        # Distância em metros, converter para km
                                        distancia_km = element['distance']['value'] / 1000
                                        matriz_distancias[origem_idx][destino_idx] = distancia_km
                                    else:
                                        # Fallback para distância euclidiana
                                        matriz_distancias[origem_idx][destino_idx] = self._distancia_euclidiana(
                                            coordenadas[origem_idx], coordenadas[destino_idx]
                                        )
                    
                    # Delay entre lotes
                    time.sleep(self.delay_between_requests)
            
            # Limpar elementos de progresso
            progress_bar.empty()
            status_text.empty()
            
            # Salvar no cache
            self.distances_cache[coords_hash] = matriz_distancias
            self._save_distances_cache()
            
            st.success("✅ Distâncias obtidas e salvas no cache!")
            
        except Exception as e:
            st.error(f"❌ Erro geral na API do Google Maps: {e}")
            st.info("🔄 Usando distâncias euclidianas como fallback")
            
            # Fallback completo para distâncias euclidianas
            matriz_distancias = self._calcular_matriz_euclidiana(coordenadas)
        
        return matriz_distancias
    
    def _calcular_matriz_euclidiana(self, coordenadas: List[Tuple[float, float]]) -> np.ndarray:
        """
        Calcula matriz completa de distâncias euclidianas
        
        Args:
            coordenadas: Lista de coordenadas
            
        Returns:
            Matriz de distâncias euclidianas
        """
        n = len(coordenadas)
        matriz_distancias = np.zeros((n, n))
        
        for i in range(n):
            for j in range(n):
                matriz_distancias[i][j] = self._distancia_euclidiana(
                    coordenadas[i], coordenadas[j]
                )
        
        return matriz_distancias
    
    def obter_rota(self, origem: Tuple[float, float], destino: Tuple[float, float]) -> Optional[List[Tuple[float, float]]]:
        """
        Obtém rota entre dois pontos com cache e retry
        
        Args:
            origem: (lat, lon) de origem
            destino: (lat, lon) de destino
            
        Returns:
            Lista de coordenadas da rota ou None se erro
        """
        route_key = f"{origem[0]:.6f},{origem[1]:.6f}_{destino[0]:.6f},{destino[1]:.6f}"
        
        # Verificar cache
        if route_key in self.routes_cache:
            return self.routes_cache[route_key]
        
        for tentativa in range(self.max_retries):
            try:
                if tentativa > 0:
                    time.sleep(self.delay_between_requests * (2 ** tentativa))
                
                # Obter rota da API
                directions_result = self.gmaps.directions(
                    origin=f"{origem[0]},{origem[1]}",
                    destination=f"{destino[0]},{destino[1]}",
                    mode="driving",
                    avoid="tolls"
                )
                
                if directions_result:
                    # Extrair pontos da rota
                    route = directions_result[0]['legs'][0]
                    pontos_rota = []
                    
                    for step in route['steps']:
                        # Decodificar polyline
                        polyline_points = googlemaps.convert.decode_polyline(
                            step['polyline']['points']
                        )
                        pontos_rota.extend([(p['lat'], p['lng']) for p in polyline_points])
                    
                    # Salvar no cache
                    self.routes_cache[route_key] = pontos_rota
                    self._save_routes_cache()
                    
                    return pontos_rota
                
            except Exception as e:
                if tentativa == self.max_retries - 1:
                    st.warning(f"Erro ao obter rota após {self.max_retries} tentativas: {e}")
        
        return None
    
    def _distancia_euclidiana(self, coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
        """Calcula distância euclidiana como fallback"""
        import math
        
        lat1, lon1 = coord1
        lat2, lon2 = coord2
        
        # Fórmula de Haversine
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        r = 6371  # Raio da Terra em km
        
        return c * r
    
    def limpar_cache(self):
        """Remove todos os arquivos de cache"""
        try:
            if os.path.exists(self.distances_file):
                os.remove(self.distances_file)
            if os.path.exists(self.routes_file):
                os.remove(self.routes_file)
            self.distances_cache = {}
            self.routes_cache = {}
            st.success("🗑️ Cache limpo com sucesso!")
        except Exception as e:
            st.error(f"Erro ao limpar cache: {e}")
    
    def obter_estatisticas_cache(self) -> Dict:
        """Retorna estatísticas do cache"""
        return {
            'matrizes_distancias': len(self.distances_cache),
            'rotas_individuais': len(self.routes_cache),
            'tamanho_cache_distancias': os.path.getsize(self.distances_file) if os.path.exists(self.distances_file) else 0,
            'tamanho_cache_rotas': os.path.getsize(self.routes_file) if os.path.exists(self.routes_file) else 0
        }