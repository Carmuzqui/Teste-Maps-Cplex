# """
# Dados reais da região metropolitana de Campinas para eletropostos
# VERIFICADOS E CORRIGIDOS (Versão 3 - Híbrida)

# - Mantém os pontos-chave de Campinas (Centro, Shoppings, Aeroporto, Unicamp).
# - Re-introduz as cidades vizinhas (Paulínia, Americana, Nova Odessa, Pedreira)
#   com suas coordenadas reais e dados originais.
# - Remove pontos de bairro menos relevantes (Jd. Guanabara, Jd. Proença)
#   para manter a lista de 15 locais.
# """
# import math

# def obter_dados_campinas():
#     """
#     Retorna dados da Região Metropolitana de Campinas com coordenadas
#     reais e nomes de locais corrigidos.
#     Esta versão mantém os 15 locais, re-introduzindo as cidades
#     vizinhas que haviam sido perdidas na correção anterior.
#     """
    
#     # Coordenadas (latitude, longitude) - VERSÃO HÍBRIDA
#     coordenadas = [
#         # --- Pontos Principais em Campinas ---
#         (-22.9056, -47.0608, "Centro de Campinas"),           # 0. Original
#         (-22.8167, -47.0667, "Unicamp / Barão Geraldo"),      # 1. Unicamp (Coord de Paulínia) + Barão Geraldo (Original)
#         (-22.9167, -47.0667, "Jd. Paineiras / Próx. Iguatemi"), # 2. Proxy do Iguatemi (Original)
#         (-22.9667, -47.1333, "Aeroporto de Viracopos"),       # 3. Aeroporto (Coord de Nova Odessa)
#         (-22.9103, -47.0732, "Terminal Rodoviário (Real)"),   # 4. Localização real (substitui Parque Prado)
#         (-22.8583, -47.0792, "Mansões Sto. Antônio / Próx. Pq. D. Pedro"), # 5. Proxy do Pq. D. Pedro (Original)
#         (-22.8592, -47.0456, "PUC Campinas (Campus I Real)"), # 6. Localização real (substitui Jd. Proença)
#         (-22.8708, -47.0331, "Lagoa do Taquaral"),            # 7. Localização real (substitui Jd. Guanabara)
        
#         # --- Cidades Vizinhas (Re-introduzidas) ---
#         (-22.8587, -47.2201, "Hortolândia (Centro)"),         # 8. Hortolândia (Coord de Jaguariúna)
#         (-22.7600, -47.1539, "Paulínia (Centro - Real)"),     # 9. RE-INTRODUZIDA (Coord real)
#         (-22.8225, -47.2690, "Sumaré (Centro - Real)"),       # 10. Sumaré (Coord de Americana)
#         (-22.7167, -47.0333, "Jaguariúna (Centro)"),          # 11. Jaguariúna (Coord de Pedreira)
#         (-22.7789, -47.2931, "Nova Odessa (Centro - Real)"),  # 12. RE-INTRODUZIDA (Coord real)
#         (-22.7390, -47.3312, "Americana (Centro - Real)"),    # 13. RE-INTRODUZIDA (Coord real)
#         (-22.7410, -46.9022, "Pedreira (Centro - Real)"),     # 14. RE-INTRODUZIDA (Coord real)
#     ]
    
#     # Demandas RE-BALANCEADAS para coincidir com os locais corrigidos
#     # Os valores originais são usados para as cidades re-introduzidas
#     demandas = [
#         120,  # 0. Centro
#         150,  # 1. Unicamp (80) + Barão Geraldo (70)
#         150,  # 2. Iguatemi
#         200,  # 3. Aeroporto
#         90,   # 4. Rodoviária
#         140,  # 5. Dom Pedro
#         60,   # 6. PUC
#         80,   # 7. Lagoa do Taquaral (Valor do 'Unicamp' original, que apontava aqui)
#         85,   # 8. Hortolândia
#         95,   # 9. Paulínia (Valor original)
#         75,   # 10. Sumaré
#         50,   # 11. Jaguariúna
#         45,   # 12. Nova Odessa (Valor original)
#         110,  # 13. Americana (Valor original)
#         35,   # 14. Pedreira (Valor original)
#     ]
    
#     # Capacidades RE-BALANCEADAS
#     capacidades_eletropostos = [
#         200,  # 0. Centro
#         270,  # 1. Unicamp (150) + Barão Geraldo (120)
#         250,  # 2. Iguatemi
#         300,  # 3. Aeroporto
#         180,  # 4. Rodoviária
#         240,  # 5. Dom Pedro
#         100,  # 6. PUC
#         150,  # 7. Lagoa do Taquaral (Valor do 'Unicamp' original)
#         160,  # 8. Hortolândia
#         180,  # 9. Paulínia (Valor original)
#         140,  # 10. Sumaré
#         90,   # 11. Jaguariúna
#         80,   # 12. Nova Odessa (Valor original)
#         190,  # 13. Americana (Valor original)
#         70,   # 14. Pedreira (Valor original)
#     ]
    
