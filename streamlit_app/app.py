# """
# Dashboard Streamlit para otimização de eletropostos em Campinas - Com Google Maps Seguro
# """

# import streamlit as st
# import folium
# from streamlit_folium import st_folium
# import pandas as pd
# import sys
# import os
# from dotenv import load_dotenv

# # Carregar variáveis de ambiente
# load_dotenv()

# # Adicionar diretório raiz ao path
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# from dados.dados_campinas import obter_dados_campinas, obter_coordenadas_simples, obter_nomes_locais
# from modelos.modelo_multi_objetivo_gmaps import ModeloEletropostosGoogleMaps

# # Configuração da página
# st.set_page_config(
#     page_title="Otimização de Eletropostos",
#     page_icon="⚡",
#     layout="wide",
#     initial_sidebar_state="collapsed"
# )

# # CSS personalizado para design moderno
# st.markdown("""
# <style>
#     /* Tema escuro moderno para sidebar */
#     .css-1d391kg {
#         background: linear-gradient(180deg, #1e3a8a 0%, #1e40af 100%);
#     }
    
#     /* Estilo dos widgets do sidebar */
#     .stSelectbox > div > div {
#         background-color: rgba(255, 255, 255, 0.1);
#         border-radius: 10px;
#         border: 1px solid rgba(255, 255, 255, 0.2);
#     }
    
#     .stSlider > div > div {
#         background-color: rgba(255, 255, 255, 0.1);
#         border-radius: 10px;
#     }
    
#     .stNumberInput > div > div {
#         background-color: rgba(255, 255, 255, 0.1);
#         border-radius: 10px;
#         border: 1px solid rgba(255, 255, 255, 0.2);
#     }
    
#     /* Botões modernos */
#     .stButton > button {
#         background: linear-gradient(45deg, #3b82f6, #1d4ed8);
#         color: white;
#         border: none;
#         border-radius: 25px;
#         padding: 0.5rem 2rem;
#         font-weight: 600;
#         transition: all 0.3s ease;
#         box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
#     }
    
#     .stButton > button:hover {
#         background: linear-gradient(45deg, #1d4ed8, #1e40af);
#         transform: translateY(-2px);
#         box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
#     }
    
#     /* Métricas modernas */
#     .metric-card {
#         background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
#         padding: 1rem;
#         border-radius: 15px;
#         border-left: 4px solid #3b82f6;
#         box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
#         margin: 0.5rem 0;
#     }
    
#     /* Título principal */
#     .main-title {
#         background: linear-gradient(90deg, #1e40af, #3b82f6);
#         -webkit-background-clip: text;
#         -webkit-text-fill-color: transparent;
#         font-size: 3rem;
#         font-weight: 800;
#         text-align: center;
#         margin-bottom: 2rem;
#     }
    
#     /* Container do mapa em tela cheia */
#     .map-container {
#         position: relative;
#         height: 70vh;
#         width: 100%;
#         border-radius: 15px;
#         overflow: hidden;
#         box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
#     }
    
#     # /* Remover padding padrão do Streamlit */
#     # .block-container {
#     #     padding-top: 1rem;
#     #     padding-bottom: 1rem;
#     # }

#     .block-container {
#         padding-top: 1.0rem;     /* ← Margen superior */
#         padding-bottom: 0.0rem;  /* ← Margen inferior */
#         padding-left: 0.5rem;    /* ← Margen izquierdo */
#         padding-right: 0.5rem;   /* ← Margen derecho */
#         max-width: 100%;         /* ← Ancho máximo */ 
#         max-height: 100%;         /* ← Ancho máximo */        
#     }
    
#     /* Estilo para expander */
#     .streamlit-expanderHeader {
#         background: linear-gradient(90deg, #f1f5f9, #e2e8f0);
#         border-radius: 10px;
#         font-weight: 600;
#     }
# </style>
# """, unsafe_allow_html=True)

# def inicializar_sessao():
#     """Inicializa variáveis de sessão"""
#     if 'resultados' not in st.session_state:
#         st.session_state.resultados = {}
#     if 'dados_campinas' not in st.session_state:
#         st.session_state.dados_campinas = obter_dados_campinas()
#     if 'modelo_atual' not in st.session_state:
#         st.session_state.modelo_atual = None

# def obter_google_maps_api_key():
#     """Obtém API key do Google Maps do arquivo .env"""
#     api_key = os.getenv('GOOGLE_MAPS_API_KEY')
#     if api_key and api_key.strip():
#         return api_key.strip()
#     return None

# def criar_sidebar():
#     """Cria sidebar com controles modernos"""
#     with st.sidebar:
#         st.markdown("### ⚙️ Configurações")
                        
#         api_key = obter_google_maps_api_key()
        
#         if api_key:
            
#             usar_google_maps = True
                        
#         else:
#             st.warning("⚠️ API Key não configurada")
#             st.info("""
#             **Para usar Google Maps:**
#             1. Crie arquivo `.env` na raiz do projeto
#             2. Adicione: `GOOGLE_MAPS_API_KEY=sua_chave_aqui`
#             3. Reinicie o dashboard
#             """)
#             usar_google_maps = False
        
                
#         st.markdown("---")
        
#         # Tipo de objetivo
#         tipo_objetivo = st.selectbox(
#             "Estratégia de otimização:",
#             ["minimizar_custo", "maximizar_cobertura", "multi_objetivo"],
#             format_func=lambda x: {
#                 "minimizar_custo": "💰 Minimizar custo",
#                 "maximizar_cobertura": "📊 Maximizar cobertura", 
#                 "multi_objetivo": "⚖️ Multi-objetivo"
#             }[x],
#             help="Escolha a estratégia de otimização desejada"
#         )
        
#         # Parâmetros específicos por tipo
#         orcamento_maximo = None
#         pesos = (0.6, 0.4)
        
#         if tipo_objetivo == "maximizar_cobertura":
#             st.markdown("#### 💰 Restrição orçamentária")
#             orcamento_maximo = st.number_input(
#                 "Orçamento máximo (R$)",
#                 min_value=100000,
#                 max_value=2000000,
#                 value=800000,
#                 step=50000,
#                 format="%d",
#                 help="Orçamento disponível para instalação dos eletropostos"
#             )
            
#         elif tipo_objetivo == "multi_objetivo":
#             st.markdown("#### ⚖️ Balanceamento de objetivos")
#             peso_cobertura = st.slider(
#                 "Prioridade: cobertura vs Custo",
#                 min_value=0.4,
#                 max_value=0.9,
#                 value=0.7,
#                 step=0.1,
#                 format="%.1f",
#                 help="0.4 = Foco no custo | 0.9 = Foco na cobertura"
#             )
#             pesos = (peso_cobertura, 1 - peso_cobertura)
            
