"""
Gerenciador de distâncias com exportação/importação Excel/CSV
"""

import pandas as pd
import numpy as np
import streamlit as st
import os
from typing import List, Tuple, Dict, Optional
import pickle
from datetime import datetime

class DistanceManager:
    def __init__(self, cache_dir: str = "cache"):
        """
        Inicializa o gerenciador de distâncias
        
        Args:
            cache_dir: Diretório para armazenar arquivos
        """
        self.cache_dir = cache_dir
        self.distances_file = os.path.join(cache_dir, "distances_matrix.pkl")
        self.excel_file = os.path.join(cache_dir, "matriz_distancias.xlsx")
        self.csv_file = os.path.join(cache_dir, "matriz_distancias.csv")
        
        # Criar diretório se não existir
        os.makedirs(cache_dir, exist_ok=True)
    
    def calcular_matriz_euclidiana(self, coordenadas: List[Tuple[float, float]], nomes: List[str]) -> np.ndarray:
        """
        Calcula matriz de distâncias euclidianas
        
        Args:
            coordenadas: Lista de (lat, lon)
            nomes: Lista de nomes dos locais
            
        Returns:
            Matriz NxN de distâncias em km
        """
        n = len(coordenadas)
        matriz_distancias = np.zeros((n, n))
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total_calculos = n * n
        calculo_atual = 0
        
        for i in range(n):
            for j in range(n):
                calculo_atual += 1
                
                # Atualizar progresso
                progresso = calculo_atual / total_calculos
                progress_bar.progress(progresso)
                status_text.text(f"Calculando distâncias: {calculo_atual}/{total_calculos}")
                
                matriz_distancias[i][j] = self._distancia_haversine(
                    coordenadas[i], coordenadas[j]
                )
        
        # Limpar elementos de progresso
        progress_bar.empty()
        status_text.empty()
        
        return matriz_distancias
    
    def _distancia_haversine(self, coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
        """Calcula distância usando fórmula de Haversine"""
        import math
        
        lat1, lon1 = coord1
        lat2, lon2 = coord2
        
        # Converter para radianos
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Fórmula de Haversine
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        r = 6371  # Raio da Terra em km
        
        return c * r
    
    def exportar_para_excel(self, matriz_distancias: np.ndarray, nomes: List[str]) -> str:
        """
        Exporta matriz de distâncias para Excel
        
        Args:
            matriz_distancias: Matriz NxN de distâncias
            nomes: Lista de nomes dos locais
            
        Returns:
            Caminho do arquivo Excel criado
        """
        try:
            # Criar DataFrame com nomes como índices e colunas
            df = pd.DataFrame(
                matriz_distancias,
                index=nomes,
                columns=nomes
            )
            
            # Criar arquivo Excel com múltiplas abas
            with pd.ExcelWriter(self.excel_file, engine='openpyxl') as writer:
                # Aba principal com matriz de distâncias
                df.to_excel(writer, sheet_name='Matriz_Distancias')
                
                # Aba com informações dos locais
                info_df = pd.DataFrame({
                    'Local': nomes,
                    'Indice': range(len(nomes))
                })
                info_df.to_excel(writer, sheet_name='Informacoes_Locais', index=False)
                
                # Aba com metadados
                metadata_df = pd.DataFrame({
                    'Propriedade': [
                        'Data_Criacao',
                        'Numero_Locais',
                        'Tipo_Distancia',
                        'Unidade',
                        'Arquivo_Origem'
                    ],
                    'Valor': [
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        len(nomes),
                        'Euclidiana (Haversine)',
                        'Quilômetros',
                        'Sistema de Otimização de Eletropostos'
                    ]
                })
                metadata_df.to_excel(writer, sheet_name='Metadados', index=False)
            
            return self.excel_file
            
        except Exception as e:
            st.error(f"Erro ao exportar para Excel: {e}")
            return None
    
    def exportar_para_csv(self, matriz_distancias: np.ndarray, nomes: List[str]) -> str:
        """
        Exporta matriz de distâncias para CSV
        
        Args:
            matriz_distancias: Matriz NxN de distâncias
            nomes: Lista de nomes dos locais
            
        Returns:
            Caminho do arquivo CSV criado
        """
        try:
            # Criar DataFrame com nomes como índices e colunas
            df = pd.DataFrame(
                matriz_distancias,
                index=nomes,
                columns=nomes
            )
            
            # Salvar como CSV
            df.to_csv(self.csv_file, encoding='utf-8-sig')
            
            return self.csv_file
            
        except Exception as e:
            st.error(f"Erro ao exportar para CSV: {e}")
            return None
    
    def importar_de_excel(self, arquivo_excel) -> Tuple[Optional[np.ndarray], Optional[List[str]]]:
        """
        Importa matriz de distâncias de arquivo Excel
        
        Args:
            arquivo_excel: Arquivo Excel carregado
            
        Returns:
            Tupla (matriz_distancias, nomes) ou (None, None) se erro
        """
        try:
            # Ler arquivo Excel
            df = pd.read_excel(arquivo_excel, sheet_name='Matriz_Distancias', index_col=0)
            
            # Extrair nomes e matriz
            nomes = df.index.tolist()
            matriz_distancias = df.values
            
            # Validar que é uma matriz quadrada
            if matriz_distancias.shape[0] != matriz_distancias.shape[1]:
                st.error("❌ Matriz deve ser quadrada (mesmo número de linhas e colunas)")
                return None, None
            
            # Validar que os nomes das colunas correspondem aos índices
            if not all(df.columns == df.index):
                st.warning("⚠️ Nomes das colunas não correspondem aos índices. Usando índices.")
            
            return matriz_distancias, nomes
            
        except Exception as e:
            st.error(f"❌ Erro ao importar Excel: {e}")
            return None, None
    
    def importar_de_csv(self, arquivo_csv) -> Tuple[Optional[np.ndarray], Optional[List[str]]]:
        """
        Importa matriz de distâncias de arquivo CSV
        
        Args:
            arquivo_csv: Arquivo CSV carregado
            
        Returns:
            Tupla (matriz_distancias, nomes) ou (None, None) se erro
        """
        try:
            # Ler arquivo CSV
            df = pd.read_csv(arquivo_csv, index_col=0, encoding='utf-8-sig')
            
            # Extrair nomes e matriz
            nomes = df.index.tolist()
            matriz_distancias = df.values
            
            # Validar que é uma matriz quadrada
            if matriz_distancias.shape[0] != matriz_distancias.shape[1]:
                st.error("❌ Matriz deve ser quadrada (mesmo número de linhas e colunas)")
                return None, None
            
            return matriz_distancias, nomes
            
        except Exception as e:
            st.error(f"❌ Erro ao importar CSV: {e}")
            return None, None
    
    def salvar_cache_pickle(self, matriz_distancias: np.ndarray, coordenadas: List[Tuple[float, float]]):
        """
        Salva matriz no cache pickle para uso pelo modelo
        
        Args:
            matriz_distancias: Matriz de distâncias
            coordenadas: Coordenadas originais para gerar hash
        """
        try:
            # Gerar hash das coordenadas
            import hashlib
            coords_str = str(sorted(coordenadas))
            coords_hash = hashlib.md5(coords_str.encode()).hexdigest()
            
            # Carregar cache existente ou criar novo
            cache = {}
            if os.path.exists(self.distances_file):
                try:
                    with open(self.distances_file, 'rb') as f:
                        cache = pickle.load(f)
                except:
                    cache = {}
            
            # Adicionar nova matriz ao cache
            cache[coords_hash] = matriz_distancias
            
            # Salvar cache atualizado
            with open(self.distances_file, 'wb') as f:
                pickle.dump(cache, f)
            
            st.success("✅ Matriz salva no cache interno!")
            
        except Exception as e:
            st.error(f"❌ Erro ao salvar no cache: {e}")
    
    def verificar_compatibilidade(self, nomes_arquivo: List[str], nomes_sistema: List[str]) -> bool:
        """
        Verifica se os nomes do arquivo são compatíveis com o sistema
        
        Args:
            nomes_arquivo: Nomes do arquivo importado
            nomes_sistema: Nomes do sistema atual
            
        Returns:
            True se compatível, False caso contrário
        """
        if len(nomes_arquivo) != len(nomes_sistema):
            st.error(f"❌ Número de locais incompatível: arquivo tem {len(nomes_arquivo)}, sistema tem {len(nomes_sistema)}")
            return False
        
        # Verificar se todos os nomes existem (ordem pode ser diferente)
        nomes_arquivo_set = set(nomes_arquivo)
        nomes_sistema_set = set(nomes_sistema)
        
        if nomes_arquivo_set != nomes_sistema_set:
            faltando = nomes_sistema_set - nomes_arquivo_set
            extra = nomes_arquivo_set - nomes_sistema_set
            
            if faltando:
                st.error(f"❌ Locais faltando no arquivo: {', '.join(faltando)}")
            if extra:
                st.error(f"❌ Locais extras no arquivo: {', '.join(extra)}")
            
            return False
        
        return True
    
    def reordenar_matriz(self, matriz_distancias: np.ndarray, nomes_arquivo: List[str], nomes_sistema: List[str]) -> np.ndarray:
        """
        Reordena matriz para corresponder à ordem do sistema
        
        Args:
            matriz_distancias: Matriz original
            nomes_arquivo: Ordem dos nomes no arquivo
            nomes_sistema: Ordem dos nomes no sistema
            
        Returns:
            Matriz reordenada
        """
        # Criar mapeamento de índices
        mapeamento = {}
        for i, nome in enumerate(nomes_arquivo):
            if nome in nomes_sistema:
                mapeamento[i] = nomes_sistema.index(nome)
        
        # Criar nova matriz reordenada
        n = len(nomes_sistema)
        nova_matriz = np.zeros((n, n))
        
        for i_old, i_new in mapeamento.items():
            for j_old, j_new in mapeamento.items():
                nova_matriz[i_new][j_new] = matriz_distancias[i_old][j_old]
        
        return nova_matriz