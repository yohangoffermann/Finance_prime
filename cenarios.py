import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Configuração da página
st.set_page_config(page_title="Análise de Fluxo de Caixa", layout="wide")

# Tema personalizado
st.markdown("""
<style>
    .reportview-container {
        background: #ffffff
    }
    .sidebar .sidebar-content {
        background: #ffffff
    }
    .Widget>label {
        color: #808495;
        font-family: "Source Sans Pro", sans-serif;
    }
    .stButton>button {
        color: #ffffff;
        background-color: #0068c9;
        border-radius: 4px;
    }
    .stTextInput>div>div>input {
        color: #31333F;
    }
</style>
""", unsafe_allow_html=True)

def calcular_fluxo_auto_financiado(vgv, custo_construcao, prazo_meses, 
                                   percentual_inicio, percentual_meio, percentual_fim,
                                   percentual_lancamento, percentual_baloes, percentual_parcelas,
                                   prazo_parcelas):
    fluxo = pd.DataFrame(index=range(prazo_meses), columns=['Mês', 'Receitas', 'Custos', 'Saldo Mensal', 'Saldo Acumulado'])
    
    custos = np.zeros(prazo_meses)
    tercio_obra = prazo_meses // 3
    custos[:tercio_obra] = custo_construcao * percentual_inicio / 100 / tercio_obra
    custos[tercio_obra:2*tercio_obra] = custo_construcao * percentual_meio / 100 / tercio_obra
    custos[2*tercio_obra:] = custo_construcao * percentual_fim / 100 / (prazo_meses - 2*tercio_obra)
    fluxo['Custos'] = custos
    
    fluxo['Receitas'] = 0
    fluxo.loc[0, 'Receitas'] += vgv * percentual_lancamento / 100
    
    valor_baloes = vgv * percentual_baloes / 100
    num_baloes = 3
    for i in range(1, num_baloes + 1):
        mes_balao = i * prazo_meses // (num_baloes + 1)
        fluxo.loc[mes_balao, 'Receitas'] += valor_baloes / num_baloes
    
    valor_parcelas = vgv * percentual_parcelas / 100
    parcela_mensal = valor_parcelas / min(prazo_parcelas, prazo_meses)
    fluxo.loc[:min(prazo_parcelas, prazo_meses)-1, 'Receitas'] += parcela_mensal
    
    fluxo['Saldo Mensal'] = fluxo['Receitas'] - fluxo['Custos']
    fluxo['Saldo Acumulado'] = fluxo['Saldo Mensal'].cumsum()
    
    fluxo['Mês'] = range(1, prazo_meses + 1)
    
    return fluxo

def mostrar_graficos(fluxo):
    colors = ["#0068c9", "#83c9ff", "#ff2b2b", "#ffabab", "#29b09d"]

    fig = make_subplots(rows=2, cols=2, 
                        subplot_titles=("Receitas e Custos", "Fluxo de Caixa", 
                                        "Saldo Acumulado", "Comparação"),
                        vertical_spacing=0.1,
                        horizontal_spacing=0.05)

    # Receitas e Custos
    fig.add_trace(go.Scatter(x=fluxo['Mês'], y=fluxo['Receitas'], name='Receitas', 
                             fill='tozeroy', mode='none', fillcolor=f'rgba(0, 104, 201, 0.7)'), row=1, col=1)
    fig.add_trace(go.Scatter(x=fluxo['Mês'], y=-fluxo['Custos'], name='Custos', 
                             fill='tozeroy', mode='none', fillcolor=f'rgba(255, 43, 43, 0.7)'), row=1, col=1)

    # Fluxo de Caixa
    fig.add_trace(go.Scatter(x=fluxo['Mês'], y=fluxo['Saldo Mensal'], name='Saldo Mensal', 
                             line=dict(color=colors[2])), row=1, col=2)

    # Saldo Acumulado
    fig.add_trace(go.Scatter(x=fluxo['Mês'], y=fluxo['Saldo Acumulado'], name='Saldo Acumulado', 
                             line=dict(color=colors[3])), row=2, col=1)

    # Comparação
    fig.add_trace(go.Scatter(x=fluxo['Mês'], y=fluxo['Receitas'], name='Receitas', 
                             line=dict(color=colors[0])), row=2, col=2)
    fig.add_trace(go.Scatter(x=fluxo['Mês'], y=-fluxo['Custos'], name='Custos', 
                             line=dict(color=colors[2])), row=2, col=2)

    fig.update_layout(
        title_text="Análise de Fluxo de Caixa",
        height=800,
        font=dict(family="Source Sans Pro, sans-serif", size=12, color="#808495"),
        plot_bgcolor='white',
        paper_bgcolor='white',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=60, b=40)
    )

    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        title_text="",
        tickfont=dict(size=12, color="#808495"),
        tickmode='linear',
        dtick=6
    )

    fig.update_yaxes(
        showgrid=True,
        gridcolor='#e6eaf1',
        zeroline=False,
        title_text="",
        tickfont=dict(size=12, color="#808495")
    )

    st.plotly_chart(fig, use_container_width=True)