#             # Visualização dos pesos
#             col1, col2 = st.columns(2)
#             with col1:
#                 st.metric("📊 Cobertura", f"{peso_cobertura:.1%}")
#             with col2:
#                 st.metric("💰 Custo", f"{1-peso_cobertura:.1%}")
        
#         st.markdown("---")

#         distancia_maxima = 15
        
                      
#         # Botão de otimização
#         if st.button("Executar otimização", use_container_width=True):
#             with st.spinner("Otimizando localização dos eletropostos..."):
#                 executar_otimizacao(tipo_objetivo, orcamento_maximo, pesos, distancia_maxima, usar_google_maps)
        
#         st.markdown("---")
#         st.markdown("#### 📋 Informações")
#         st.info(f"""
#         **Região:** Campinas e Região Metropolitana
        
#         **Localizações:** {len(st.session_state.dados_campinas['coordenadas'])}
        
#         **Demanda total:** {sum(st.session_state.dados_campinas['demandas'])} veículos/dia
        
#         **Investimento máximo:** R$ {sum(st.session_state.dados_campinas['custos_instalacao']):,.0f}
#         """)

# def criar_mapa_campinas(resultados=None):
#     """Cria mapa interativo de Campinas com rotas"""
#     dados = st.session_state.dados_campinas
#     nomes = obter_nomes_locais()
    
#     # Centro do mapa (Campinas)
#     centro_lat = -22.9056
#     centro_lon = -47.0608
    
#     # Criar mapa base
#     m = folium.Map(
#         location=[centro_lat, centro_lon],
#         zoom_start=10,
#         tiles='CartoDB positron',
#         # tiles='CartoDB dark_matter',
#         attr='CartoDB'
#     )
    
#     # Adicionar marcadores de demanda
#     for i, ((lat, lon, nome), demanda, capacidade) in enumerate(zip(
#         dados['coordenadas'], dados['demandas'], dados['capacidades_eletropostos']
#     )):
#         # Cor baseada na demanda
#         if demanda < 60:
#             cor = 'green'
#         elif demanda < 120:
#             cor = 'orange' 
#         else:
#             cor = 'red'
        
#         # Verificar se é um eletroposto selecionado
#         eh_selecionado = resultados and i in resultados.get('localizacoes', [])
        
#         if eh_selecionado:
#             # Eletroposto selecionado - marcador especial
#             folium.Marker(
#                 location=[lat, lon],
#                 popup=folium.Popup(f"""
#                 <div style="width: 200px;">
#                     <h4>⚡ {nome}</h4>
#                     <hr>
#                     <b>Status:</b> ELETROPOSTO INSTALADO<br>
#                     <b>Demanda:</b> {demanda} veículos/dia<br>
#                     <b>Capacidade:</b> {capacidade} veículos/dia<br>
#                     <b>Custo:</b> R$ {dados['custos_instalacao'][i]:,.0f}<br>
#                     <b>Utilização:</b> {(demanda/capacidade*100):.1f}%
#                 </div>
#                 """, max_width=250),
#                 tooltip=f"⚡ {nome} - INSTALADO",
#                 icon=folium.Icon(
#                     color='blue',
#                     icon='bolt',
#                     prefix='fa'
#                 )
#             ).add_to(m)
            
#             # # Círculo de cobertura
#             # folium.Circle(
#             #     location=[lat, lon],
#             #     radius=dados['max_distancia'] * 1000,  # Converter para metros
#             #     popup=f"Área de cobertura: {dados['max_distancia']} km",
#             #     color='blue',
#             #     weight=2,
#             #     fill=True,
#             #     fillColor='lightblue',
#             #     fillOpacity=0.2
#             # ).add_to(m)
            
#         else:
#             # Ponto de demanda normal
#             folium.CircleMarker(
#                 location=[lat, lon],
#                 radius=8 + (demanda / 20),  # Tamanho baseado na demanda
#                 popup=folium.Popup(f"""
#                 <div style="width: 180px;">
#                     <h4>📍 {nome}</h4>
#                     <hr>
#                     <b>Demanda:</b> {demanda} veículos/dia<br>
#                     <b>Capacidade Potencial:</b> {capacidade} veículos/dia<br>
#                     <b>Custo de Instalação:</b> R$ {dados['custos_instalacao'][i]:,.0f}<br>
#                     <b>Eficiência:</b> R$ {dados['custos_instalacao'][i]/capacidade:.0f}/veículo
#                 </div>
#                 """, max_width=220),
#                 tooltip=f"📍 {nome}",
#                 color='darkblue',
#                 weight=2,
#                 fill=True,
#                 fillColor=cor,
#                 fillOpacity=0.7
#             ).add_to(m)
    
#     # Adicionar rotas se disponíveis
#     if resultados and resultados.get('rotas_disponiveis', False):
#         _adicionar_rotas_ao_mapa(m, resultados, dados)
    
#     # Adicionar legenda
#     legenda_html = """
#     <div style="position: fixed; 
#                 top: 10px; right: 10px; width: 220px; height: 180px; 
#                 background-color: white; border:2px solid grey; z-index:9999; 
#                 font-size:14px; padding: 10px; border-radius: 10px;
#                 box-shadow: 0 4px 8px rgba(0,0,0,0.1);">    
#     <p><i class="fa fa-bolt" style="color:blue"></i> Eletroposto instalado</p>
#     <p><i class="fa fa-circle" style="color:green"></i> Baixa demanda (&lt;60)</p>
#     <p><i class="fa fa-circle" style="color:orange"></i> Média demanda (60-120)</p>
#     <p><i class="fa fa-circle" style="color:red"></i> Alta demanda (&gt;120)</p>    
#     <span style="color:#444;">- - Rotas de conexão</span></p>
#     </div>
#     """
#     m.get_root().html.add_child(folium.Element(legenda_html))
    
#     return m

# def _adicionar_rotas_ao_mapa(m, resultados, dados):
#     """Adiciona rotas pontilhadas ao mapa"""
#     if 'rotas' not in resultados:
#         return
    
#     coordenadas = dados['coordenadas']
    
#     for eletroposto_idx, rotas_eletroposto in resultados['rotas'].items():
#         eletroposto_coord = coordenadas[eletroposto_idx]
        
#         for no_idx, pontos_rota in rotas_eletroposto.items():
#             if pontos_rota:
#                 # Adicionar rota pontilhada
#                 folium.PolyLine(
#                     locations=pontos_rota,
#                     color='#666666',
#                     weight=2,
#                     opacity=0.7,
#                     dash_array='10, 10',  # Linha pontilhada
#                     popup=f"Rota: {coordenadas[no_idx][2]} → {eletroposto_coord[2]}"
#                 ).add_to(m)

# def executar_otimizacao(tipo_objetivo, orcamento_maximo, pesos, distancia_maxima, usar_google_maps):
#     """Executa otimização com parâmetros selecionados"""
#     dados = st.session_state.dados_campinas
#     coordenadas_simples = obter_coordenadas_simples()
    
