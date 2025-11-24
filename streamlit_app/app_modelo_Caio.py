"""
Dashboard Streamlit para Modelo FCSA MILP - Caio dos Santos
Otimização de estações de recarga rápida com PV e cobertura espacial
"""

import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import sys
import os
from pathlib import Path
import yaml

# Adicionar diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modelos.modelo_Caio import FCSA_MILP

# Configuração da página
st.set_page_config(
    page_title="FCSA MILP - Otimização Eletropostos",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    /* Tema moderno */
    .main-title {
        background: linear-gradient(90deg, #1e40af, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .subtitle {
        text-align: center;
        color: #64748b;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    
    /* Métricas modernas */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 700;
    }
    
    /* Botão principal */
    .stButton > button {
        background: linear-gradient(45deg, #3b82f6, #1d4ed8);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.7rem 2rem;
        font-weight: 600;
        width: 100%;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
    }
    
    .stButton > button:hover {
        background: linear-gradient(45deg, #1d4ed8, #1e40af);
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
    }
    
    /* Container do mapa */
    .map-container {
        border-radius: 15px;
        overflow: hidden;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: linear-gradient(90deg, #f1f5f9, #e2e8f0);
        border-radius: 10px;
        font-weight: 600;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e3a8a 0%, #1e40af 100%);
    }
    
    /* Remover padding extra */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
        max-width: 100%;
    }
</style>
""", unsafe_allow_html=True)

def inicializar_sessao():
    """Inicializa variáveis de sessão"""
    if 'modelo_resolvido' not in st.session_state:
        st.session_state.modelo_resolvido = False
    if 'modelo_atual' not in st.session_state:
        st.session_state.modelo_atual = None
    if 'problema_selecionado' not in st.session_state:
        st.session_state.problema_selecionado = None

def listar_problemas_disponiveis():
    """Lista problemas disponíveis na pasta dados/"""
    pasta_dados = Path('dados')
    if not pasta_dados.exists():
        return []
    
    problemas = []
    for item in pasta_dados.iterdir():
        if item.is_dir() and item.name.startswith('problema'):
            # Verificar se tem config_geral.yaml
            if (item / 'config_geral.yaml').exists():
                problemas.append(item.name)
    
    return sorted(problemas)

def carregar_info_problema(pasta_problema):
    """Carrega informações básicas do problema"""
    try:
        with open(Path(pasta_problema) / 'config_geral.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        return {
            'nome': config['problema']['nome'],
            'descricao': config['problema']['descricao'],
            'cidade': config['problema'].get('cidade', 'N/A'),
            'num_links': config['dimensoes']['num_links'],
            'raio_cobertura': config['parametros_otimizacao'].get('raio_cobertura_km', 3.0),
            'gamma': config['parametros_otimizacao']['gamma'],
            'alpha': config['parametros_financeiros']['alpha'],
            'horizonte': config['parametros_financeiros']['Delta_h'],
            'time_limit': config['solver']['time_limit'],
            'mip_gap': config['solver']['mip_gap']
        }
    except Exception as e:
        return None

def criar_sidebar():
    """Cria sidebar com seleção de problema"""
    with st.sidebar:
        st.markdown("### ⚙️ Configuração")
        st.markdown("---")
        
        # Listar problemas disponíveis
        problemas = listar_problemas_disponiveis()
        
        if not problemas:
            st.error("❌ Nenhum problema encontrado na pasta `dados/`")
            st.info("""
            **Estrutura esperada:**
            ```
            dados/
            ├── problema0/
            │   ├── config_geral.yaml
            │   ├── links.csv
            │   └── ...
            ├── problema1/
            │   └── ...
            ```
            """)
            return None
        
        # Seleção do problema
        problema_selecionado = st.selectbox(
            "📁 Problema a resolver:",
            problemas,
            index=0,
            help="Selecione qual problema deseja otimizar"
        )
        
        # Carregar informações do problema
        info = carregar_info_problema(f'dados/{problema_selecionado}')
        
        if info:
            st.markdown("---")
            st.markdown("#### 📋 Informações do Problema")
            st.markdown(f"**Nome:** {info['nome']}")
            st.markdown(f"**Cidade:** {info['cidade']}")
            st.markdown(f"**Links:** {info['num_links']}")
            st.markdown(f"**Raio cobertura:** {info['raio_cobertura']} km")
            st.markdown(f"**Peso γ:** {info['gamma']}")
            st.markdown(f"**Taxa α:** {info['alpha']*100:.0f}%")
            st.markdown(f"**Horizonte:** {info['horizonte']} anos")
            
            st.markdown("---")
            st.markdown("#### ⚡ Solver")
            st.markdown(f"**Tempo limite:** {info['time_limit']}s")
            st.markdown(f"**Gap MIP:** {info['mip_gap']*100:.1f}%")
            
            st.markdown("---")
            
            # Botão de otimização
            if st.button("🚀 Executar Otimização", use_container_width=True):
                executar_otimizacao(f'dados/{problema_selecionado}')
            
            # Informação sobre o gap
            st.info("""
            **💡 Sobre o Gap MIP:**
            
            O gap indica a distância entre a solução encontrada e o ótimo teórico.
            
            - **Gap < 2%:** Solução excelente
            - **Gap < 5%:** Solução boa
            - **Gap > 5%:** Solução aceitável
            
            O solver para quando atinge o gap configurado ou o tempo limite.
            """)
        
        return problema_selecionado

def executar_otimizacao(pasta_problema):
    """Executa otimização do modelo"""
    with st.spinner("🔄 Resolvendo modelo FCSA MILP... Isso pode levar alguns minutos."):
        try:
            # Criar e resolver modelo
            modelo = FCSA_MILP(pasta_problema)
            sucesso = modelo.resolver()
            
            if sucesso:
                st.session_state.modelo_resolvido = True
                st.session_state.modelo_atual = modelo
                st.session_state.problema_selecionado = pasta_problema
                st.success("✅ Otimização concluída com sucesso!")
                st.rerun()
            else:
                st.error("❌ Não foi possível encontrar uma solução viável.")
                
        except Exception as e:
            st.error(f"❌ Erro durante otimização: {str(e)}")
            st.exception(e)

def criar_mapa_resultados(modelo):
    """Cria mapa interativo com resultados"""
    solucao = modelo.solucao
    
    # Centro do mapa (média das coordenadas)
    coords = list(modelo.coordenadas.values())
    centro_lat = sum(c['latitude'] for c in coords) / len(coords)
    centro_lon = sum(c['longitude'] for c in coords) / len(coords)
    
    # Criar mapa base
    m = folium.Map(
        location=[centro_lat, centro_lon],
        zoom_start=12,
        tiles='CartoDB positron'
    )
    
    # Estações instaladas
    estacoes = solucao['estacoes_instaladas']
    carports = solucao['carports_instalados']
    
    # Adicionar círculos de cobertura
    for est_id in estacoes:
        coord = modelo.coordenadas[est_id]
        
        # Círculo de cobertura
        folium.Circle(
            location=[coord['latitude'], coord['longitude']],
            radius=modelo.raio_cobertura_km * 1000,  # Converter para metros
            color='#3b82f6',
            fill=True,
            fillColor='#3b82f6',
            fillOpacity=0.1,
            weight=2,
            opacity=0.4,
            dash_array='5, 5'
        ).add_to(m)
    
    # Marcadores de estações
    for est_id in estacoes:
        coord = modelo.coordenadas[est_id]
        tem_pv = est_id in carports
        
        # Informações da estação
        demanda_total = sum(modelo.E_d.get((est_id, t), 0) for t in modelo.T)
        
        popup_html = f"""
        <div style="width: 250px;">
            <h4>{'☀️ ' if tem_pv else '⚡ '}Estação Link {est_id}</h4>
            <hr>
            <b>Status:</b> INSTALADA<br>
            <b>Demanda diária:</b> {demanda_total:,.0f} kWh<br>
            <b>Custo instalação:</b> R$ {modelo.c_CS[est_id]:,.0f}<br>
        """
        
        if tem_pv:
            tipo_pv = carports[est_id]
            popup_html += f"""
            <hr>
            <b>🌞 Sistema PV Tipo {tipo_pv}</b><br>
            <b>Potência:</b> {modelo.P_k[tipo_pv]} kW<br>
            <b>Área:</b> {modelo.a_k[tipo_pv]} m²<br>
            <b>Custo PV:</b> R$ {modelo.c_PV[tipo_pv]:,.0f}<br>
            """
        
        popup_html += "</div>"
        
        folium.Marker(
            location=[coord['latitude'], coord['longitude']],
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=f"{'☀️ PV ' if tem_pv else '⚡ '}Link {est_id}",
            icon=folium.Icon(
                color='green' if tem_pv else 'blue',
                icon='solar-panel' if tem_pv else 'bolt',
                prefix='fa'
            )
        ).add_to(m)
    
    # Marcadores de links NÃO instalados
    links_nao_instalados = [l for l in modelo.L if l not in estacoes]
    
    for link_id in links_nao_instalados:
        coord = modelo.coordenadas[link_id]
        demanda_total = sum(modelo.E_d.get((link_id, t), 0) for t in modelo.T)
        
        # Verificar se está coberto
        coberto = link_id in solucao['links_cobertos']
        
        folium.CircleMarker(
            location=[coord['latitude'], coord['longitude']],
            radius=6,
            popup=f"""
            <div style="width: 200px;">
                <h4>📍 Link {link_id}</h4>
                <hr>
                <b>Status:</b> {'COBERTO' if coberto else 'NÃO COBERTO'}<br>
                <b>Demanda:</b> {demanda_total:,.0f} kWh/dia<br>
                <b>ρ×β:</b> {modelo.rho[link_id]*modelo.beta[link_id]:.4f}<br>
            </div>
            """,
            tooltip=f"📍 Link {link_id} - {'✓' if coberto else '✗'}",
            color='green' if coberto else 'red',
            fill=True,
            fillColor='lightgreen' if coberto else 'lightcoral',
            fillOpacity=0.6,
            weight=2
        ).add_to(m)
    
    # Legenda
    legenda_html = """
    <div style="position: fixed; 
                top: 10px; right: 10px; width: 240px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:13px; padding: 12px; border-radius: 10px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);">
    <h4 style="margin:0 0 10px 0;">📋 Legenda</h4>
    <p style="margin:5px 0;"><i class="fa fa-bolt" style="color:blue"></i> Estação sem PV</p>
    <p style="margin:5px 0;"><i class="fa fa-solar-panel" style="color:green"></i> Estação com PV</p>
    <p style="margin:5px 0;"><span style="color:blue; font-size:20px;">○</span> Raio de cobertura</p>
    <p style="margin:5px 0;"><i class="fa fa-circle" style="color:green"></i> Link coberto</p>
    <p style="margin:5px 0;"><i class="fa fa-circle" style="color:red"></i> Link não coberto</p>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legenda_html))
    
    return m

def exibir_metricas_principais(solucao):
    """Exibe métricas principais em cards"""
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "⚡ Estações",
            solucao['num_estacoes'],
            help="Número de estações instaladas"
        )
    
    with col2:
        st.metric(
            "☀️ Carports PV",
            len(solucao['carports_instalados']),
            help="Estações com sistema fotovoltaico"
        )
    
    with col3:
        st.metric(
            "📍 Cobertura",
            f"{solucao['taxa_cobertura_%']:.0f}%",
            help="Percentual de links cobertos"
        )
    
    with col4:
        st.metric(
            "💰 Custo Total",
            f"R$ {solucao['custo_total']/1000:.0f}k",
            help="Investimento + Operação (VP)"
        )
    
    with col5:
        if solucao['energia_pv_kwh'] > 0:
            percentual_pv = (solucao['energia_pv_kwh'] / 
                           (solucao['energia_comprada_kwh'] + solucao['energia_pv_kwh'])) * 100
        else:
            percentual_pv = 0.0
        
        st.metric(
            "🌞 Energia PV",
            f"{percentual_pv:.1f}%",
            help="Percentual de energia solar"
        )

