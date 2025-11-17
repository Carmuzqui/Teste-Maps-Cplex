"""
Configurações da aplicação com variáveis de ambiente
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Carregar variáveis do arquivo .env
load_dotenv()

class Config:
    """Configurações da aplicação"""
    
    # Google Maps API
    GOOGLE_MAPS_API_KEY: Optional[str] = os.getenv('GOOGLE_MAPS_API_KEY')
    
    # Configurações do cache
    CACHE_DIR: str = os.getenv('CACHE_DIR', 'cache')
    
    # Configurações do modelo
    DISTANCIA_MAXIMA_DEFAULT: int = int(os.getenv('DISTANCIA_MAXIMA_DEFAULT', '10'))
    ORCAMENTO_DEFAULT: int = int(os.getenv('ORCAMENTO_DEFAULT', '800000'))
    
    # Configurações do Streamlit
    PAGE_TITLE: str = "Otimização de Eletropostos - Campinas"
    PAGE_ICON: str = "⚡"
    
    # Debug
    DEBUG: bool = os.getenv('DEBUG', 'False').lower() == 'true'
    
    @classmethod
    def has_google_maps_api(cls) -> bool:
        """Verifica se a API do Google Maps está configurada"""
        return cls.GOOGLE_MAPS_API_KEY is not None and cls.GOOGLE_MAPS_API_KEY.strip() != ""
    
    @classmethod
    def get_google_maps_api_key(cls) -> Optional[str]:
        """Retorna a API key do Google Maps se disponível"""
        if cls.has_google_maps_api():
            return cls.GOOGLE_MAPS_API_KEY.strip()
        return None
    
    @classmethod
    def print_config_status(cls):
        """Imprime status das configurações (para debug)"""
        if cls.DEBUG:
            print("=== CONFIGURAÇÕES ===")
            print(f"Google Maps API: {'✅ Configurada' if cls.has_google_maps_api() else '❌ Não configurada'}")
            print(f"Cache Dir: {cls.CACHE_DIR}")
            print(f"Debug Mode: {cls.DEBUG}")
            print("====================")