#     try:
#         # Usar API key do arquivo .env se disponível
#         api_key = obter_google_maps_api_key() if usar_google_maps else None
        
#         modelo = ModeloEletropostosGoogleMaps(
#             coordenadas=coordenadas_simples,
#             demandas=dados['demandas'],
#             capacidades_eletropostos=dados['capacidades_eletropostos'],
#             custos_instalacao=dados['custos_instalacao'],
#             distancia_maxima=distancia_maxima,
#             tipo_objetivo=tipo_objetivo,
#             orcamento_maximo=orcamento_maximo,
#             pesos=pesos,
#             google_maps_api_key=api_key
#         )
        
#         if modelo.resolver():
#             # Obter resumo com rotas
#             st.session_state.resultados[tipo_objetivo] = modelo.obter_resumo_com_rotas()
#             st.session_state.modelo_atual = modelo
#             st.success(f"✅ Otimização concluída com sucesso!")
#             st.rerun()
#         else:
#             st.error("❌ Não foi possível encontrar uma solução viável.")
            
#     except Exception as e:
#         st.error(f"❌ Erro durante otimização: {str(e)}")

# def main():
#     """Função principal do dashboard"""
#     inicializar_sessao()
    
#     # Título principal
#     st.markdown('<h1 class="main-title">Otimização de Eletropostos - Campinas</h1>', 
#                 unsafe_allow_html=True)
    
#     # Criar sidebar
#     criar_sidebar()
    
#     # Layout principal
#     if st.session_state.resultados:
#         # Se há resultados, mostrar métricas e mapa
#         resultado_atual = list(st.session_state.resultados.values())[-1]  # Último resultado
        
#         # Métricas principais
#         col1, col2, col3, col4 = st.columns(4)
        
#         with col1:
#             st.metric(
#                 "⚡ Eletropostos",
#                 resultado_atual['eletropostos_instalados'],
#                 help="Número de eletropostos a serem instalados"
#             )
        
#         with col2:
#             st.metric(
#                 "💰 Investimento",
#                 f"R$ {resultado_atual['custo_total']:,.0f}",
#                 help="Custo total de instalação"
#             )
        
#         with col3:
#             st.metric(
#                 "📊 Cobertura",
#                 f"{resultado_atual['cobertura_percentual']:.1f}%",
#                 help="Percentual da demanda atendida"
#             )
        
#         with col4:
#             if resultado_atual['custo_total'] > 0:
#                 eficiencia = resultado_atual['cobertura_total'] / resultado_atual['custo_total'] * 1000
#             else:
#                 eficiencia = 0.0
#             st.metric(
#                 "⚡ Eficiência",
#                 f"{eficiencia:.2f}",
#                 help="Cobertura por mil reais investidos"
#             )
        
        
        
#         # Mapa
#         with st.container():
#             mapa = criar_mapa_campinas(resultado_atual)
#             st_folium(mapa, width=None, height=None, returned_objects=["last_clicked"])
#             # st_folium(mapa, width=1200, height=500, returned_objects=["last_clicked"])
            
#     else:
#         # Se não há resultados, mostrar mapa básico e instruções                
#         with st.container():
#             mapa = criar_mapa_campinas()
#             st_folium(mapa, width=None, height=500)

# if __name__ == "__main__":
#     main()










# """
# Dashboard Streamlit para otimização de eletropostos em Campinas - Com importação/exportação de distâncias
# """

# import streamlit as st
# import folium
# from streamlit_folium import st_folium
# import pandas as pd
# import sys
# import os
# from dotenv import load_dotenv
# import numpy as np

# # Carregar variáveis de ambiente
# load_dotenv()

# # Adicionar diretório raiz ao path
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# from dados.dados_campinas import obter_dados_campinas, obter_coordenadas_simples, obter_nomes_locais
# from modelos.modelo_multi_objetivo_gmaps import ModeloEletropostosGoogleMaps
# from utils.distance_manager import DistanceManager

# # Configuração da página
# st.set_page_config(
#     page_title="Otimização de Eletropostos",
#     page_icon="⚡",
#     layout="wide",
#     initial_sidebar_state="collapsed"
# )

# # CSS personalizado para design moderno
# st.markdown("""
# <style>
#     /* Tema escuro moderno para sidebar */
#     .css-1d391kg {
#         background: linear-gradient(180deg, #1e3a8a 0%, #1e40af 100%);
#     }
    
#     /* Estilo dos widgets do sidebar */
#     .stSelectbox > div > div {
#         background-color: rgba(255, 255, 255, 0.1);
#         border-radius: 10px;
#         border: 1px solid rgba(255, 255, 255, 0.2);
#     }
    
#     .stSlider > div > div {
#         background-color: rgba(255, 255, 255, 0.1);
#         border-radius: 10px;
#     }
    
#     .stNumberInput > div > div {
#         background-color: rgba(255, 255, 255, 0.1);
#         border-radius: 10px;
#         border: 1px solid rgba(255, 255, 255, 0.2);
#     }
    
#     /* Botões modernos */
#     .stButton > button {
#         background: linear-gradient(45deg, #3b82f6, #1d4ed8);
#         color: white;
#         border: none;
#         border-radius: 25px;
#         padding: 0.5rem 2rem;
#         font-weight: 600;
#         transition: all 0.3s ease;
#         box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
#     }
    
#     .stButton > button:hover {
#         background: linear-gradient(45deg, #1d4ed8, #1e40af);
#         transform: translateY(-2px);
#         box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
#     }
    
#     /* Métricas modernas */
#     .metric-card {
#         background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
#         padding: 1rem;
#         border-radius: 15px;
#         border-left: 4px solid #3b82f6;
#         box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
#         margin: 0.5rem 0;
#     }
    
#     /* Título principal */
#     .main-title {
#         background: linear-gradient(90deg, #1e40af, #3b82f6);
#         -webkit-background-clip: text;
#         -webkit-text-fill-color: transparent;
#         font-size: 3rem;
#         font-weight: 800;
#         text-align: center;
#         margin-bottom: 2rem;
#     }
    
#     /* Container do mapa em tela cheia */
#     .map-container {
#         position: relative;
#         height: 70vh;
#         width: 100%;
#         border-radius: 15px;
#         overflow: hidden;
#         box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
#     }
    
#     /* Remover padding padrão do Streamlit */
#     .block-container {
#         padding-top: 1.0rem;
#         padding-bottom: 0.5rem;
#         padding-left: 0.5rem;
#         padding-right: 0.5rem;
#         max-width: 100%;
#     }

 
    
#     /* Estilo para expander */
#     .streamlit-expanderHeader {
#         background: linear-gradient(90deg, #f1f5f9, #e2e8f0);
#         border-radius: 10px;
#         font-weight: 600;
#     }
# </style>
# """, unsafe_allow_html=True)