# Menu de navegação lateral
with st.sidebar:
    selected = option_menu(
        "Menu Principal", ["Home", "Parâmetros", "Fluxo de Caixa", "Análise"],
        icons=["house", "gear", "cash", "graph-up"],
        menu_icon="cast", default_index=0
    )

# Variáveis de estado para armazenar os inputs
if 'vgv' not in st.session_state:
    st.session_state.vgv = 35.0
if 'custo_construcao_percentual' not in st.session_state:
    st.session_state.custo_construcao_percentual = 70
if 'prazo_meses' not in st.session_state:
    st.session_state.prazo_meses = 48
if 'percentual_inicio' not in st.session_state:
    st.session_state.percentual_inicio = 30
if 'percentual_meio' not in st.session_state:
    st.session_state.percentual_meio = 40
if 'percentual_fim' not in st.session_state:
    st.session_state.percentual_fim = 30
if 'percentual_lancamento' not in st.session_state:
    st.session_state.percentual_lancamento = 20
if 'percentual_baloes' not in st.session_state:
    st.session_state.percentual_baloes = 30
if 'percentual_parcelas' not in st.session_state:
    st.session_state.percentual_parcelas = 50
if 'prazo_parcelas' not in st.session_state:
    st.session_state.prazo_parcelas = 48

# Conteúdo principal
if selected == "Home":
    st.title("Análise de Fluxo de Caixa - Modelo Auto Financiado")
    st.write("Bem-vindo à ferramenta de análise de fluxo de caixa para projetos imobiliários.")
    st.write("Use o menu lateral para navegar entre as diferentes seções.")

elif selected == "Parâmetros":
    st.header("Parâmetros do Projeto")
    
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.vgv = st.number_input('VGV (Valor Geral de Vendas) em milhões R$', value=st.session_state.vgv, step=0.1)
        st.session_state.custo_construcao_percentual = st.slider('Custo de Construção (% do VGV)', 50, 90, st.session_state.custo_construcao_percentual)
        st.session_state.prazo_meses = st.number_input('Prazo de Construção (meses)', value=st.session_state.prazo_meses, step=1)

    with col2:
        st.subheader("Distribuição dos Custos")
        st.session_state.percentual_inicio = st.slider('% Custos no Início da Obra', 0, 100, st.session_state.percentual_inicio)
        st.session_state.percentual_meio = st.slider('% Custos no Meio da Obra', 0, 100, st.session_state.percentual_meio)
        st.session_state.percentual_fim = st.slider('% Custos no Fim da Obra', 0, 100, st.session_state.percentual_fim)
        
        if st.session_state.percentual_inicio + st.session_state.percentual_meio + st.session_state.percentual_fim != 100:
            st.warning("A soma dos percentuais de custos deve ser 100%")

    st.subheader("Distribuição das Vendas")
    col3, col4 = st.columns(2)
    with col3:
        st.session_state.percentual_lancamento = st.slider('% Vendas no Lançamento', 0, 100, st.session_state.percentual_lancamento)
        st.session_state.percentual_baloes = st.slider('% Vendas em Balões', 0, 100, st.session_state.percentual_baloes)
    with col4:
        st.session_state.percentual_parcelas = st.slider('% Vendas em Parcelas', 0, 100, st.session_state.percentual_parcelas)
        st.session_state.prazo_parcelas = st.slider('Prazo das Parcelas (meses)', 1, 120, st.session_state.prazo_parcelas)
    
    if st.session_state.percentual_lancamento + st.session_state.percentual_baloes + st.session_state.percentual_parcelas != 100:
        st.warning("A soma dos percentuais de vendas deve ser 100%")

