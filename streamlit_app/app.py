"""
Dashboard Streamlit para otimização de eletropostos em Campinas
"""

import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os

# Adicionar diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dados.dados_campinas import obter_dados_campinas, obter_coordenadas_simples, obter_nomes_locais
from modelos.modelo_multi_objetivo import ModeloEletropostosMultiObjetivo

# Configuração da página
st.set_page_config(
    page_title="Otimização de Eletropostos - Campinas",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"  # Sidebar oculto por padrão
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

def criar_sidebar():
    """Cria sidebar com controles modernos"""
    with st.sidebar:
        st.markdown("### ⚙️ Configurações de Otimização")
        
        # Tipo de objetivo
        tipo_objetivo = st.selectbox(
            "🎯 Estratégia de Otimização",
            ["minimizar_custo", "maximizar_cobertura", "multi_objetivo"],
            format_func=lambda x: {
                "minimizar_custo": "💰 Minimizar Custo",
                "maximizar_cobertura": "📊 Maximizar Cobertura", 
                "multi_objetivo": "⚖️ Multi-Objetivo"
            }[x],
            help="Escolha a estratégia de otimização desejada"
        )
        
        st.markdown("---")
        
        # Parâmetros específicos por tipo
        orcamento_maximo = None
        pesos = (0.6, 0.4)
        
        if tipo_objetivo == "maximizar_cobertura":
            st.markdown("#### 💰 Restrição Orçamentária")
            orcamento_maximo = st.number_input(
                "Orçamento Máximo (R$)",
                min_value=100000,
                max_value=2000000,
                value=800000,
                step=50000,
                format="%d",
                help="Orçamento disponível para instalação dos eletropostos"
            )
            
        elif tipo_objetivo == "multi_objetivo":
            st.markdown("#### ⚖️ Balanceamento de Objetivos")
            peso_cobertura = st.slider(
                "Prioridade: Cobertura vs Custo",
                min_value=0.1,
                max_value=0.9,
                value=0.7,
                step=0.1,
                format="%.1f",
                help="0.1 = Foco no custo | 0.9 = Foco na cobertura"
            )
            pesos = (peso_cobertura, 1 - peso_cobertura)
            
            # Visualização dos pesos
            col1, col2 = st.columns(2)
            with col1:
                st.metric("📊 Cobertura", f"{peso_cobertura:.1%}")
            with col2:
                st.metric("💰 Custo", f"{1-peso_cobertura:.1%}")
        
        st.markdown("---")
        
        # Parâmetros avançados
        with st.expander("🔧 Parâmetros Avançados"):
            distancia_maxima = st.slider(
                "Distância Máxima de Atendimento (km)",
                min_value=5,
                max_value=30,
                value=15,
                step=1,
                help="Distância máxima que um eletroposto pode atender"
            )
        
        st.markdown("---")
        
        # Botão de otimização
        if st.button("🚀 Executar Otimização", use_container_width=True):
            with st.spinner("Otimizando localização dos eletropostos..."):
                executar_otimizacao(tipo_objetivo, orcamento_maximo, pesos, distancia_maxima)
        
        # Botão para comparar estratégias
        if st.button("📊 Comparar Todas as Estratégias", use_container_width=True):
            with st.spinner("Executando todas as estratégias..."):
                comparar_todas_estrategias()
        
        st.markdown("---")
        st.markdown("#### 📋 Informações do Dataset")
        st.info(f"""
        **Região:** Campinas e Região Metropolitana
        
        **Localizações:** {len(st.session_state.dados_campinas['coordenadas'])}
        
        **Demanda Total:** {sum(st.session_state.dados_campinas['demandas'])} veículos/dia
        
        **Investimento Máximo:** R$ {sum(st.session_state.dados_campinas['custos_instalacao']):,.0f}
        """)

def criar_mapa_campinas(resultados=None):
    """Cria mapa interativo de Campinas em tela cheia"""
    dados = st.session_state.dados_campinas
    nomes = obter_nomes_locais()
    
    # Centro do mapa (Campinas)
    centro_lat = -22.9056
    centro_lon = -47.0608
    
    # Criar mapa base
    m = folium.Map(
        location=[centro_lat, centro_lon],
        zoom_start=11,
        tiles='CartoDB positron',
        attr='CartoDB'
    )
    
    # Adicionar marcadores de demanda (pontos não selecionados)
    for i, ((lat, lon, nome), demanda, capacidade) in enumerate(zip(
        dados['coordenadas'], dados['demandas'], dados['capacidades_eletropostos']
    )):
        # Cor baseada na demanda
        if demanda < 60:
            cor = 'green'
            icone = 'leaf'
        elif demanda < 120:
            cor = 'orange' 
            icone = 'flash'
        else:
            cor = 'red'
            icone = 'fire'
        
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
    
    # Adicionar legenda
    legenda_html = """
    <div style="position: fixed; 
                top: 10px; right: 10px; width: 200px; height: 120px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px; border-radius: 10px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
    <h4 style="margin-top:0;">📊 Legenda</h4>
    <p><i class="fa fa-bolt" style="color:blue"></i> Eletroposto Instalado</p>
    <p><i class="fa fa-circle" style="color:green"></i> Baixa Demanda (&lt;60)</p>
    <p><i class="fa fa-circle" style="color:orange"></i> Média Demanda (60-120)</p>
    <p><i class="fa fa-circle" style="color:red"></i> Alta Demanda (&gt;120)</p>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legenda_html))
    
    return m

def executar_otimizacao(tipo_objetivo, orcamento_maximo, pesos, distancia_maxima):
    """Executa otimização com parâmetros selecionados"""
    dados = st.session_state.dados_campinas
    coordenadas_simples = obter_coordenadas_simples()
    
    # Atualizar distância máxima nos dados
    dados_temp = dados.copy()
    dados_temp['max_distancia'] = distancia_maxima
    
    try:
        modelo = ModeloEletropostosMultiObjetivo(
            coordenadas=coordenadas_simples,
            demandas=dados['demandas'],
            capacidades_eletropostos=dados['capacidades_eletropostos'],
            custos_instalacao=dados['custos_instalacao'],
            distancia_maxima=distancia_maxima,
            tipo_objetivo=tipo_objetivo,
            orcamento_maximo=orcamento_maximo,
            pesos=pesos
        )
        
        if modelo.resolver():
            st.session_state.resultados[tipo_objetivo] = modelo.obter_resumo()
            st.session_state.modelo_atual = modelo
            st.success(f"✅ Otimização concluída com sucesso!")
            st.rerun()
        else:
            st.error("❌ Não foi possível encontrar uma solução viável. Tente ajustar os parâmetros.")
            
    except Exception as e:
        st.error(f"❌ Erro durante otimização: {str(e)}")

def comparar_todas_estrategias():
    """Executa todas as estratégias para comparação"""
    dados = st.session_state.dados_campinas
    coordenadas_simples = obter_coordenadas_simples()
    
    estrategias = [
        ('minimizar_custo', None, (0.6, 0.4)),
        ('maximizar_cobertura', 800000, (0.6, 0.4)),
        ('multi_objetivo', None, (0.7, 0.3))
    ]
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, (tipo, orcamento, pesos_estrategia) in enumerate(estrategias):
        status_text.text(f"Executando estratégia: {tipo.replace('_', ' ').title()}")
        
        try:
            modelo = ModeloEletropostosMultiObjetivo(
                coordenadas=coordenadas_simples,
                demandas=dados['demandas'],
                capacidades_eletropostos=dados['capacidades_eletropostos'],
                custos_instalacao=dados['custos_instalacao'],
                distancia_maxima=dados['max_distancia'],
                tipo_objetivo=tipo,
                orcamento_maximo=orcamento,
                pesos=pesos_estrategia
            )
            
            if modelo.resolver():
                st.session_state.resultados[tipo] = modelo.obter_resumo()
                
        except Exception as e:
            st.error(f"Erro na estratégia {tipo}: {str(e)}")
        
        progress_bar.progress((i + 1) / len(estrategias))
    
    status_text.text("Comparação concluída!")
    st.success("✅ Todas as estratégias foram executadas!")
    st.rerun()

def main():
    """Função principal do dashboard"""
    inicializar_sessao()
    
    # Título principal
    st.markdown('<h1 class="main-title">⚡ Otimização de Eletropostos - Campinas</h1>', 
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
            eficiencia = resultado_atual['cobertura_total'] / resultado_atual['custo_total'] * 1000
            st.metric(
                "⚡ Eficiência",
                f"{eficiencia:.2f}",
                help="Cobertura por mil reais investidos"
            )
        
        # Mapa em tela cheia
        st.markdown("### 🗺️ Localização Otimizada dos Eletropostos")
        
        with st.container():
            st.markdown('<div class="map-container">', unsafe_allow_html=True)
            mapa = criar_mapa_campinas(resultado_atual)
            st_folium(mapa, width=None, height=500, returned_objects=["last_clicked"])
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Tabela de comparação se houver múltiplos resultados
        if len(st.session_state.resultados) > 1:
            st.markdown("### �� Comparação de Estratégias")
            criar_tabela_comparacao()
    
    else:
        # Se não há resultados, mostrar mapa básico e instruções
        st.markdown("### 🗺️ Região Metropolitana de Campinas")
        st.info("👈 Configure os parâmetros no painel lateral e execute a otimização para ver os resultados no mapa.")
        
        with st.container():
            st.markdown('<div class="map-container">', unsafe_allow_html=True)
            mapa = criar_mapa_campinas()
            st_folium(mapa, width=None, height=500)
            st.markdown('</div>', unsafe_allow_html=True)

def criar_tabela_comparacao():
    """Cria tabela de comparação entre estratégias"""
    df_comparacao = []
    
    for nome, resultado in st.session_state.resultados.items():
        eficiencia = resultado['cobertura_total'] / resultado['custo_total'] * 1000
        
        df_comparacao.append({
            'Estratégia': nome.replace('_', ' ').title(),
            'Eletropostos': resultado['eletropostos_instalados'],
            'Custo (R$)': f"R$ {resultado['custo_total']:,.0f}",
            'Cobertura (%)': f"{resultado['cobertura_percentual']:.1f}%",
            'Eficiência': f"{eficiencia:.2f}",
            'Tempo (s)': f"{resultado['tempo_solucao']:.2f}"
        })
    
    df = pd.DataFrame(df_comparacao)
    st.dataframe(df, use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()







# """
# Dashboard Streamlit para otimização de eletropostos em Campinas
# """

# import streamlit as st
# import folium
# from streamlit_folium import st_folium
# import pandas as pd
# import sys
# import os

# # Adicionar diretório raiz ao path
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# from dados.dados_campinas import obter_dados_campinas, obter_coordenadas_simples, obter_nomes_locais
# from modelos.modelo_multi_objetivo import ModeloEletropostosMultiObjetivo

# # Configuração da página
# st.set_page_config(
#     page_title="Otimização de Eletropostos - Campinas",
#     page_icon="⚡",
#     layout="wide",
#     initial_sidebar_state="collapsed"
# )

# # CSS personalizado para mapa em tela cheia
# st.markdown("""
# <style>
#     /* Remover padding e margin padrão */
#     .main .block-container {
#         padding-top: 0rem;
#         padding-bottom: 0rem;
#         padding-left: 1rem;
#         padding-right: 1rem;
#         max-width: 100%;
#     }
    
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
    
#     /* Container do mapa em tela cheia */
#     .map-fullscreen {
#         position: relative;
#         height: 100vh;
#         width: 100%;
#         margin: 0;
#         padding: 0;
#     }
    
#     /* Métricas flutuantes sobre o mapa */
#     .metrics-overlay {
#         position: absolute;
#         top: 20px;
#         left: 20px;
#         z-index: 1000;
#         background: rgba(255, 255, 255, 0.95);
#         backdrop-filter: blur(10px);
#         border-radius: 15px;
#         padding: 1rem;
#         box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
#         border: 1px solid rgba(255, 255, 255, 0.2);
#     }
    
#     .metric-item {
#         display: inline-block;
#         margin-right: 2rem;
#         text-align: center;
#     }
    
#     .metric-value {
#         font-size: 1.5rem;
#         font-weight: bold;
#         color: #1e40af;
#         display: block;
#     }
    
#     .metric-label {
#         font-size: 0.8rem;
#         color: #64748b;
#         display: block;
#     }
    
#     /* Ocultar elementos desnecessários */
#     header[data-testid="stHeader"] {
#         display: none;
#     }
    
#     .stDeployButton {
#         display: none;
#     }
    
#     /* Estilo para expander */
#     .streamlit-expanderHeader {
#         background: linear-gradient(90deg, #f1f5f9, #e2e8f0);
#         border-radius: 10px;
#         font-weight: 600;
#     }
    
#     /* Forçar iframe do folium a ocupar espaço completo */
#     iframe {
#         width: 100% !important;
#         height: 100vh !important;
#         border: none !important;
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

# def verificar_cplex():
#     """Verifica se CPLEX está disponível"""
#     try:
#         from docplex.mp.model import Model
#         # Tentar criar um modelo simples
#         test_model = Model('test')
#         x = test_model.binary_var('x')
#         test_model.minimize(x)
#         # Não resolver, apenas verificar se pode ser criado
#         return True
#     except Exception as e:
#         return False, str(e)

# def criar_sidebar():
#     """Cria sidebar com controles modernos"""
#     with st.sidebar:
#         st.markdown("### ⚙️ Configurações de Otimização")
        
#         # Verificar CPLEX primeiro
#         cplex_ok = verificar_cplex()
#         if not cplex_ok:
#             st.error("❌ CPLEX não detectado!")
#             st.markdown("""
#             **Soluções possíveis:**
#             1. Instalar CPLEX Community Edition
#             2. Configurar variáveis de ambiente
#             3. Usar solver alternativo (PuLP)
#             """)
#             return None, None, None, None
        
#         # Tipo de objetivo
#         tipo_objetivo = st.selectbox(
#             "🎯 Estratégia de Otimização",
#             ["minimizar_custo", "maximizar_cobertura", "multi_objetivo"],
#             format_func=lambda x: {
#                 "minimizar_custo": "💰 Minimizar Custo",
#                 "maximizar_cobertura": "📊 Maximizar Cobertura", 
#                 "multi_objetivo": "⚖️ Multi-Objetivo"
#             }[x],
#             help="Escolha a estratégia de otimização desejada"
#         )
        
#         st.markdown("---")
        
#         # Parâmetros específicos por tipo
#         orcamento_maximo = None
#         pesos = (0.6, 0.4)
        
#         if tipo_objetivo == "maximizar_cobertura":
#             st.markdown("#### 💰 Restrição Orçamentária")
#             orcamento_maximo = st.number_input(
#                 "Orçamento Máximo (R$)",
#                 min_value=100000,
#                 max_value=2000000,
#                 value=800000,
#                 step=50000,
#                 format="%d",
#                 help="Orçamento disponível para instalação dos eletropostos"
#             )
            
#         elif tipo_objetivo == "multi_objetivo":
#             st.markdown("#### ⚖️ Balanceamento de Objetivos")
#             peso_cobertura = st.slider(
#                 "Prioridade: Cobertura vs Custo",
#                 min_value=0.1,
#                 max_value=0.9,
#                 value=0.7,
#                 step=0.1,
#                 format="%.1f",
#                 help="0.1 = Foco no custo | 0.9 = Foco na cobertura"
#             )
#             pesos = (peso_cobertura, 1 - peso_cobertura)
            
#             # Visualização dos pesos
#             col1, col2 = st.columns(2)
#             with col1:
#                 st.metric("📊 Cobertura", f"{peso_cobertura:.1%}")
#             with col2:
#                 st.metric("💰 Custo", f"{1-peso_cobertura:.1%}")
        
#         st.markdown("---")
        
#         # Parâmetros avançados
#         with st.expander("🔧 Parâmetros Avançados"):
#             distancia_maxima = st.slider(
#                 "Distância Máxima de Atendimento (km)",
#                 min_value=5,
#                 max_value=30,
#                 value=15,
#                 step=1,
#                 help="Distância máxima que um eletroposto pode atender"
#             )
        
#         st.markdown("---")
        
#         # Botão de otimização
#         if st.button("🚀 Executar Otimização", use_container_width=True):
#             with st.spinner("Otimizando localização dos eletropostos..."):
#                 executar_otimizacao(tipo_objetivo, orcamento_maximo, pesos, distancia_maxima)
        
#         # Botão para comparar estratégias
#         if st.button("📊 Comparar Todas as Estratégias", use_container_width=True):
#             with st.spinner("Executando todas as estratégias..."):
#                 comparar_todas_estrategias()
        
#         st.markdown("---")
#         st.markdown("#### 📋 Informações do Dataset")
#         st.info(f"""
#         **Região:** Campinas e Região Metropolitana
        
#         **Localizações:** {len(st.session_state.dados_campinas['coordenadas'])}
        
#         **Demanda Total:** {sum(st.session_state.dados_campinas['demandas'])} veículos/dia
        
#         **Investimento Máximo:** R$ {sum(st.session_state.dados_campinas['custos_instalacao']):,.0f}
#         """)
        
#         return tipo_objetivo, orcamento_maximo, pesos, distancia_maxima

# def criar_mapa_campinas(resultados=None):
#     """Cria mapa interativo de Campinas em tela cheia"""
#     dados = st.session_state.dados_campinas
#     nomes = obter_nomes_locais()
    
#     # Centro do mapa (Campinas)
#     centro_lat = -22.9056
#     centro_lon = -47.0608
    
#     # Criar mapa base
#     m = folium.Map(
#         location=[centro_lat, centro_lon],
#         zoom_start=11,
#         tiles='CartoDB positron',
#         attr='CartoDB'
#     )
    
#     # Adicionar marcadores de demanda (pontos não selecionados)
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
            
#             # Círculo de cobertura
#             folium.Circle(
#                 location=[lat, lon],
#                 radius=dados['max_distancia'] * 1000,  # Converter para metros
#                 popup=f"Área de cobertura: {dados['max_distancia']} km",
#                 color='blue',
#                 weight=2,
#                 fill=True,
#                 fillColor='lightblue',
#                 fillOpacity=0.2
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
#                 color='darkblue',
#                 weight=2,
#                 fill=True,
#                 fillColor=cor,
#                 fillOpacity=0.7
#             ).add_to(m)
    
#     # Adicionar legenda
#     legenda_html = """
#     <div style="position: fixed; 
#                 top: 10px; right: 10px; width: 200px; height: 120px; 
#                 background-color: white; border:2px solid grey; z-index:9999; 
#                 font-size:14px; padding: 10px; border-radius: 10px;
#                 box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
#     <h4 style="margin-top:0;">📊 Legenda</h4>
#     <p><i class="fa fa-bolt" style="color:blue"></i> Eletroposto Instalado</p>
#     <p><i class="fa fa-circle" style="color:green"></i> Baixa Demanda (&lt;60)</p>
#     <p><i class="fa fa-circle" style="color:orange"></i> Média Demanda (60-120)</p>
#     <p><i class="fa fa-circle" style="color:red"></i> Alta Demanda (&gt;120)</p>
#     </div>
#     """
#     m.get_root().html.add_child(folium.Element(legenda_html))
    
#     return m

# def executar_otimizacao(tipo_objetivo, orcamento_maximo, pesos, distancia_maxima):
#     """Executa otimização com parâmetros selecionados"""
#     dados = st.session_state.dados_campinas
#     coordenadas_simples = obter_coordenadas_simples()
    
#     # Atualizar distância máxima nos dados
#     dados_temp = dados.copy()
#     dados_temp['max_distancia'] = distancia_maxima
    
#     try:
#         modelo = ModeloEletropostosMultiObjetivo(
#             coordenadas=coordenadas_simples,
#             demandas=dados['demandas'],
#             capacidades_eletropostos=dados['capacidades_eletropostos'],
#             custos_instalacao=dados['custos_instalacao'],
#             distancia_maxima=distancia_maxima,
#             tipo_objetivo=tipo_objetivo,
#             orcamento_maximo=orcamento_maximo,
#             pesos=pesos
#         )
        
#         if modelo.resolver():
#             st.session_state.resultados[tipo_objetivo] = modelo.obter_resumo()
#             st.session_state.modelo_atual = modelo
#             st.success(f"✅ Otimização concluída com sucesso!")
#             st.rerun()
#         else:
#             st.error("❌ Não foi possível encontrar uma solução viável. Tente ajustar os parâmetros.")
            
#     except Exception as e:
#         st.error(f"❌ Erro durante otimização: {str(e)}")
        
#         # Sugestões de solução
#         st.markdown("""
#         **Possíveis soluções:**
#         - Verificar se CPLEX está instalado corretamente
#         - Tentar com parâmetros menos restritivos
#         - Verificar se há memória suficiente
#         """)

# def comparar_todas_estrategias():
#     """Executa todas as estratégias para comparação"""
#     dados = st.session_state.dados_campinas
#     coordenadas_simples = obter_coordenadas_simples()
    
#     estrategias = [
#         ('minimizar_custo', None, (0.6, 0.4)),
#         ('maximizar_cobertura', 800000, (0.6, 0.4)),
#         ('multi_objetivo', None, (0.7, 0.3))
#     ]
    
#     progress_bar = st.progress(0)
#     status_text = st.empty()
    
#     for i, (tipo, orcamento, pesos_estrategia) in enumerate(estrategias):
#         status_text.text(f"Executando estratégia: {tipo.replace('_', ' ').title()}")
        
#         try:
#             modelo = ModeloEletropostosMultiObjetivo(
#                 coordenadas=coordenadas_simples,
#                 demandas=dados['demandas'],
#                 capacidades_eletropostos=dados['capacidades_eletropostos'],
#                 custos_instalacao=dados['custos_instalacao'],
#                 distancia_maxima=dados['max_distancia'],
#                 tipo_objetivo=tipo,
#                 orcamento_maximo=orcamento,
#                 pesos=pesos_estrategia
#             )
            
#             if modelo.resolver():
#                 st.session_state.resultados[tipo] = modelo.obter_resumo()
                
#         except Exception as e:
#             st.error(f"Erro na estratégia {tipo}: {str(e)}")
        
#         progress_bar.progress((i + 1) / len(estrategias))
    
#     status_text.text("Comparação concluída!")
#     st.success("✅ Todas as estratégias foram executadas!")
#     st.rerun()

# def criar_metricas_overlay(resultado):
#     """Cria overlay de métricas sobre o mapa"""
#     eficiencia = resultado['cobertura_total'] / resultado['custo_total'] * 1000
    
#     metricas_html = f"""
#     <div class="metrics-overlay">
#         <div class="metric-item">
#             <span class="metric-value">⚡ {resultado['eletropostos_instalados']}</span>
#             <span class="metric-label">Eletropostos</span>
#         </div>
#         <div class="metric-item">
#             <span class="metric-value">💰 {resultado['custo_total']:,.0f}</span>
#             <span class="metric-label">Custo (R$)</span>
#         </div>
#         <div class="metric-item">
#             <span class="metric-value">📊 {resultado['cobertura_percentual']:.1f}%</span>
#             <span class="metric-label">Cobertura</span>
#         </div>
#         <div class="metric-item">
#             <span class="metric-value">⚡ {eficiencia:.2f}</span>
#             <span class="metric-label">Eficiência</span>
#         </div>
#     </div>
#     """
#     return metricas_html

# def main():
#     """Função principal do dashboard"""
#     inicializar_sessao()
    
#     # Criar sidebar e obter parâmetros
#     params = criar_sidebar()
    
#     # Se CPLEX não estiver disponível, mostrar apenas mapa básico
#     if params[0] is None:
#         st.markdown('<div class="map-fullscreen">', unsafe_allow_html=True)
#         mapa = criar_mapa_campinas()
#         st_folium(mapa, width=None, height=600, returned_objects=["last_clicked"])
#         st.markdown('</div>', unsafe_allow_html=True)
#         return
    
#     # Layout principal - mapa em tela cheia
#     if st.session_state.resultados:
#         resultado_atual = list(st.session_state.resultados.values())[-1]  # Último resultado
        
#         # Criar overlay de métricas
#         metricas_overlay = criar_metricas_overlay(resultado_atual)
#         st.markdown(metricas_overlay, unsafe_allow_html=True)
        
#         # Mapa em tela cheia
#         st.markdown('<div class="map-fullscreen">', unsafe_allow_html=True)
#         mapa = criar_mapa_campinas(resultado_atual)
#         st_folium(mapa, width=None, height=600, returned_objects=["last_clicked"])
#         st.markdown('</div>', unsafe_allow_html=True)
        
#     else:
#         # Mapa básico sem resultados
#         st.markdown('<div class="map-fullscreen">', unsafe_allow_html=True)
#         mapa = criar_mapa_campinas()
#         st_folium(mapa, width=None, height=600, returned_objects=["last_clicked"])
#         st.markdown('</div>', unsafe_allow_html=True)

# if __name__ == "__main__":
#     main()