# def inicializar_sessao():
#     """Inicializa variáveis de sessão"""
#     if 'resultados' not in st.session_state:
#         st.session_state.resultados = {}
#     if 'dados_campinas' not in st.session_state:
#         st.session_state.dados_campinas = obter_dados_campinas()
#     if 'modelo_atual' not in st.session_state:
#         st.session_state.modelo_atual = None
#     if 'matriz_distancias_customizada' not in st.session_state:
#         st.session_state.matriz_distancias_customizada = None
#     if 'usar_matriz_customizada' not in st.session_state:
#         st.session_state.usar_matriz_customizada = False

# def obter_google_maps_api_key():
#     """Obtém API key do Google Maps do arquivo .env"""
#     api_key = os.getenv('GOOGLE_MAPS_API_KEY')
#     if api_key and api_key.strip():
#         return api_key.strip()
#     return None

# def criar_sidebar():
#     """Cria sidebar com controles modernos"""
#     with st.sidebar:
#         st.markdown("### ⚙️ Configurações")
        
#         # === SEÇÃO DE DISTÂNCIAS ===
#         st.markdown("#### 📏 Gerenciamento de Distâncias")
        
#         # Opções de fonte de distâncias
#         fonte_distancias = st.radio(
#             "Fonte das distâncias:",
#             ["google_maps", "euclidiana", "arquivo_personalizado"],
#             format_func=lambda x: {
#                 "google_maps": "🗺️ Google Maps (API)",
#                 "euclidiana": "📐 Euclidiana (Haversine)",
#                 "arquivo_personalizado": "📁 Arquivo personalizado"
#             }[x],
#             help="Escolha como calcular as distâncias entre locais"
#         )
        
#         usar_google_maps = False
#         usar_matriz_customizada = False
        
#         if fonte_distancias == "google_maps":
#             api_key = obter_google_maps_api_key()
#             if api_key:
#                 st.success("✅ API Key configurada")
#                 usar_google_maps = True
#             else:
#                 st.error("❌ API Key não configurada no arquivo .env")
#                 st.info("Usando distâncias euclidianas como fallback")
                
#         elif fonte_distancias == "arquivo_personalizado":
#             usar_matriz_customizada = True
            
#             # Upload de arquivo
#             uploaded_file = st.file_uploader(
#                 "Carregar matriz de distâncias:",
#                 type=['xlsx', 'csv'],
#                 help="Arquivo Excel (.xlsx) ou CSV (.csv) com matriz de distâncias"
#             )
            
#             if uploaded_file is not None:
#                 processar_arquivo_distancias(uploaded_file)
            
#             # Mostrar status da matriz customizada
#             if st.session_state.matriz_distancias_customizada is not None:
#                 st.success("✅ Matriz personalizada carregada")
#                 st.session_state.usar_matriz_customizada = True
#             else:
#                 st.warning("⚠️ Nenhuma matriz personalizada carregada")
#                 st.session_state.usar_matriz_customizada = False
        
#         # === SEÇÃO DE EXPORTAÇÃO ===
#         with st.expander("📤 Exportar Distâncias"):
#             st.markdown("**Gerar matriz de distâncias para edição:**")
            
#             col1, col2 = st.columns(2)
            
#             with col1:
#                 if st.button("📊 Gerar Excel", use_container_width=True):
#                     gerar_arquivo_distancias("excel")
            
#             with col2:
#                 if st.button("📄 Gerar CSV", use_container_width=True):
#                     gerar_arquivo_distancias("csv")
            
#             st.info("""
#             **Como usar:**
#             1. Clique em 'Gerar Excel' ou 'Gerar CSV'
#             2. Baixe o arquivo gerado
#             3. Edite as distâncias conforme necessário
#             4. Carregue o arquivo editado acima
#             """)
        
#         st.markdown("---")
        
#         # === SEÇÃO DE OTIMIZAÇÃO ===
#         st.markdown("#### 🎯 Configurações de Otimização")
        
#         # Tipo de objetivo
#         tipo_objetivo = st.selectbox(
#             "Estratégia de otimização:",
#             ["minimizar_custo", "maximizar_cobertura", "multi_objetivo"],
#             format_func=lambda x: {
#                 "minimizar_custo": "💰 Minimizar custo",
#                 "maximizar_cobertura": "📊 Maximizar cobertura", 
#                 "multi_objetivo": "⚖️ Multi-objetivo"
#             }[x],
#             help="Escolha a estratégia de otimização desejada"
#         )
        
#         # Parâmetros específicos por tipo
#         orcamento_maximo = None
#         pesos = (0.6, 0.4)
        
#         if tipo_objetivo == "maximizar_cobertura":
#             st.markdown("#### 💰 Restrição orçamentária")
#             orcamento_maximo = st.number_input(
#                 "Orçamento máximo (R$)",
#                 min_value=100000,
#                 max_value=2000000,
#                 value=800000,
#                 step=50000,
#                 format="%d",
#                 help="Orçamento disponível para instalação dos eletropostos"
#             )
            
#         elif tipo_objetivo == "multi_objetivo":
#             st.markdown("#### ⚖️ Balanceamento de objetivos")
#             peso_cobertura = st.slider(
#                 "Prioridade: cobertura vs Custo",
#                 min_value=0.4,
#                 max_value=0.9,
#                 value=0.7,
#                 step=0.1,
#                 format="%.1f",
#                 help="0.4 = Foco no custo | 0.9 = Foco na cobertura"
#             )
#             pesos = (peso_cobertura, 1 - peso_cobertura)
            
#             # Visualização dos pesos
#             col1, col2 = st.columns(2)
#             with col1:
#                 st.metric("📊 Cobertura", f"{peso_cobertura:.1%}")
#             with col2:
#                 st.metric("💰 Custo", f"{1-peso_cobertura:.1%}")
        
#         st.markdown("---")

#         # Distância máxima
#         distancia_maxima = st.slider(
#             "Distância máxima de atendimento (km)",
#             min_value=5,
#             max_value=25,
#             value=15,
#             step=1,
#             help="Distância máxima que um eletroposto pode atender"
#         )
        
#         # Botão de otimização
#         if st.button("🚀 Executar otimização", use_container_width=True):
#             with st.spinner("Otimizando localização dos eletropostos..."):
#                 executar_otimizacao(
#                     tipo_objetivo, 
#                     orcamento_maximo, 
#                     pesos, 
#                     distancia_maxima, 
#                     usar_google_maps,
#                     st.session_state.usar_matriz_customizada
#                 )
        
#         st.markdown("---")
        
#         # === SEÇÃO DE INFORMAÇÕES ===
#         st.markdown("#### 📋 Informações")
        
