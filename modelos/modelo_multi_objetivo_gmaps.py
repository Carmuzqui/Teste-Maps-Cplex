"""
Modelo multi-objetivo com integração Google Maps
"""

import numpy as np
from typing import List, Tuple, Optional
from modelos.modelo_multi_objetivo import ModeloEletropostosMultiObjetivo
from utils.google_maps_cache import GoogleMapsCache

class ModeloEletropostosGoogleMaps(ModeloEletropostosMultiObjetivo):
    def __init__(self, 
                 coordenadas: List[Tuple[float, float]],
                 demandas: List[float],
                 capacidades_eletropostos: List[float],
                 custos_instalacao: List[float],
                 distancia_maxima: float,
                 tipo_objetivo: str = 'minimizar_custo',
                 orcamento_maximo: Optional[float] = None,
                 pesos: Tuple[float, float] = (0.6, 0.4),
                 google_maps_api_key: Optional[str] = None):
        """
        Inicializa modelo com Google Maps
        
        Args:
            google_maps_api_key: Chave da API do Google Maps (opcional)
            Outros parâmetros: iguais ao modelo base
        """
        self.google_maps_api_key = google_maps_api_key
        self.gmaps_cache = None
        self.matriz_distancias_reais = None
        
        # Inicializar Google Maps se API key fornecida
        if google_maps_api_key:
            self.gmaps_cache = GoogleMapsCache(google_maps_api_key)
            self.matriz_distancias_reais = self.gmaps_cache.obter_matriz_distancias(coordenadas)
        
        # Inicializar modelo base
        super().__init__(
            coordenadas=coordenadas,
            demandas=demandas,
            capacidades_eletropostos=capacidades_eletropostos,
            custos_instalacao=custos_instalacao,
            distancia_maxima=distancia_maxima,
            tipo_objetivo=tipo_objetivo,
            orcamento_maximo=orcamento_maximo,
            pesos=pesos
        )
    
    def _calcular_distancia(self, i: int, j: int) -> float:
        """
        Calcula distância entre dois pontos
        Usa Google Maps se disponível, senão euclidiana
        """
        if self.matriz_distancias_reais is not None:
            return self.matriz_distancias_reais[i][j]
        else:
            # Fallback para distância euclidiana
            return super()._calcular_distancia(i, j)
    
    def obter_rota_entre_pontos(self, origem_idx: int, destino_idx: int) -> Optional[List[Tuple[float, float]]]:
        """
        Obtém rota real entre dois pontos usando Google Maps
        
        Args:
            origem_idx: Índice do ponto de origem
            destino_idx: Índice do ponto de destino
            
        Returns:
            Lista de coordenadas da rota ou None
        """
        if self.gmaps_cache is None:
            return None
        
        origem = self.coordenadas[origem_idx]
        destino = self.coordenadas[destino_idx]
        
        return self.gmaps_cache.obter_rota(origem, destino)
    
    def obter_resumo_com_rotas(self) -> dict:
        """
        Obtém resumo incluindo informações de rotas
        """
        resumo = super().obter_resumo()
        
        # Adicionar informações de rotas se Google Maps disponível
        if self.gmaps_cache is not None:
            resumo['usa_google_maps'] = True
            resumo['rotas_disponiveis'] = True
            
            # Calcular rotas para cada atribuição
            rotas = {}
            for eletroposto_idx in self.eletropostos_instalados:
                nos_atendidos = self.atribuicoes[eletroposto_idx]
                rotas[eletroposto_idx] = {}
                
                for no_idx in nos_atendidos:
                    if no_idx != eletroposto_idx:  # Não calcular rota para si mesmo
                        rota = self.obter_rota_entre_pontos(no_idx, eletroposto_idx)
                        if rota:
                            rotas[eletroposto_idx][no_idx] = rota
            
            resumo['rotas'] = rotas
        else:
            resumo['usa_google_maps'] = False
            resumo['rotas_disponiveis'] = False
        
        return resumo