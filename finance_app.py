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
            saldo *= (Decimal('1') + indice_correcao_anual)
        
        amortizacao = parcela - (saldo * taxa_admin_mensal)
        saldo -= amortizacao
    
    return max(saldo, Decimal('0')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def aplicar_dropdown(saldo_devedor, valor_dropdown, agio):
    valor_efetivo = valor_dropdown * (Decimal('1') + Decimal(str(agio)) / Decimal('100'))
    return max(saldo_devedor - valor_efetivo, Decimal('0'))

# Função para atualizar o gráfico e métricas
def update_simulation():
    valor_credito = parse_currency(st.session_state.valor_credito)
    valor_lance = parse_currency(st.session_state.valor_lance)
    prazo_meses = st.session_state.prazo_meses
    taxa_admin_anual = Decimal(str(st.session_state.taxa_admin_anual))
    indice_correcao_anual = Decimal(str(st.session_state.indice_correcao_anual))

    parcela_inicial = calcular_parcela(valor_credito - valor_lance, prazo_meses, taxa_admin_anual)
    
    saldos_padrao = [calcular_saldo_devedor(valor_credito - valor_lance, parcela_inicial, taxa_admin_anual, indice_correcao_anual, m) for m in range(prazo_meses + 1)]
    
    saldos_com_dropdowns = saldos_padrao.copy()
    saldo_atual = valor_credito - valor_lance
    for dropdown in sorted(st.session_state.dropdowns, key=lambda x: x['mes']):
        mes = dropdown['mes']
        valor = parse_currency(dropdown['valor'])
        agio = Decimal(str(dropdown['agio']))
        
        saldo_antes_dropdown = calcular_saldo_devedor(saldo_atual, parcela_inicial, taxa_admin_anual, indice_correcao_anual, mes - len(st.session_state.dropdowns) + 1)
        saldo_apos_dropdown = aplicar_dropdown(saldo_antes_dropdown, valor, agio)
        
        for m in range(mes, prazo_meses + 1):
            saldos_com_dropdowns[m] = calcular_saldo_devedor(saldo_apos_dropdown, parcela_inicial, taxa_admin_anual, indice_correcao_anual, m - mes)
        
        saldo_atual = saldo_apos_dropdown
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=list(range(prazo_meses + 1)), y=saldos_padrao, name='Amortização Padrão'))
    fig.add_trace(go.Scatter(x=list(range(prazo_meses + 1)), y=saldos_com_dropdowns, name='Com Dropdowns'))
    
    for dropdown in st.session_state.dropdowns:
        fig.add_annotation(
            x=dropdown['mes'],
            y=saldos_com_dropdowns[dropdown['mes']],
            text=f"Dropdown: {format_currency(parse_currency(dropdown['valor']))}",
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=2,
            arrowcolor="#636363",
            ax=-40,
            ay=-40
        )
    
    fig.update_layout(
        title="Evolução do Saldo Devedor",
        xaxis_title="Meses",
        yaxis_title="Saldo (R$)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.session_state.fig = fig

    st.session_state.saldo_final = saldos_com_dropdowns[-1]
    st.session_state.parcela_inicial = parcela_inicial
    st.session_state.reducao_prazo = prazo_meses - next((i for i, saldo in enumerate(saldos_com_dropdowns) if saldo == 0), prazo_meses)

# Interface do usuário
st.title("Constructa - Simulador de Consórcio com Múltiplos Dropdowns")

# Sidebar para inputs base
with st.sidebar:
    st.header("Parâmetros do Consórcio")
    
    if 'valor_credito' not in st.session_state:
        st.session_state.valor_credito = "R$ 1.000.000,00"
    valor_credito = st.text_input("Valor do Crédito", value=st.session_state.valor_credito, key="input_valor_credito")
    if valor_credito != st.session_state.valor_credito:
        st.session_state.valor_credito = format_input_currency(valor_credito)

    prazo_meses = st.number_input("Prazo (meses)", min_value=12, max_value=240, value=180, key="prazo_meses")
    taxa_admin_anual = st.number_input("Taxa de Administração Anual (%)", min_value=0.0, value=1.20, step=0.01, key="taxa_admin_anual")
    indice_correcao_anual = st.number_input("Índice de Correção Anual (%)", min_value=0.0, value=5.0, step=0.1, key="indice_correcao_anual")

    if 'valor_lance' not in st.session_state:
        st.session_state.valor_lance = "R$ 200.000,00"
    valor_lance = st.text_input("Valor do Lance", value=st.session_state.valor_lance, key="input_valor_lance")
    if valor_lance != st.session_state.valor_lance:
        st.session_state.valor_lance = format_input_currency(valor_lance)

# Corpo principal para inputs operacionais
st.subheader("Simulação de Dropdowns")

# Inicialização da lista de dropdowns
if 'dropdowns' not in st.session_state:
    st.session_state.dropdowns = []

# Inputs para adicionar novo dropdown
col1, col2, col3, col4 = st.columns(4)
with col1:
    novo_valor_dropdown = st.text_input("Valor do Dropdown", value="R$ 100.000,00", key="novo_valor_dropdown")
with col2:
    novo_agio = st.number_input("Ágio (%)", min_value=0.0, value=5.0, step=0.1, key="novo_agio")
with col3:
    novo_mes_dropdown = st.number_input("Mês do Dropdown", min_value=1, value=60, step=1, key="novo_mes_dropdown")
with col4:
    if st.button("Adicionar Dropdown"):
        st.session_state.dropdowns.append({
            "valor": format_input_currency(novo_valor_dropdown),
            "agio": novo_agio,
            "mes": novo_mes_dropdown
        })
        st.experimental_rerun()

# Exibir dropdowns adicionados
if st.session_state.dropdowns:
    st.write("Dropdowns Adicionados:")
    for i, dropdown in enumerate(st.session_state.dropdowns):
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
        with col1:
            st.write(f"Dropdown {i+1}: {dropdown['valor']}")
        with col2:
            st.write(f"Ágio: {dropdown['agio']}%")
        with col3:
            st.write(f"Mês: {dropdown['mes']}")
        with col4:
            if st.button(f"Remover {i+1}"):
                st.session_state.dropdowns.pop(i)
                st.experimental_rerun()

# Atualizar simulação em tempo real
if all(key in st.session_state for key in ['valor_credito', 'prazo_meses', 'taxa_admin_anual', 'indice_correcao_anual', 'valor_lance']):
    update_simulation()

# Exibir gráfico
if 'fig' in st.session_state:
    st.plotly_chart(st.session_state.fig, use_container_width=True)

# Exibir métricas
if all(key in st.session_state for key in ['saldo_final', 'parcela_inicial', 'reducao_prazo']):
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Saldo Devedor Final", format_currency(st.session_state.saldo_final))
        st.metric("Parcela Inicial", format_currency(st.session_state.parcela_inicial))
    with col2:
        st.metric("Redução Estimada no Prazo", f"{st.session_state.reducao_prazo} meses")

# Informações adicionais
st.subheader("Detalhes da Simulação")
st.write(f"Valor do Crédito: {st.session_state.valor_credito}")
st.write(f"Valor do Lance: {st.session_state.valor_lance}")
st.write(f"Crédito Efetivo: {format_currency(parse_currency(st.session_state.valor_credito) - parse_currency(st.session_state.valor_lance))}")

st.sidebar.info("Constructa - Módulo de Consórcio v1.4")