#         # Status da fonte de distâncias
#         if st.session_state.usar_matriz_customizada:
#             st.info("📁 Usando matriz personalizada")
#         elif usar_google_maps:
#             st.info("🗺️ Usando Google Maps API")
#         else:
#             st.info("📐 Usando distâncias euclidianas")
        
#         # Informações gerais
#         st.info(f"""
#         **Região:** Campinas e Região Metropolitana
        
#         **Localizações:** {len(st.session_state.dados_campinas['coordenadas'])}
        
#         **Demanda total:** {sum(st.session_state.dados_campinas['demandas'])} veículos/dia
        
#         **Investimento máximo:** R$ {sum(st.session_state.dados_campinas['custos_instalacao']):,.0f}
#         """)

# def processar_arquivo_distancias(uploaded_file):
#     """Processa arquivo de distâncias carregado"""
#     try:
#         distance_manager = DistanceManager()
#         nomes_sistema = [coord[2] for coord in st.session_state.dados_campinas['coordenadas']]
        
#         # Determinar tipo de arquivo e importar
#         if uploaded_file.name.endswith('.xlsx'):
#             matriz_distancias, nomes_arquivo = distance_manager.importar_de_excel(uploaded_file)
#         elif uploaded_file.name.endswith('.csv'):
#             matriz_distancias, nomes_arquivo = distance_manager.importar_de_csv(uploaded_file)
#         else:
#             st.error("❌ Formato de arquivo não suportado. Use .xlsx ou .csv")
#             return
        
#         if matriz_distancias is None or nomes_arquivo is None:
#             return
        
#         # Verificar compatibilidade
#         if not distance_manager.verificar_compatibilidade(nomes_arquivo, nomes_sistema):
#             return
        
#         # Reordenar matriz se necessário
#         if nomes_arquivo != nomes_sistema:
#             st.info("🔄 Reordenando matriz para corresponder à ordem do sistema...")
#             matriz_distancias = distance_manager.reordenar_matriz(
#                 matriz_distancias, nomes_arquivo, nomes_sistema
#             )
        
#         # Salvar matriz customizada
#         st.session_state.matriz_distancias_customizada = matriz_distancias
        
#         # Salvar no cache para uso pelo modelo
#         coordenadas_simples = obter_coordenadas_simples()
#         distance_manager.salvar_cache_pickle(matriz_distancias, coordenadas_simples)
        
#         st.success(f"✅ Matriz de distâncias carregada com sucesso! ({len(nomes_arquivo)} locais)")
        
#         # Mostrar estatísticas
#         with st.expander("📊 Estatísticas da Matriz"):
#             col1, col2, col3 = st.columns(3)
#             with col1:
#                 st.metric("Locais", len(nomes_arquivo))
#             with col2:
#                 st.metric("Distância Média", f"{np.mean(matriz_distancias):.1f} km")
#             with col3:
#                 st.metric("Distância Máxima", f"{np.max(matriz_distancias):.1f} km")
        
#     except Exception as e:
#         st.error(f"❌ Erro ao processar arquivo: {e}")

# def gerar_arquivo_distancias(formato):
#     """Gera arquivo de distâncias para download"""
#     try:
#         distance_manager = DistanceManager()
#         coordenadas_simples = obter_coordenadas_simples()
#         nomes = [coord[2] for coord in st.session_state.dados_campinas['coordenadas']]
        
#         with st.spinner("Calculando distâncias euclidianas..."):
#             # Calcular matriz euclidiana
#             matriz_distancias = distance_manager.calcular_matriz_euclidiana(
#                 coordenadas_simples, nomes
#             )
        
#         if formato == "excel":
#             arquivo_path = distance_manager.exportar_para_excel(matriz_distancias, nomes)
#             if arquivo_path:
#                 # Ler arquivo para download
#                 with open(arquivo_path, 'rb') as f:
#                     st.download_button(
#                         label="⬇️ Baixar arquivo Excel",
#                         data=f.read(),
#                         file_name="matriz_distancias_campinas.xlsx",
#                         mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#                     )
#                 st.success("✅ Arquivo Excel gerado com sucesso!")
        
#         elif formato == "csv":
#             arquivo_path = distance_manager.exportar_para_csv(matriz_distancias, nomes)
#             if arquivo_path:
#                 # Ler arquivo para download
#                 with open(arquivo_path, 'r', encoding='utf-8-sig') as f:
#                     st.download_button(
#                         label="⬇️ Baixar arquivo CSV",
#                         data=f.read(),
#                         file_name="matriz_distancias_campinas.csv",
#                         mime="text/csv"
#                     )
#                 st.success("✅ Arquivo CSV gerado com sucesso!")
        
#     except Exception as e:
#         st.error(f"❌ Erro ao gerar arquivo: {e}")

# def criar_mapa_campinas(resultados=None):
#     """Cria mapa interativo de Campinas com rotas"""
#     dados = st.session_state.dados_campinas
#     nomes = obter_nomes_locais()
    
#     # Centro do mapa (Campinas)
#     centro_lat = -22.9056
#     centro_lon = -47.0608
    
#     # Criar mapa base - modo escuro
#     m = folium.Map(
#         location=[centro_lat, centro_lon],
#         zoom_start=10,
#         tiles='CartoDB positron',
#         # tiles='CartoDB dark_matter',  # Modo oscuro
#         attr='CartoDB'
#     )
    
#     # Adicionar marcadores de demanda
#     for i, ((lat, lon, nome), demanda, capacidade) in enumerate(zip(
#         dados['coordenadas'], dados['demandas'], dados['capacidades_eletropostos']
#     )):
#         # Cor baseada na demanda
#         if demanda < 60:
#             cor = 'green'
#         elif demanda < 120:
#             cor = 'orange' 
#         else:
#             cor = 'red'
        
#         # Verificar se é um eletroposto selecionado
#         eh_selecionado = resultados and i in resultados.get('localizacoes', [])
        
#         if eh_selecionado:
#             # Eletroposto selecionado - marcador especial
#             folium.Marker(
#                 location=[lat, lon],
#                 popup=folium.Popup(f"""
#                 <div style="width: 200px;">
#                     <h4>⚡ {nome}</h4>
#                     <hr>
#                     <b>Status:</b> ELETROPOSTO INSTALADO<br>
#                     <b>Demanda:</b> {demanda} veículos/dia<br>
#                     <b>Capacidade:</b> {capacidade} veículos/dia<br>
#                     <b>Custo:</b> R$ {dados['custos_instalacao'][i]:,.0f}<br>
#                     <b>Utilização:</b> {(demanda/capacidade*100):.1f}%
#                 </div>
#                 """, max_width=250),
#                 tooltip=f"⚡ {nome} - INSTALADO",
#                 icon=folium.Icon(
#                     color='blue',
#                     icon='bolt',
#                     prefix='fa'
#                 )
#             ).add_to(m)
            