elif selected == "Fluxo de Caixa":
    st.header("Fluxo de Caixa")
    
    custo_construcao = st.session_state.vgv * st.session_state.custo_construcao_percentual / 100
    fluxo_auto = calcular_fluxo_auto_financiado(
        st.session_state.vgv, custo_construcao, st.session_state.prazo_meses, 
        st.session_state.percentual_inicio, st.session_state.percentual_meio, st.session_state.percentual_fim,
        st.session_state.percentual_lancamento, st.session_state.percentual_baloes, st.session_state.percentual_parcelas,
        st.session_state.prazo_parcelas
    )

    mostrar_graficos(fluxo_auto)

    st.subheader('Fluxo de Caixa Mensal')
    st.dataframe(fluxo_auto)

elif selected == "Análise":
    st.header("Análise do Projeto")
    
    custo_construcao = st.session_state.vgv * st.session_state.custo_construcao_percentual / 100
    fluxo_auto = calcular_fluxo_auto_financiado(
        st.session_state.vgv, custo_construcao, st.session_state.prazo_meses, 
        st.session_state.percentual_inicio, st.session_state.percentual_meio, st.session_state.percentual_fim,
        st.session_state.percentual_lancamento, st.session_state.percentual_baloes, st.session_state.percentual_parcelas,
        st.session_state.prazo_parcelas
    )

    lucro_total = fluxo_auto['Saldo Mensal'].sum()
    margem = (lucro_total / st.session_state.vgv) * 100
    exposicao_maxima = -fluxo_auto['Saldo Acumulado'].min()
    
    saldo_acumulado_positivo = fluxo_auto[fluxo_auto['Saldo Acumulado'] > 0]
    if not saldo_acumulado_positivo.empty:
        mes_payback = saldo_acumulado_positivo.index[0] + 1
        valor_payback = saldo_acumulado_positivo['Saldo Acumulado'].iloc[0]
    else:
        mes_payback = "Não atingido"
        valor_payback = None

    st.subheader('Métricas do Projeto')
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("VGV", f"R$ {st.session_state.vgv:.2f} milhões")
        st.metric("Custo de Construção", f"R$ {custo_construcao:.2f} milhões")
    with col2:
        st.metric("Lucro Total", f"R$ {lucro_total:.2f} milhões")
        st.metric("Margem", f"{margem:.2f}%")
    with col3:
        st.metric("Exposição Máxima de Caixa", f"R$ {exposicao_maxima:.2f} milhões")
        if isinstance(mes_payback, int):
            st.metric("Mês de Payback", f"{mes_payback} (R$ {valor_payback:.2f} milhões)")
        else:
            st.metric("Mês de Payback", mes_payback)

    st.subheader('Análise Detalhada')
    st.write(f"""
    No modelo auto financiado:
    1. O incorporador recebe R$ {st.session_state.vgv * st.session_state.percentual_lancamento / 100:.2f} milhões no lançamento.
    2. R$ {st.session_state.vgv * st.session_state.percentual_baloes / 100:.2f} milhões são recebidos em 3 balões ao longo do projeto.
    3. R$ {st.session_state.vgv * st.session_state.percentual_parcelas / 100:.2f} milhões são recebidos em {st.session_state.prazo_parcelas} parcelas mensais.
    4. Os custos de construção são distribuídos da seguinte forma:
       - {st.session_state.percentual_inicio}% no início da obra
       - {st.session_state.percentual_meio}% no meio da obra
       - {st.session_state.percentual_fim}% no final da obra
    5. A exposição máxima de caixa é de R$ {exposicao_maxima:.2f} milhões, o que representa o momento de maior necessidade de capital no projeto.
    6. O projeto atinge o ponto de equilíbrio (payback) no mês {mes_payback}{f', com um saldo positivo de R$ {valor_payback:.2f} milhões' if isinstance(mes_payback, int) else ''}.
    7. A margem final do projeto é de {margem:.2f}%.
    """)

    mostrar_graficos(fluxo_auto)

if __name__ == "__main__":
    st.sidebar.title("Sobre")
    st.sidebar.info(
        "Esta é uma aplicação de análise de fluxo de caixa "
        "para projetos imobiliários auto financiados. "
        "Desenvolvida com Streamlit."
    )
