"""
Sistema de cache para Google Maps API - distâncias e rotas
"""

import googlemaps
import pickle
import os
import json
import streamlit as st
from typing import List, Tuple, Dict, Optional
import numpy as np
import hashlib

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
    
    def obter_matriz_distancias(self, coordenadas: List[Tuple[float, float]]) -> np.ndarray:
        """
        Obtém matriz de distâncias reais usando Google Maps com cache
        
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
        
        st.info("🌐 Consultando Google Maps API para distâncias...")
        
        n = len(coordenadas)
        matriz_distancias = np.zeros((n, n))
        
        try:
            # Preparar coordenadas para API
            origins = [f"{lat},{lon}" for lat, lon in coordenadas]
            destinations = origins.copy()
            
            # Fazer chamada para Distance Matrix API
            with st.spinner("Calculando distâncias reais..."):
                result = self.gmaps.distance_matrix(
                    origins=origins,
                    destinations=destinations,
                    mode="driving",
                    units="metric",
                    avoid="tolls"
                )
            
            # Processar resultados
            for i, row in enumerate(result['rows']):
                for j, element in enumerate(row['elements']):
                    if element['status'] == 'OK':
                        # Distância em metros, converter para km
                        distancia_km = element['distance']['value'] / 1000
                        matriz_distancias[i][j] = distancia_km
                    else:
                        # Fallback para distância euclidiana
                        matriz_distancias[i][j] = self._distancia_euclidiana(
                            coordenadas[i], coordenadas[j]
                        )
            
            # Salvar no cache
            self.distances_cache[coords_hash] = matriz_distancias
            self._save_distances_cache()
            
            st.success("✅ Distâncias obtidas e salvas no cache!")
            
        except Exception as e:
            st.warning(f"⚠️ Erro na API do Google Maps: {e}")
            st.info("🔄 Usando distâncias euclidianas como fallback")
            
            # Fallback para distâncias euclidianas
            for i in range(n):
                for j in range(n):
                    matriz_distancias[i][j] = self._distancia_euclidiana(
                        coordenadas[i], coordenadas[j]
                    )
        
        return matriz_distancias
    
    def obter_rota(self, origem: Tuple[float, float], destino: Tuple[float, float]) -> Optional[List[Tuple[float, float]]]:
        """
        Obtém rota entre dois pontos com cache
        
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
        
        try:
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
            st.warning(f"Erro ao obter rota: {e}")
        
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