#         else:
#             # Ponto de demanda normal
#             folium.CircleMarker(
#                 location=[lat, lon],
#                 radius=8 + (demanda / 20),  # Tamanho baseado na demanda
#                 popup=folium.Popup(f"""
#                 <div style="width: 180px;">
#                     <h4>📍 {nome}</h4>
#                     <hr>
#                     <b>Demanda:</b> {demanda} veículos/dia<br>
#                     <b>Capacidade Potencial:</b> {capacidade} veículos/dia<br>
#                     <b>Custo de Instalação:</b> R$ {dados['custos_instalacao'][i]:,.0f}<br>
#                     <b>Eficiência:</b> R$ {dados['custos_instalacao'][i]/capacidade:.0f}/veículo
#                 </div>
#                 """, max_width=220),
#                 tooltip=f"📍 {nome}",
#                 color='white',
#                 weight=2,
#                 fill=True,
#                 fillColor=cor,
#                 fillOpacity=0.7
#             ).add_to(m)
    
#     # Adicionar rotas se disponíveis
#     if resultados and resultados.get('rotas_disponiveis', False):
#         _adicionar_rotas_ao_mapa(m, resultados, dados)
    
#     # Adicionar legenda - versão escura
#     legenda_html = """
#     <div style="position: fixed; 
#                 top: 10px; right: 10px; width: 220px; height: 180px; 
#                 background-color: #2d3748; border:2px solid #4a5568; z-index:9999; 
#                 font-size:14px; padding: 10px; border-radius: 10px;
#                 box-shadow: 0 4px 8px rgba(0,0,0,0.3); color: white;">    
#     <p><i class="fa fa-bolt" style="color:#60a5fa"></i> Eletroposto instalado</p>
#     <p><i class="fa fa-circle" style="color:green"></i> Baixa demanda (&lt;60)</p>
#     <p><i class="fa fa-circle" style="color:orange"></i> Média demanda (60-120)</p>
#     <p><i class="fa fa-circle" style="color:red"></i> Alta demanda (&gt;120)</p>    
#     <span style="color:#cbd5e0;">- - Rotas de conexão</span></p>
#     </div>
#     """
#     m.get_root().html.add_child(folium.Element(legenda_html))
    
#     return m

# def _adicionar_rotas_ao_mapa(m, resultados, dados):
#     """Adiciona rotas pontilhadas ao mapa"""
#     if 'rotas' not in resultados:
#         return
    
#     coordenadas = dados['coordenadas']
    
#     for eletroposto_idx, rotas_eletroposto in resultados['rotas'].items():
#         eletroposto_coord = coordenadas[eletroposto_idx]
        
#         for no_idx, pontos_rota in rotas_eletroposto.items():
#             if pontos_rota:
#                 # Adicionar rota pontilhada
#                 folium.PolyLine(
#                     locations=pontos_rota,
#                     color='#fbbf24',  # Amarelo para modo escuro
#                     weight=2,
#                     opacity=0.8,
#                     dash_array='10, 10',  # Linha pontilhada
#                     popup=f"Rota: {coordenadas[no_idx][2]} → {eletroposto_coord[2]}"
#                 ).add_to(m)

# def executar_otimizacao(tipo_objetivo, orcamento_maximo, pesos, distancia_maxima, usar_google_maps, usar_matriz_customizada):
#     """Executa otimização com parâmetros selecionados"""
#     dados = st.session_state.dados_campinas
#     coordenadas_simples = obter_coordenadas_simples()
    
#     try:
#         # Determinar API key
#         api_key = None
#         if usar_google_maps and not usar_matriz_customizada:
#             api_key = obter_google_maps_api_key()
        
#         modelo = ModeloEletropostosGoogleMaps(
#             coordenadas=coordenadas_simples,
#             demandas=dados['demandas'],
#             capacidades_eletropostos=dados['capacidades_eletropostos'],
#             custos_instalacao=dados['custos_instalacao'],
#             distancia_maxima=distancia_maxima,
#             tipo_objetivo=tipo_objetivo,
#             orcamento_maximo=orcamento_maximo,
#             pesos=pesos,
#             google_maps_api_key=api_key
#         )
        
#         if modelo.resolver():
#             # Obter resumo com rotas
#             st.session_state.resultados[tipo_objetivo] = modelo.obter_resumo_com_rotas()
#             st.session_state.modelo_atual = modelo
#             st.success(f"✅ Otimização concluída com sucesso!")
#             st.rerun()
#         else:
#             st.error("❌ Não foi possível encontrar uma solução viável.")
            
#     except Exception as e:
#         st.error(f"❌ Erro durante otimização: {str(e)}")

# def main():
#     """Função principal do dashboard"""
#     inicializar_sessao()
    
#     # Título principal
#     st.markdown('<h1 class="main-title">Otimização de Eletropostos - Campinas</h1>', 
#                 unsafe_allow_html=True)
    
#     # Criar sidebar
#     criar_sidebar()
    
#     # Layout principal
#     if st.session_state.resultados:
#         # Se há resultados, mostrar métricas e mapa
#         resultado_atual = list(st.session_state.resultados.values())[-1]  # Último resultado
        
#         # Métricas principais
#         col1, col2, col3, col4 = st.columns(4)
        
#         with col1:
#             st.metric(
#                 "⚡ Eletropostos",
#                 resultado_atual['eletropostos_instalados'],
#                 help="Número de eletropostos a serem instalados"
#             )
        
#         with col2:
#             st.metric(
#                 "💰 Investimento",
#                 f"R$ {resultado_atual['custo_total']:,.0f}",
#                 help="Custo total de instalação"
#             )
        
#         with col3:
#             st.metric(
#                 "📊 Cobertura",
#                 f"{resultado_atual['cobertura_percentual']:.1f}%",
#                 help="Percentual da demanda atendida"
#             )
        
#         with col4:
#             if resultado_atual['custo_total'] > 0:
#                 eficiencia = resultado_atual['cobertura_total'] / resultado_atual['custo_total'] * 1000
#             else:
#                 eficiencia = 0.0
#             st.metric(
#                 "⚡ Eficiência",
#                 f"{eficiencia:.2f}",
#                 help="Cobertura por mil reais investidos"
#             )
        
#         # Mapa
#         with st.container():
#             mapa = criar_mapa_campinas(resultado_atual)
#             st_folium(mapa, width=1200, height=650, returned_objects=["last_clicked"])
            
#     else:
#         # Se não há resultados, mostrar mapa básico e instruções                
#         with st.container():
#             mapa = criar_mapa_campinas()
#             st_folium(mapa, width=1200, height=650)

# if __name__ == "__main__":
#     main()






"""
Dashboard Streamlit para otimização de eletropostos em Campinas - Com Google Maps Seguro
"""

