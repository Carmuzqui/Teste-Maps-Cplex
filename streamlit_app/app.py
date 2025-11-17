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
                       
    else:
        # Se não há resultados, mostrar mapa básico e instruções                
        with st.container():
            mapa = criar_mapa_campinas()
            st_folium(mapa, width=None, height=650)

if __name__ == "__main__":
    main()