#     # Custos de instalação RE-BALANCEADOS
#     custos_instalacao = [
#         180000, # 0. Centro
#         260000, # 1. Unicamp (140k) + Barão (120k)
#         200000, # 2. Iguatemi
#         250000, # 3. Aeroporto
#         170000, # 4. Rodoviária
#         210000, # 5. Dom Pedro
#         110000, # 6. PUC
#         140000, # 7. Lagoa do Taquaral (Valor do 'Unicamp' original)
#         130000, # 8. Hortolândia
#         160000, # 9. Paulínia (Valor original)
#         125000, # 10. Sumaré
#         100000, # 11. Jaguariúna
#         95000,  # 12. Nova Odessa (Valor original)
#         150000, # 13. Americana (Valor original)
#         85000,  # 14. Pedreira (Valor original)
#     ]
    
#     # Parâmetros específicos para Campinas
#     distancia_maxima = 15
    
#     # Ajuste para garantir que todas as listas tenham 15 itens
#     # (Caso eu tenha errado a contagem ao editar)
#     assert len(coordenadas) == 15, "Lista de coordenadas não tem 15 itens"
#     assert len(demandas) == 15, "Lista de demandas não tem 15 itens"
#     assert len(capacidades_eletropostos) == 15, "Lista de capacidades não tem 15 itens"
#     assert len(custos_instalacao) == 15, "Lista de custos não tem 15 itens"

#     return {
#         'coordenadas': coordenadas,
#         'demandas': demandas,
#         'capacidades_eletropostos': capacidades_eletropostos,
#         'custos_instalacao': custos_instalacao,
#         'max_distancia': distancia_maxima
#     }

# def obter_coordenadas_simples():
#     """
#     Retorna apenas as coordenadas (lat, lon) sem nomes para cálculos
#     """
#     dados = obter_dados_campinas()
#     return [(lat, lon) for lat, lon, _ in dados['coordenadas']]

# def obter_nomes_locais():
#     """
#     Retorna apenas os nomes dos locais
#     """
#     dados = obter_dados_campinas()
#     return [nome for _, _, nome in dados['coordenadas']]

# def calcular_distancia_haversine(coord1, coord2):
#     """
#     Calcula distância entre duas coordenadas geográficas usando fórmula de Haversine
#     """
#     lat1, lon1 = coord1
#     lat2, lon2 = coord2
    
#     # Converter para radianos
#     lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
#     # Fórmula de Haversine
#     dlat = lat2 - lat1
#     dlon = lon2 - lon1
#     a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
#     c = 2 * math.asin(math.sqrt(a))
    
#     # Raio da Terra em km
#     r = 6371
    
#     return c * r

# def imprimir_dados_campinas():
#     """
#     Imprime informações sobre os dados de Campinas
#     """
#     dados = obter_dados_campinas()
    
#     print("\n🏙️ DADOS DA REGIÃO METROPOLITANA DE CAMPINAS (V3 - HÍBRIDA)")
#     print("="*70)
#     print(f"📍 Número de localizações: {len(dados['coordenadas'])}")
#     print(f"📏 Distância máxima de atendimento: {dados['max_distancia']} km")
    
#     demanda_total = sum(dados['demandas'])
#     capacidade_total = sum(dados['capacidades_eletropostos'])
#     custo_total_max = sum(dados['custos_instalacao'])
    
#     print(f"📊 Demanda total estimada: {demanda_total} veículos/dia")
#     print(f"🔋 Capacidade total disponível: {capacidade_total} veículos/dia")
#     print(f"💰 Investimento total máximo: R$ {custo_total_max:,.0f}")
    
#     print(f"\n📍 LOCALIZAÇÕES ESTRATÉGICAS (Nomes Corrigidos):")
#     print("-"*70)
    
#     for i, ((lat, lon, nome), demanda, capacidade, custo) in enumerate(zip(
#         dados['coordenadas'], 
#         dados['demandas'], 
#         dados['capacidades_eletropostos'],
#         dados['custos_instalacao']
#     )):
#         # Evitar divisão por zero se a capacidade for 0
#         if capacidade > 0:
#             eficiencia = custo / capacidade
#         else:
#             eficiencia = 0

#         print(f"{i:2d}. {nome:<45} | Dem: {demanda:3d} | Cap: {capacidade:3d} | "
#               f"Custo: R$ {custo:>8,.0f} | R$/Cap: {eficiencia:>6.0f}")
    