import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import sys
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Adicionar diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dados.dados_campinas import obter_dados_campinas, obter_coordenadas_simples, obter_nomes_locais
from modelos.modelo_multi_objetivo_gmaps import ModeloEletropostosGoogleMaps

# Configuração da página
st.set_page_config(
    page_title="Otimização de Eletropostos",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS personalizado para design moderno
st.markdown("""
<style>
    /* Tema escuro moderno para sidebar */
    .css-1d391kg {
        background: linear-gradient(180deg, #1e3a8a 0%, #1e40af 100%);
    }
    
    /* Estilo dos widgets do sidebar */
    .stSelectbox > div > div {
        background-color: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    .stSlider > div > div {
        background-color: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
    }
    
    .stNumberInput > div > div {
        background-color: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    /* Botões modernos */
    .stButton > button {
        background: linear-gradient(45deg, #3b82f6, #1d4ed8);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.5rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
    }
    
    .stButton > button:hover {
        background: linear-gradient(45deg, #1d4ed8, #1e40af);
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
    }
    
    /* Métricas modernas */
    .metric-card {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        padding: 1rem;
        border-radius: 15px;
        border-left: 4px solid #3b82f6;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 0.5rem 0;
    }
    
    /* Título principal */
    .main-title {
        background: linear-gradient(90deg, #1e40af, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* Container do mapa em tela cheia */
    .map-container {
        position: relative;
        height: 70vh;
        width: 100%;
        border-radius: 15px;
        overflow: hidden;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    }
    
    /* Remover padding padrão do Streamlit */
    .block-container {
        padding-top: 1.0rem;
        padding-bottom: 0.0rem;
        padding-left: 0.5rem;
        padding-right: 0.5rem;
        max-width: 100%;
        max-height: 100%;
    }
    
    /* Estilo para expander */
    .streamlit-expanderHeader {
        background: linear-gradient(90deg, #f1f5f9, #e2e8f0);
        border-radius: 10px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

def inicializar_sessao():
    """Inicializa variáveis de sessão"""
    if 'resultados' not in st.session_state:
        st.session_state.resultados = {}
    if 'dados_campinas' not in st.session_state:
        st.session_state.dados_campinas = obter_dados_campinas()
    if 'modelo_atual' not in st.session_state:
        st.session_state.modelo_atual = None

def obter_google_maps_api_key():
    """Obtém API key do Google Maps do arquivo .env"""
    api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    if api_key and api_key.strip():
        return api_key.strip()
    return None

def criar_sidebar():
    """Cria sidebar com controles modernos"""
    with st.sidebar:
        st.markdown("### ⚙️ Configurações")
        
                
        api_key = obter_google_maps_api_key()
        
        if api_key:
            
            usar_google_maps = True
            
            # # Botão para limpar cache
            # if st.button("Limpar Cache Google Maps", help="Remove cache de distâncias e rotas"):
            #     try:
            #         from utils.google_maps_cache import GoogleMapsCache
            #         cache = GoogleMapsCache(api_key)
            #         cache.limpar_cache()
            #     except Exception as e:
            #         st.error(f"Erro ao limpar cache: {e}")
        else:
            st.warning("⚠️ API Key não configurada")
            st.info("""
            **Para usar Google Maps:**
            1. Crie arquivo `.env` na raiz do projeto
            2. Adicione: `GOOGLE_MAPS_API_KEY=sua_chave_aqui`
            3. Reinicie o dashboard
            """)
            usar_google_maps = False
        
        
               
        # Tipo de objetivo
        tipo_objetivo = st.selectbox(
            "Estratégia de otimização:",
            ["minimizar_custo", "maximizar_cobertura", "multi_objetivo"],
            format_func=lambda x: {
                "minimizar_custo": "💰 Minimizar custo",
                "maximizar_cobertura": "📊 Maximizar cobertura", 
                "multi_objetivo": "⚖️ Multi-objetivo"
            }[x],
            help="Escolha a estratégia de otimização desejada"
        )
        
        # Parâmetros específicos por tipo
        orcamento_maximo = None
        pesos = (0.6, 0.4)
        
        if tipo_objetivo == "maximizar_cobertura":
            st.markdown("#### 💰 Restrição orçamentária")
            orcamento_maximo = st.number_input(
                "Orçamento máximo (R$)",
                min_value=100000,
                max_value=2000000,
                value=800000,
                step=50000,
                format="%d",
                help="Orçamento disponível para instalação dos eletropostos"
            )
            
        elif tipo_objetivo == "multi_objetivo":
            st.markdown("#### ⚖️ Balanceamento de objetivos")
            peso_cobertura = st.slider(
                "Prioridade: cobertura vs Custo",
                min_value=0.4,
                max_value=0.9,
                value=0.7,
                step=0.1,
                format="%.1f",
                help="0.4 = Foco no custo | 0.9 = Foco na cobertura"
            )
            pesos = (peso_cobertura, 1 - peso_cobertura)
            
            # Visualização dos pesos
            col1, col2 = st.columns(2)
            with col1:
                st.metric("📊 Cobertura", f"{peso_cobertura:.1%}")
            with col2:
                st.metric("💰 Custo", f"{1-peso_cobertura:.1%}")
        
        st.markdown("---")
        

        distancia_maxima=15
        
        
        # Botão de otimização
        if st.button("Executar otimização", use_container_width=True):
            with st.spinner("Otimizando localização dos eletropostos..."):
                executar_otimizacao(tipo_objetivo, orcamento_maximo, pesos, distancia_maxima, usar_google_maps)
        
        st.markdown("---")
        st.markdown("#### 📋 Informações")
        st.info(f"""
        **Região:** Campinas e Região Metropolitana
        
        **Localizações:** {len(st.session_state.dados_campinas['coordenadas'])}
        
        **Demanda total:** {sum(st.session_state.dados_campinas['demandas'])} veículos/dia
        
        **Investimento máximo:** R$ {sum(st.session_state.dados_campinas['custos_instalacao']):,.0f}
        """)

def criar_mapa_campinas(resultados=None):
    """Cria mapa interativo de Campinas com rotas"""
    dados = st.session_state.dados_campinas
    nomes = obter_nomes_locais()
    
    # Centro do mapa (Campinas)
    centro_lat = -22.9056
    centro_lon = -47.0608
    
    # Criar mapa base
    m = folium.Map(
        location=[centro_lat, centro_lon],
        zoom_start=10,
        tiles='CartoDB positron',
        attr='CartoDB'
    )
    
    # Adicionar marcadores de demanda
    for i, ((lat, lon, nome), demanda, capacidade) in enumerate(zip(
        dados['coordenadas'], dados['demandas'], dados['capacidades_eletropostos']
    )):
        # Cor baseada na demanda
        if demanda < 60:
            cor = 'green'
        elif demanda < 120:
            cor = 'orange' 
        else:
            cor = 'red'
        
        # Verificar se é um eletroposto selecionado
        eh_selecionado = resultados and i in resultados.get('localizacoes', [])
        
        if eh_selecionado:
            # Eletroposto selecionado - marcador especial
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(f"""
                <div style="width: 200px;">
                    <h4>⚡ {nome}</h4>
                    <hr>
                    <b>Status:</b> ELETROPOSTO INSTALADO<br>
                    <b>Demanda:</b> {demanda} veículos/dia<br>
                    <b>Capacidade:</b> {capacidade} veículos/dia<br>
                    <b>Custo:</b> R$ {dados['custos_instalacao'][i]:,.0f}<br>
                    <b>Utilização:</b> {(demanda/capacidade*100):.1f}%
                </div>
                """, max_width=250),
                tooltip=f"⚡ {nome} - INSTALADO",
                icon=folium.Icon(
                    color='blue',
                    icon='bolt',
                    prefix='fa'
                )
            ).add_to(m)
            
        else:
            # Ponto de demanda normal
            folium.CircleMarker(
                location=[lat, lon],
                radius=8 + (demanda / 20),  # Tamanho baseado na demanda
                popup=folium.Popup(f"""
                <div style="width: 180px;">
                    <h4>📍 {nome}</h4>
                    <hr>
                    <b>Demanda:</b> {demanda} veículos/dia<br>
                    <b>Capacidade Potencial:</b> {capacidade} veículos/dia<br>
                    <b>Custo de Instalação:</b> R$ {dados['custos_instalacao'][i]:,.0f}<br>
                    <b>Eficiência:</b> R$ {dados['custos_instalacao'][i]/capacidade:.0f}/veículo
                </div>
                """, max_width=220),
                tooltip=f"📍 {nome}",
                color='darkblue',
                weight=2,
                fill=True,
                fillColor=cor,
                fillOpacity=0.7
            ).add_to(m)
    
    # Adicionar rotas se disponíveis
    if resultados and resultados.get('rotas_disponiveis', False):
        _adicionar_rotas_ao_mapa(m, resultados, dados)
    
    # Adicionar legenda
    legenda_html = """
    <div style="position: fixed; 
                top: 10px; right: 10px; width: 220px; height: 180px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px; border-radius: 10px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);">    
    <p><i class="fa fa-bolt" style="color:blue"></i> Eletroposto instalado</p>
    <p><i class="fa fa-circle" style="color:green"></i> Baixa demanda (&lt;60)</p>
    <p><i class="fa fa-circle" style="color:orange"></i> Média demanda (60-120)</p>
    <p><i class="fa fa-circle" style="color:red"></i> Alta demanda (&gt;120)</p>    
    <span style="color:#444;">- - Rotas de conexão</span></p>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legenda_html))
    
    return m

