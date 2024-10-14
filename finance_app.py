import streamlit as st
import plotly.graph_objects as go
from decimal import Decimal, ROUND_HALF_UP

# Configuração da página
st.set_page_config(page_title="Constructa - Módulo de Consórcio", layout="wide")

# Funções auxiliares
def format_currency(value):
    if isinstance(value, str):
        value = parse_currency(value)
    return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

def parse_currency(value):
    if isinstance(value, (int, float, Decimal)):
        return Decimal(str(value))
    return Decimal(value.replace('R$', '').replace('.', '').replace(',', '.').strip())

def format_input_currency(value):
    numeric_value = ''.join(filter(str.isdigit, value))
    if numeric_value:
        return format_currency(int(numeric_value) / 100)
    return "R$ 0,00"

# Funções de cálculo
def calcular_parcela(valor_credito, prazo_meses, taxa_admin_anual):
    valor_credito = Decimal(str(valor_credito))
    prazo_meses = Decimal(str(prazo_meses))
    taxa_admin_mensal = Decimal(str(taxa_admin_anual)) / Decimal('12') / Decimal('100')
    
    parcela_fundo = valor_credito / prazo_meses
    parcela_admin = valor_credito * taxa_admin_mensal
    return (parcela_fundo + parcela_admin).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def calcular_saldo_devedor(valor_credito, parcela, taxa_admin_anual, indice_correcao_anual, meses_pagos):
    valor_credito = Decimal(str(valor_credito))
    parcela = Decimal(str(parcela))
    taxa_admin_mensal = Decimal(str(taxa_admin_anual)) / Decimal('12') / Decimal('100')
    indice_correcao_anual = Decimal(str(indice_correcao_anual)) / Decimal('100')
    
    saldo = valor_credito
    for mes in range(1, meses_pagos + 1):
        if mes % 12 == 1 and mes > 12:  # Aplica correção no início de cada ano, a partir do segundo ano
            saldo *= (1 + indice_correcao_anual)
        
        amortizacao = parcela - (saldo * taxa_admin_mensal)
        saldo -= amortizacao
    
    return max(saldo, Decimal('0')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def aplicar_dropdown(saldo_devedor, valor_dropdown, agio):
    valor_efetivo = valor_dropdown * (1 + Decimal(str(agio)) / Decimal('100'))
    return max(saldo_devedor - valor_efetivo, Decimal('0'))

# Função para atualizar o gráfico e métricas
def update_simulation():
    valor_credito = parse_currency(st.session_state.valor_credito)
    valor_lance = parse_currency(st.session_state.valor_lance)
    prazo_meses = st.session_state.prazo_meses
    taxa_admin_anual = st.session_state.taxa_admin_anual
    indice_correcao_anual = st.session_state.indice_correcao_anual
    valor_dropdown = parse_currency(st.session_state.valor_dropdown)
    agio = st.session_state.agio
    mes_dropdown = st.session_state.mes_dropdown

    parcela_inicial = calcular_parcela(valor_credito - valor_lance, prazo_meses, taxa_admin_anual)
    
    saldos_padrao = [calcular_saldo_devedor(valor_credito - valor_lance, parcela_inicial, taxa_admin_anual, indice_correcao_anual, m) for m in range(prazo_meses + 1)]
    
    saldos_com_dropdown = saldos_padrao.copy()
    if mes_dropdown < prazo_meses:
        saldo_antes_dropdown = calcular_saldo_devedor(valor_credito - valor_lance, parcela_inicial, taxa_admin_anual, indice_correcao_anual, mes_dropdown)
        saldo_apos_dropdown = aplicar_dropdown(saldo_antes_dropdown, valor_dropdown, agio)
        for m in range(mes_dropdown, prazo_meses + 1):
            saldos_com_dropdown[m] = calcular_saldo_devedor(saldo_apos_dropdown, parcela_inicial, taxa_admin_anual, indice_correcao_anual, m - mes_dropdown)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=list(range(prazo_meses + 1)), y=saldos_padrao, name='Amortização Padrão'))
    fig.add_trace(go.Scatter(x=list(range(prazo_meses + 1)), y=saldos_com_dropdown, name='Com Dropdown'))
    fig.update_layout(
        title="Evolução do Saldo Devedor",
        xaxis_title="Meses",
        yaxis_title="Saldo (R$)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.session_state.fig = fig

    saldo_atual = saldos_com_dropdown[mes_dropdown]
    parcela_atualizada = calcular_parcela(saldo_atual, prazo_meses - mes_dropdown, taxa_admin_anual)
    
    st.session_state.saldo_atual = saldo_atual
    st.session_state.parcela_atualizada = parcela_atualizada
    st.session_state.parcela_inicial = parcela_inicial
    st.session_state.reducao_parcela = parcela_inicial - parcela_atualizada
    
    prazo_reduzido = next((i for i, saldo in enumerate(saldos_com_dropdown) if saldo == 0), prazo_meses) - 1
    st.session_state.reducao_prazo = prazo_meses - prazo_reduzido

# Interface do usuário
st.title("Constructa - Simulador de Consórcio com Dropdown")

# Sidebar para inputs base
with st.sidebar:
    st.header("Parâmetros do Consórcio")
    
    # Valor do Crédito
    if 'valor_credito' not in st.session_state:
        st.session_state.valor_credito = "R$ 1.000.000,00"
    
    valor_credito = st.text_input("Valor do Crédito", value=st.session_state.valor_credito, key="input_valor_credito")
    if valor_credito != st.session_state.valor_credito:
        st.session_state.valor_credito = format_input_currency(valor_credito)

    # Prazo
    prazo_meses = st.number_input("Prazo (meses)", min_value=12, max_value=240, value=180, key="prazo_meses")
    
    # Taxa de Administração
    taxa_admin_anual = st.number_input("Taxa de Administração Anual (%)", min_value=0.0, value=1.20, step=0.01, key="taxa_admin_anual")
    
    # Índice de Correção
    indice_correcao_anual = st.number_input("Índice de Correção Anual (%)", min_value=0.0, value=5.0, step=0.1, key="indice_correcao_anual")

    # Valor do Lance
    if 'valor_lance' not in st.session_state:
        st.session_state.valor_lance = "R$ 200.000,00"
    
    valor_lance = st.text_input("Valor do Lance", value=st.session_state.valor_lance, key="input_valor_lance")
    if valor_lance != st.session_state.valor_lance:
        st.session_state.valor_lance = format_input_currency(valor_lance)

# Corpo principal para inputs operacionais
st.subheader("Simulação de Dropdown")
col1, col2, col3 = st.columns(3)
with col1:
    if 'valor_dropdown' not in st.session_state:
        st.session_state.valor_dropdown = "R$ 100.000,00"
    
    valor_dropdown = st.text_input("Valor do Dropdown", value=st.session_state.valor_dropdown, key="input_valor_dropdown")
    if valor_dropdown != st.session_state.valor_dropdown:
        st.session_state.valor_dropdown = format_input_currency(valor_dropdown)

with col2:
    agio = st.number_input("Ágio (%)", min_value=0.0, value=5.0, step=0.1, key="agio")
with col3:
    mes_dropdown = st.number_input("Mês do Dropdown", min_value=1, value=60, step=1, key="mes_dropdown")

# Atualizar simulação em tempo real
if all(key in st.session_state for key in ['valor_credito', 'prazo_meses', 'taxa_admin_anual', 'indice_correcao_anual', 'valor_lance', 'valor_dropdown', 'agio', 'mes_dropdown']):
    update_simulation()

# Exibir gráfico
if 'fig' in st.session_state:
    st.plotly_chart(st.session_state.fig, use_container_width=True)

# Exibir métricas
if all(key in st.session_state for key in ['saldo_atual', 'parcela_atualizada', 'parcela_inicial', 'reducao_parcela', 'reducao_prazo']):
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Saldo Devedor Atual", format_currency(st.session_state.saldo_atual))
        st.metric("Parcela Atualizada", format_currency(st.session_state.parcela_atualizada))
    with col2:
        st.metric("Parcela Original", format_currency(st.session_state.parcela_inicial))
        st.metric("Redução na Parcela", format_currency(st.session_state.reducao_parcela))

    st.metric("Redução Estimada no Prazo", f"{st.session_state.reducao_prazo} meses")

    # Informações adicionais
    st.subheader("Detalhes da Simulação")
    st.write(f"Valor do Crédito: {st.session_state.valor_credito}")
    st.write(f"Valor do Lance: {st.session_state.valor_lance}")
    st.write(f"Crédito Efetivo: {format_currency(parse_currency(st.session_state.valor_credito) - parse_currency(st.session_state.valor_lance))}")
    st.write(f"Valor do Dropdown: {st.session_state.valor_dropdown}")
    st.write(f"Valor Efetivo do Dropdown (com ágio): {format_currency(parse_currency(st.session_state.valor_dropdown) * (1 + st.session_state.agio/100))}")

st.sidebar.info("Constructa - Módulo de Consórcio v1.3")