def exibir_detalhes_solucao(modelo):
    """Exibe detalhes expandíveis da solução"""
    solucao = modelo.solucao
    
    # Abas para organizar informações
    tab1, tab2, tab3, tab4 = st.tabs(["💰 Custos", "⚡ Energia", "☀️ Sistemas PV", "📊 Análise"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🏗️ Investimento")
            st.metric("Estações", f"R$ {sum(modelo.c_CS[l] for l in solucao['estacoes_instaladas']):,.0f}")
            st.metric("Carports PV", f"R$ {sum(modelo.c_PV[k] for k in solucao['carports_instalados'].values()):,.0f}")
            st.metric("**TOTAL**", f"**R$ {solucao['custo_investimento']:,.0f}**")
        
        with col2:
            st.markdown("#### ⚡ Operação (VP)")
            st.metric(f"Horizonte {modelo.Delta_h} anos", f"R$ {solucao['custo_operacao_vp']:,.0f}")
            st.metric("Fator VP", f"{modelo.fator_vp:.4f}")
            
            # Análise de payback aproximado
            if len(solucao['carports_instalados']) > 0:
                economia_anual = solucao['energia_pv_kwh'] * sum(modelo.c_e.values()) / len(modelo.T)
                custo_pv_total = sum(modelo.c_PV[k] for k in solucao['carports_instalados'].values())
                payback = custo_pv_total / economia_anual if economia_anual > 0 else float('inf')
                st.metric("Payback PV (aprox)", f"{payback:.1f} anos" if payback < 50 else "N/A")
    
    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🔌 Compra da Rede")
            st.metric("Energia comprada", f"{solucao['energia_comprada_kwh']:,.0f} kWh")
            custo_medio_kwh = sum(modelo.c_e.values()) / len(modelo.c_e)
            st.metric("Custo médio", f"R$ {custo_medio_kwh:.2f}/kWh")
        
        with col2:
            st.markdown("#### ☀️ Geração PV")
            st.metric("Energia gerada", f"{solucao['energia_pv_kwh']:,.0f} kWh")
            st.metric("Exportada (NM)", f"{solucao['energia_exportada_kwh']:,.0f} kWh")
            st.metric("Importada (NM)", f"{solucao['energia_importada_kwh']:,.0f} kWh")
            st.metric("Créditos finais", f"{solucao['creditos_finais_kwh']:,.0f} kWh")
    
    with tab3:
        if solucao['carports_instalados']:
            st.markdown("#### 🌞 Carports Fotovoltaicos Instalados")
            
            dados_pv = []
            for link_id, tipo_pv in solucao['carports_instalados'].items():
                geracao_total = sum(
                    modelo.P_k[tipo_pv] * modelo.sh.get((link_id, t), 0) 
                    for t in modelo.T
                )
                
                dados_pv.append({
                    'Link': link_id,
                    'Tipo': tipo_pv,
                    'Potência (kW)': modelo.P_k[tipo_pv],
                    'Área (m²)': modelo.a_k[tipo_pv],
                    'Custo (R$)': f"{modelo.c_PV[tipo_pv]:,.0f}",
                    'Geração/dia (kWh)': f"{geracao_total:,.0f}"
                })
            
            df_pv = pd.DataFrame(dados_pv)
            st.dataframe(df_pv, use_container_width=True, hide_index=True)
            
            # Estatísticas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Potência total instalada", 
                         f"{sum(modelo.P_k[k] for k in solucao['carports_instalados'].values())} kW")
            with col2:
                st.metric("Área total", 
                         f"{sum(modelo.a_k[k] for k in solucao['carports_instalados'].values())} m²")
            with col3:
                st.metric("Investimento PV", 
                         f"R$ {sum(modelo.c_PV[k] for k in solucao['carports_instalados'].values()):,.0f}")
        else:
            st.info("Nenhum sistema PV foi instalado nesta solução.")
    
    with tab4:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📊 Cobertura Espacial")
            st.metric("Links totais", len(modelo.L))
            st.metric("Links cobertos", solucao['num_links_cobertos'])
            st.metric("Taxa de cobertura", f"{solucao['taxa_cobertura_%']:.1f}%")
            st.metric("Raio de cobertura", f"{modelo.raio_cobertura_km} km")
        
        with col2:
            st.markdown("#### ⚖️ Parâmetros do Modelo")
            st.metric("f* (ótimo)", f"{solucao['f_otimo']:.6f}")
            st.metric("Gap MIP", f"{solucao['gap_%']:.2f}%")
            st.metric("Tempo de solução", f"{solucao['tempo_s']:.2f}s")
            st.metric("Peso γ", modelo.gamma)

def main():
    """Função principal do dashboard"""
    inicializar_sessao()
    
    # Título
    st.markdown('<h1 class="main-title">⚡ FCSA MILP - Otimização de Eletropostos</h1>', 
                unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Modelo de Caio dos Santos - Integração PV + Net-Metering + Cobertura Espacial</p>', 
                unsafe_allow_html=True)
    
    # Sidebar
    problema_selecionado = criar_sidebar()
    
    if not problema_selecionado:
        st.warning("⚠️ Configure os problemas na pasta `dados/` para continuar.")
        return
    
    # Verificar se há modelo resolvido
    if st.session_state.modelo_resolvido and st.session_state.modelo_atual:
        modelo = st.session_state.modelo_atual
        
        # Métricas principais
        exibir_metricas_principais(modelo.solucao)
        
        st.markdown("---")
        
        # Layout com mapa e detalhes
        col_mapa, col_detalhes = st.columns([2, 1])
        
        with col_mapa:
            st.markdown("### 🗺️ Mapa da Solução")
            mapa = criar_mapa_resultados(modelo)
            st_folium(mapa, width=None, height=500, returned_objects=[])
        
        with col_detalhes:
            st.markdown("### 📋 Resumo")
            
            st.markdown("#### ⚡ Estações Instaladas")
            for est in modelo.solucao['estacoes_instaladas']:
                tem_pv = est in modelo.solucao['carports_instalados']
                st.markdown(f"- {'☀️' if tem_pv else '⚡'} **Link {est}**")
            
            st.markdown("---")
            st.markdown("#### 📊 Indicadores")
            
            eficiencia_economica = (modelo.solucao['num_links_cobertos'] / 
                                   (modelo.solucao['custo_total']/1000))
            st.metric("Eficiência", f"{eficiencia_economica:.2f} links/R$1k")
            
            if modelo.solucao['energia_pv_kwh'] > 0:
                reducao_grid = (modelo.solucao['energia_pv_kwh'] / 
                               (modelo.solucao['energia_comprada_kwh'] + 
                                modelo.solucao['energia_pv_kwh']) * 100)
                st.metric("Redução Grid", f"{reducao_grid:.1f}%")
        
        st.markdown("---")
        
        # Detalhes expandíveis
        exibir_detalhes_solucao(modelo)
        
    else:
        # Instruções iniciais
        st.info("""
        ### 👈 Como usar:
        
        1. **Selecione um problema** no painel lateral
        2. **Revise os parâmetros** (configurados no arquivo YAML)
        3. **Clique em "Executar Otimização"**
        4. **Aguarde** enquanto o solver CPLEX encontra a solução ótima
        5. **Analise os resultados** no mapa e gráficos
        
        ---
        
        ### 📊 Sobre o modelo:
        
        Este dashboard implementa o **modelo FCSA MILP** da tese de Caio dos Santos (Unicamp, 2021),
        que otimiza a localização de estações de recarga rápida considerando:
        
        - ⚡ **Cobertura espacial** com raio configurável
        - ☀️ **Integração de sistemas fotovoltaicos**
        - 💡 **Net-metering** para aproveitamento de energia
        - 💰 **Otimização econômica** (investimento + operação)
        - 🚗 **Benefícios de transporte** (acessibilidade + demanda)
        
        **Método lexicográfico em 2 passos:**
        1. Minimizar `f = Σ(xl·ρl·βl)` → Melhor cobertura
        2. Minimizar custos mantendo `f = f*` → Economia
        """)
        
        # Mostrar problemas disponíveis
        st.markdown("### 📁 Problemas Disponíveis")
        problemas = listar_problemas_disponiveis()
        
        for prob in problemas:
            info = carregar_info_problema(f'dados/{prob}')
            if info:
                with st.expander(f"📂 {prob}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Nome:** {info['nome']}")
                        st.markdown(f"**Cidade:** {info['cidade']}")
                        st.markdown(f"**Links:** {info['num_links']}")
                    with col2:
                        st.markdown(f"**Raio:** {info['raio_cobertura']} km")
                        st.markdown(f"**Horizonte:** {info['horizonte']} anos")
                        st.markdown(f"**Gap:** {info['mip_gap']*100:.1f}%")
                    st.markdown(f"*{info['descricao']}*")

if __name__ == "__main__":
    main()