def _adicionar_rotas_ao_mapa(m, resultados, dados):
    """Adiciona rotas pontilhadas ao mapa"""
    if 'rotas' not in resultados:
        return
    
    coordenadas = dados['coordenadas']
    
    for eletroposto_idx, rotas_eletroposto in resultados['rotas'].items():
        eletroposto_coord = coordenadas[eletroposto_idx]
        
        for no_idx, pontos_rota in rotas_eletroposto.items():
            if pontos_rota:
                # Adicionar rota pontilhada
                folium.PolyLine(
                    locations=pontos_rota,
                    color='#666666',
                    weight=2,
                    opacity=0.7,
                    dash_array='10, 10',  # Linha pontilhada
                    popup=f"Rota: {coordenadas[no_idx][2]} → {eletroposto_coord[2]}"
                ).add_to(m)

def executar_otimizacao(tipo_objetivo, orcamento_maximo, pesos, distancia_maxima, usar_google_maps):
    """Executa otimização com parâmetros selecionados"""
    dados = st.session_state.dados_campinas
    coordenadas_simples = obter_coordenadas_simples()
    
    try:
        # Usar API key do arquivo .env se disponível
        api_key = obter_google_maps_api_key() if usar_google_maps else None
        
        modelo = ModeloEletropostosGoogleMaps(
            coordenadas=coordenadas_simples,
            demandas=dados['demandas'],
            capacidades_eletropostos=dados['capacidades_eletropostos'],
            custos_instalacao=dados['custos_instalacao'],
            distancia_maxima=distancia_maxima,
            tipo_objetivo=tipo_objetivo,
            orcamento_maximo=orcamento_maximo,
            pesos=pesos,
            google_maps_api_key=api_key
        )
        
        if modelo.resolver():
            # Obter resumo com rotas
            st.session_state.resultados[tipo_objetivo] = modelo.obter_resumo_com_rotas()
            st.session_state.modelo_atual = modelo
            st.success(f"✅ Otimização concluída com sucesso!")
            st.rerun()
        else:
            st.error("❌ Não foi possível encontrar uma solução viável.")
            
    except Exception as e:
        st.error(f"❌ Erro durante otimização: {str(e)}")

def main():
    """Função principal do dashboard"""
    inicializar_sessao()
    
    # Título principal
    st.markdown('<h1 class="main-title">Otimização de Eletropostos - Campinas</h1>', 
                unsafe_allow_html=True)
    
    # Criar sidebar
    criar_sidebar()
    
    # Layout principal
    if st.session_state.resultados:
        # Se há resultados, mostrar métricas e mapa
        resultado_atual = list(st.session_state.resultados.values())[-1]  # Último resultado
        
        # Métricas principais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "⚡ Eletropostos",
                resultado_atual['eletropostos_instalados'],
                help="Número de eletropostos a serem instalados"
            )
        
        with col2:
            st.metric(
                "💰 Investimento",
                f"R$ {resultado_atual['custo_total']:,.0f}",
                help="Custo total de instalação"
            )
        
        with col3:
            st.metric(
                "📊 Cobertura",
                f"{resultado_atual['cobertura_percentual']:.1f}%",
                help="Percentual da demanda atendida"
            )
        
        with col4:
            if resultado_atual['custo_total'] > 0:
                eficiencia = resultado_atual['cobertura_total'] / resultado_atual['custo_total'] * 1000
            else:
                eficiencia = 0.0
            st.metric(
                "⚡ Eficiência",
                f"{eficiencia:.2f}",
                help="Cobertura por mil reais investidos"
            )
        
        
        
        # Mapa
        with st.container():
            mapa = criar_mapa_campinas(resultado_atual)
            st_folium(mapa, width=None, height=580, returned_objects=["last_clicked"])            
            # st_folium(mapa, width=1200, height=650, returned_objects=["last_clicked"])
            
    else:
        # Se não há resultados, mostrar mapa básico e instruções                
        with st.container():
            mapa = criar_mapa_campinas()
            st_folium(mapa, width=None, height=650)

if __name__ == "__main__":
    main()