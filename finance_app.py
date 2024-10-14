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
def calcular_parcela(valor_credito, prazo_meses, taxa_admin_anual, indice_correcao_anual):
    valor_credito = Decimal(str(valor_credito))
    prazo_meses = Decimal(str(prazo_meses))
    taxa_admin_mensal = Decimal(str(taxa_admin_anual)) / Decimal('12') / Decimal('100')
    indice_correcao_mensal = (Decimal('1') + Decimal(str(indice_correcao_anual)) / Decimal('100')) ** (Decimal('1') / Decimal('12')) - Decimal('1')
    
    taxa_efetiva = taxa_admin_mensal + indice_correcao_mensal
    fator = (Decimal('1') - (Decimal('1') + taxa_efetiva) ** (-prazo_meses)) / taxa_efetiva
    
    parcela = valor_credito / fator
    return parcela.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def calcular_saldo_devedor(valor_credito, parcela, taxa_admin_anual, indice_correcao_anual, meses_pagos):
    valor_credito = Decimal(str(valor_credito))
    parcela = Decimal(str(parcela))
    taxa_admin_mensal = Decimal(str(taxa_admin_anual)) / Decimal('12') / Decimal('100')
    indice_correcao_anual = Decimal(str(indice_correcao_anual)) / Decimal('100')
    
    saldo = valor_credito
    for mes in range(1, meses_pagos + 1):
        if mes % 12 == 1 and mes > 12:  # Aplica correção no início de cada ano, a partir do segundo ano
            saldo *= (Decimal('1') + indice_correcao_anual)
        
        juros_admin = saldo * taxa_admin_mensal
        amortizacao = parcela - juros_admin
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

    parcela_inicial = calcular_parcela(valor_credito - valor_lance, prazo_meses, taxa_admin_anual, indice_correcao_anual)
    
    saldos_padrao = [calcular_saldo_devedor(valor_credito - valor_lance, parcela_inicial, taxa_admin_anual, indice_correcao_anual, m) for m in range(prazo_meses + 1)]
    
    saldos_com_dropdowns = saldos_padrao.copy()
    saldo_atual = valor_credito - valor_lance
    ultimo_mes_dropdown = 0
    for dropdown in st.session_state.dropdowns:
        mes = dropdown['mes']
        valor = parse_currency(dropdown['valor'])
        agio = Decimal(str(dropdown['agio']))
        
        saldo_antes_dropdown = calcular_saldo_devedor(saldo_atual, parcela_inicial, taxa_admin_anual, indice_correcao_anual, mes - ultimo_mes_dropdown)
        saldo_apos_dropdown = aplicar_dropdown(saldo_antes_dropdown, valor, agio)
        
        for m in range(mes, prazo_meses + 1):
            saldos_com_dropdowns[m] = calcular_saldo_devedor(saldo_apos_dropdown, parcela_inicial, taxa_admin_anual, indice_correcao_anual, m - mes)
        
        saldo_atual = saldo_apos_dropdown
        ultimo_mes_dropdown = mes

    # Calcular saldo e parcela no momento do último dropdown
    if st.session_state.dropdowns:
        ultimo_mes = st.session_state.dropdowns[-1]['mes']
        st.session_state.saldo_padrao_ultimo_dropdown = saldos_padrao[ultimo_mes]
        st.session_state.parcela_padrao = parcela_inicial
        st.session_state.saldo_com_dropdown_ultimo = saldos_com_dropdowns[ultimo_mes]
        st.session_state.parcela_com_dropdown = calcular_parcela(saldos_com_dropdowns[ultimo_mes], prazo_meses - ultimo_mes, taxa_admin_anual, indice_correcao_anual)
    else:
        ultimo_mes = 0
        st.session_state.saldo_padrao_ultimo_dropdown = valor_credito - valor_lance
        st.session_state.parcela_padrao = parcela_inicial
        st.session_state.saldo_com_dropdown_ultimo = valor_credito - valor_lance
        st.session_state.parcela_com_dropdown = parcela_inicial

    # Calcular relações percentuais parcela/saldo devedor
    st.session_state.relacao_parcela_saldo_padrao = (st.session_state.parcela_padrao / st.session_state.saldo_padrao_ultimo_dropdown) * 100
    st.session_state.relacao_parcela_saldo_com_dropdown = (st.session_state.parcela_com_dropdown / st.session_state.saldo_com_dropdown_ultimo) * 100

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=list(range(prazo_meses + 1)), y=saldos_padrao, name='Amortização Padrão'))
    fig.add_trace(go.Scatter(x=list(range(prazo_meses + 1)), y=saldos_com_dropdowns, name='Com Dropdowns'))
    
    for dropdown in st.session_state.dropdowns:
        fig.add_annotation(
            x=dropdown['mes'],
            y=saldos_com_dropdowns[dropdown['mes']],
            text=f"Dropdown: {dropdown['valor']}",
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
        novo_dropdown = {
            "valor": format_input_currency(novo_valor_dropdown),
            "agio": novo_agio,
            "mes": novo_mes_dropdown
        }
        if not any(d['mes'] == novo_mes_dropdown for d in st.session_state.dropdowns):
            st.session_state.dropdowns.append(novo_dropdown)
            st.session_state.dropdowns.sort(key=lambda x: x['mes'])
        else:
            st.error(f"Já existe um dropdown no mês {novo_mes_dropdown}. Escolha outro mês.")

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

# Exibir métricas acima do gráfico
if all(key in st.session_state for key in ['saldo_padrao_ultimo_dropdown', 'parcela_padrao', 'relacao_parcela_saldo_padrao']):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Saldo Devedor (Amortização Padrão)", format_currency(st.session_state.saldo_padrao_ultimo_dropdown))
    with col2:
        st.metric("Parcela (Amortização Padrão)", format_currency(st.session_state.parcela_padrao))
    with col3:
        st.metric("Relação Parcela/Saldo (Amortização Padrão)", f"{st.session_state.relacao_parcela_saldo_padrao:.2f}%")

# Exibir gráfico
if 'fig' in st.session_state:
    st.plotly_chart(st.session_state.fig, use_container_width=True)

# Exibir métricas abaixo do gráfico
if all(key in st.session_state for key in ['saldo_com_dropdown_ultimo', 'parcela_com_dropdown', 'relacao_parcela_saldo_com_dropdown']):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Saldo Devedor (Com Dropdowns)", format_currency(st.session_state.saldo_com_dropdown_ultimo))
    with col2:
        st.metric("Parcela (Com Dropdowns)", format_currency(st.session_state.parcela_com_dropdown))
    with col3:
        st.metric("Relação Parcela/Saldo (Com Dropdowns)", f"{st.session_state.relacao_parcela_saldo_com_dropdown:.2f}%")

# Informações adicionais
st.subheader("Detalhes da Simulação")
st.write(f"Valor do Crédito: {st.session_state.valor_credito}")
st.write(f"Valor do Lance: {st.session_state.valor_lance}")
st.write(f"Crédito Efetivo: {format_currency(parse_currency(st.session_state.valor_credito) - parse_currency(st.session_state.valor_lance))}")

st.sidebar.info("Constructa - Módulo de Consórcio v1.8")