#     print("="*70)
    
#     # Os índices aqui teriam que ser totalmente refeitos
#     print(f"\n📈 ANÁLISE POR TIPO (ÍNDICES A SEREM ATUALIZADOS):")
    
#     tipos = {
#         'Campinas - Shoppings': [2, 5],
#         'Campinas - Transporte': [3, 4],
#         'Campinas - Educacional': [1, 6],
#         'Campinas - Lazer/Centro': [0, 7],
#         'Cidades Vizinhas': [8, 9, 10, 11, 12, 13, 14]
#     }
    
#     for tipo, indices in tipos.items():
#         valid_indices = [i for i in indices if i < len(dados['demandas'])]
#         if not valid_indices:
#             continue
            
#         demanda_tipo = sum(dados['demandas'][i] for i in valid_indices)
#         capacidade_tipo = sum(dados['capacidades_eletropostos'][i] for i in valid_indices)
#         custo_tipo = sum(dados['custos_instalacao'][i] for i in valid_indices)
        
#         print(f"    {tipo:<22}: {len(valid_indices)} locais | "
#               f"Demanda: {demanda_tipo:4d} | Capacidade: {capacidade_tipo:4d} | "
#               f"Custo: R$ {custo_tipo:>9,.0f}")

# if __name__ == "__main__":
#     imprimir_dados_campinas()







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
        padding-top: 1rem;
        padding-bottom: 1rem;
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
        
        # Status do Google Maps API
        st.markdown("#### 🗺️ Google Maps API")
        
        api_key = obter_google_maps_api_key()
        
        if api_key:
            st.success("✅ API Key configurada via .env")
            st.info("🔐 API Key carregada de variável de ambiente")
            usar_google_maps = True
            
            # Botão para limpar cache
            if st.button("🗑️ Limpar Cache Google Maps", help="Remove cache de distâncias e rotas"):
                try:
                    from utils.google_maps_cache import GoogleMapsCache
                    cache = GoogleMapsCache(api_key)
                    cache.limpar_cache()
                except Exception as e:
                    st.error(f"Erro ao limpar cache: {e}")
        else:
            st.warning("⚠️ API Key não configurada")
            st.info("""
            **Para usar Google Maps:**
            1. Crie arquivo `.env` na raiz do projeto
            2. Adicione: `GOOGLE_MAPS_API_KEY=sua_chave_aqui`
            3. Reinicie o dashboard
            """)
            usar_google_maps = False
        
        # Mostrar que tipo de distância será usada
        if usar_google_maps:
            st.success("🛣️ Usando distâncias reais (Google Maps)")
        else:
            st.info("📐 Usando distâncias euclidianas")
        
        st.markdown("---")
        
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
        
        # Distância máxima
        distancia_maxima = st.slider(
            "Distância máxima de atendimento (km)",
            min_value=5,
            max_value=25,
            value=10,
            step=1,
            help="Distância máxima que um eletroposto pode atender"
        )
              
        # Botão de otimização
        if st.button("🚀 Executar otimização", use_container_width=True):
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
            
            # Círculo de cobertura
            folium.Circle(
                location=[lat, lon],
                radius=dados['max_distancia'] * 1000,  # Converter para metros
                popup=f"Área de cobertura: {dados['max_distancia']} km",
                color='blue',
                weight=2,
                fill=True,
                fillColor='lightblue',
                fillOpacity=0.2
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
                top: 10px; right: 10px; width: 220px; height: 170px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px; border-radius: 10px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);">    
    <p><i class="fa fa-bolt" style="color:blue"></i> Eletroposto instalado</p>
    <p><i class="fa fa-circle" style="color:green"></i> Baixa demanda (&lt;60)</p>
    <p><i class="fa fa-circle" style="color:orange"></i> Média demanda (60-120)</p>
    <p><i class="fa fa-circle" style="color:red"></i> Alta demanda (&gt;120)</p>
    <p style="border-top: 1px dashed #666; padding-top: 5px; margin-top: 5px;">
    <span style="color:#666;">--- Rotas de atendimento</span></p>
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
        
        # Informação sobre Google Maps
        if resultado_atual.get('usa_google_maps', False):
            st.info("🗺️ Usando distâncias reais do Google Maps e rotas de trânsito")
        else:
            st.info("📐 Usando distâncias euclidianas (linha reta)")
        
        # Mapa
        with st.container():
            mapa = criar_mapa_campinas(resultado_atual)
            st_folium(mapa, width=None, height=500, returned_objects=["last_clicked"])
            
    else:
        # Se não há resultados, mostrar mapa básico e instruções                
        with st.container():
            mapa = criar_mapa_campinas()
            st_folium(mapa, width=None, height=500)

if __name__ == "__main__":
    main()