import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP

# Configuração da página
st.set_page_config(page_title="Constructa MVP", layout="wide")

# Funções auxiliares
def format_currency(value):
    if isinstance(value, str):
        value = parse_currency(value)
    return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

def parse_currency(value):
    if isinstance(value, (int, float, Decimal)):
        return Decimal(str(value))
    return Decimal(value.replace('R$', '').replace('.', '').replace(',', '.').strip())

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

def gerar_perfil(valor_total, prazo, perfil):
    valor_total = Decimal(str(valor_total))
    prazo = int(prazo)
    if perfil == 'Linear':
        return [valor_total / prazo] * prazo
    elif perfil == 'Front-loaded':
        meio = prazo // 2
        return [valor_total * Decimal('0.6') / Decimal(str(meio))] * meio + \
               [valor_total * Decimal('0.4') / Decimal(str(prazo - meio))] * (prazo - meio)
    else:  # Back-loaded
        meio = prazo // 2
        return [valor_total * Decimal('0.4') / Decimal(str(meio))] * meio + \
               [valor_total * Decimal('0.6') / Decimal(str(prazo - meio))] * (prazo - meio)

def calcular_fluxo_caixa(vgv, orcamento, prazo, perfil_vendas, perfil_despesas):
    receitas = gerar_perfil(vgv, prazo, perfil_vendas)
    despesas = gerar_perfil(orcamento, prazo, perfil_despesas)
    return [receitas[i] - despesas[i] for i in range(prazo)]

def calcular_vpl(fluxo_caixa, taxa_desconto):
    taxa_desconto = Decimal(str(taxa_desconto)) / Decimal('100')
    return sum(Decimal(str(valor)) / (1 + taxa_desconto) ** Decimal(str(i)) for i, valor in enumerate(fluxo_caixa))

def aplicar_dropdown(saldo_devedor, valor_dropdown, agio):
    valor_efetivo = valor_dropdown * (1 + Decimal(str(agio)) / Decimal('100'))
    return max(saldo_devedor - valor_efetivo, Decimal('0'))

def calcular_tir(fluxo_caixa, precisao=0.0001):
    def vpn(taxa):
        return sum(valor / (1 + taxa) ** i for i, valor in enumerate(fluxo_caixa))
    
    taxa_baixa, taxa_alta = -0.99, 0.99
    while taxa_alta - taxa_baixa > precisao:
        taxa_media = (taxa_baixa + taxa_alta) / 2
        if vpn(taxa_media) > 0:
            taxa_baixa = taxa_media
        else:
            taxa_alta = taxa_media
    return (taxa_baixa + taxa_alta) / 2

def calcular_fluxo_caixa_com_consorcio(fluxo_caixa_original, valor_credito, parcela, prazo_meses):
    fluxo_com_consorcio = fluxo_caixa_original.copy()
    fluxo_com_consorcio[0] += valor_credito  # Entrada do crédito no início
    for i in range(min(len(fluxo_com_consorcio), prazo_meses)):
        fluxo_com_consorcio[i] -= parcela  # Saída das parcelas
    return fluxo_com_consorcio

# Função para atualizar todos os gráficos e métricas
def update_all():
    valor_credito = Decimal(str(st.session_state.valor_credito))
    prazo_meses = st.session_state.prazo_meses
    taxa_admin_anual = st.session_state.taxa_admin_anual
    indice_correcao_anual = st.session_state.indice_correcao_anual
    valor_lance = Decimal(str(st.session_state.valor_lance))
    vgv = Decimal(str(st.session_state.vgv))
    orcamento = Decimal(str(st.session_state.orcamento))
    prazo_empreendimento = st.session_state.prazo_empreendimento
    perfil_vendas = st.session_state.perfil_vendas
    perfil_despesas = st.session_state.perfil_despesas
    taxa_desconto_vpl = st.session_state.taxa_desconto_vpl

    # Cálculos do consórcio
    parcela = calcular_parcela(valor_credito, prazo_meses, taxa_admin_anual)
    credito_novo = valor_credito - valor_lance
    relacao_parcela_credito = (parcela / credito_novo) * Decimal('100')

    # Cálculos do fluxo de caixa
    fluxo_caixa = calcular_fluxo_caixa(vgv, orcamento, prazo_empreendimento, perfil_vendas, perfil_despesas)
    vpl = calcular_vpl(fluxo_caixa, taxa_desconto_vpl)
    
    # Cálculos do fluxo de caixa com consórcio
    fluxo_caixa_com_consorcio = calcular_fluxo_caixa_com_consorcio(fluxo_caixa, valor_credito, parcela, prazo_meses)
    vpl_com_consorcio = calcular_vpl(fluxo_caixa_com_consorcio, taxa_desconto_vpl)
    
    # Cálculo da TIR
    tir = calcular_tir(fluxo_caixa)
    tir_com_consorcio = calcular_tir(fluxo_caixa_com_consorcio)

    # Atualizar gráfico de fluxo de caixa
    fig_fluxo.data[0].x = list(range(1, len(fluxo_caixa) + 1))
    fig_fluxo.data[0].y = fluxo_caixa
    fluxo_chart.plotly_chart(fig_fluxo, use_container_width=True)

    # Atualizar tabela de fluxo de caixa
    df_fluxo = pd.DataFrame({
        'Mês': range(1, len(fluxo_caixa) + 1),
        'Fluxo de Caixa': [format_currency(fc) for fc in fluxo_caixa]
    })
    fluxo_table.dataframe(df_fluxo)

    # Atualizar métricas do projeto
    vpl_metric.metric("VPL do Projeto", format_currency(vpl))
    tir_metric.metric("TIR do Projeto", f"{tir*100:.2f}%")

    # Atualizar gráfico de saldo devedor
    saldos_sem_dropdown = [calcular_saldo_devedor(valor_credito, parcela, taxa_admin_anual, indice_correcao_anual, m) for m in range(prazo_meses + 1)]
    fig_saldo.data[0].x = list(range(prazo_meses + 1))
    fig_saldo.data[0].y = saldos_sem_dropdown

    # Cálculo e visualização dos dropdowns
    saldos_com_dropdown = saldos_sem_dropdown.copy()
    for dropdown in st.session_state.get('dropdowns', []):
        mes, valor, agio = dropdown['mes'], dropdown['valor'], dropdown['agio']
        if mes < len(saldos_com_dropdown):
            saldos_com_dropdown[mes:] = [
                aplicar_dropdown(saldo, valor, agio) if i == mes else 
                calcular_saldo_devedor(saldos_com_dropdown[mes], parcela, taxa_admin_anual, indice_correcao_anual, i-mes)
                for i, saldo in enumerate(saldos_com_dropdown[mes:], start=mes)
            ]
    
    fig_saldo.data[1].x = list(range(prazo_meses + 1))
    fig_saldo.data[1].y = saldos_com_dropdown
    saldo_chart.plotly_chart(fig_saldo, use_container_width=True)

    # Atualizar métricas do consórcio
    parcela_metric.metric("Parcela Mensal", format_currency(parcela))
    relacao_metric.metric("Relação Parcela/Crédito Novo", f"{relacao_parcela_credito:.2f}%")

    # Atualizar gráfico combinado
    fig_combinado.data[0].x = list(range(1, len(fluxo_caixa) + 1))
    fig_combinado.data[0].y = fluxo_caixa
    fig_combinado.data[1].x = list(range(1, len(fluxo_caixa_com_consorcio) + 1))
    fig_combinado.data[1].y = fluxo_caixa_com_consorcio
    combinado_chart.plotly_chart(fig_combinado, use_container_width=True)

    # Atualizar métricas comparativas
    vpl_consorcio_metric.metric("VPL do Projeto com Consórcio", format_currency(vpl_com_consorcio))
    melhoria_vpl_metric.metric("Melhoria no VPL", format_currency(vpl_com_consorcio - vpl))

# Interface do usuário
# Sidebar para inputs principais
with st.sidebar:
    valor_credito_str = st.text_input("Valor do Crédito", value="10000000", key="valor_credito_str")
    valor_credito = parse_currency(valor_credito_str)
    st.session_state.valor_credito = float(valor_credito)

    prazo_meses = st.number_input("Prazo do Consórcio (meses)", min_value=12, max_value=240, value=60, step=12, key="prazo_meses")
    
    taxa_admin_anual = st.number_input("Taxa de Administração Anual (%)", min_value=0.0, value=1.20, step=0.01, key="taxa_admin_anual")
    
    indice_correcao_anual = st.number_input("Índice de Correção Anual (%)", min_value=0.0, value=5.0, step=0.1, key="indice_correcao_anual")
    
    valor_lance_str = st.text_input("Valor do Lance", value="2000000", key="valor_lance_str")
    valor_lance = parse_currency(valor_lance_str)
    st.session_state.valor_lance = float(valor_lance)

    vgv_str = st.text_input("VGV", value="10000000", key="vgv_str")
    vgv = parse_currency(vgv_str)
    st.session_state.vgv = float(vgv)

    orcamento_str = st.text_input("Orçamento", value="8000000", key="orcamento_str")
    orcamento = parse_currency(orcamento_str)
    st.session_state.orcamento = float(orcamento)

    taxa_desconto_vpl = st.number_input("Taxa de Desconto para VPL (%)", min_value=0.0, value=10.0, step=0.1, key="taxa_desconto_vpl")

# Título principal
st.title("Constructa MVP - Simulador de Consórcio e Fluxo de Caixa")

# Inputs da tela operacional
col1, col2, col3 = st.columns(3)
with col1:
    prazo_empreendimento = st.number_input("Prazo do Empreendimento (meses)", min_value=1, value=24, step=1, key="prazo_empreendimento")
with col2:
    perfil_vendas = st.selectbox("Perfil de Vendas", ['Linear', 'Front-loaded', 'Back-loaded'], key="perfil_vendas")
with col3:
    perfil_despesas = st.selectbox("Perfil de Despesas", ['Linear', 'Front-loaded', 'Back-loaded'], key="perfil_despesas")

# 1. Fluxo de Caixa do Empreendimento
st.header("Fluxo de Caixa do Empreendimento")

# Gráfico de Fluxo de Caixa (placeholder)
fig_fluxo = go.Figure()
fig_fluxo.add_trace(go.Bar(x=[0], y=[0], name='Fluxo de Caixa'))
fig_fluxo.update_layout(title="Fluxo de Caixa do Empreendimento", xaxis_title="Meses", yaxis_title="Valor (R$)")
fluxo_chart = st.plotly_chart(fig_fluxo, use_container_width=True)

# Tabela de Fluxo de Caixa (placeholder)
fluxo_table = st.empty()

# Métricas do projeto (placeholders)
col1, col2 = st.columns(2)
vpl_metric = col1.empty()
tir_metric = col2.empty()

# 2. Seção do Consórcio
st.header("Simulação do Consórcio")

# Gráfico de Saldo Devedor (placeholder)
fig_saldo = go.Figure()
fig_saldo.add_trace(go.Scatter(x=[0], y=[0], name='Sem Dropdown'))
fig_saldo.add_trace(go.Scatter(x=[0], y=[0], name='Com Dropdown'))
fig_saldo.update_layout(title="Evolução do Saldo Devedor", xaxis_title="Meses", yaxis_title="Saldo (R$)")
saldo_chart = st.plotly_chart(fig_saldo, use_container_width=True)

# Métricas do consórcio (placeholders)
col1, col2 = st.columns(2)
parcela_metric = col1.empty()
relacao_metric = col2.empty()

# Seção de Dropdowns
st.subheader("Simulação de Dropdown")
col1, col2, col3 = st.columns(3)
with col1:
    valor_dropdown_str = st.text_input("Valor do Dropdown", value="500000", key="valor_dropdown_str")
    valor_dropdown = parse_currency(valor_dropdown_str)
with col2:
    agio = st.number_input("Ágio (%)", min_value=0.0, value=5.0, step=0.1, key="agio")
with col3:
    mes_dropdown = st.number_input("Mês do Dropdown", min_value=1, value=12, step=1, key="mes_dropdown")

if st.button("Adicionar Dropdown"):
    if 'dropdowns' not in st.session_state:
        st.session_state.dropdowns = []
    st.session_state.dropdowns.append({
        "valor": float(valor_dropdown),
        "agio": agio,
        "mes": mes_dropdown
    })
    st.experimental_rerun()

if 'dropdowns' in st.session_state and st.session_state.dropdowns:
    st.write("Dropdowns Adicionados:")
    for i, dropdown in enumerate(st.session_state.dropdowns):
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
        with col1:
            st.write(f"Dropdown {i+1}: {format_currency(dropdown['valor'])}")
        with col2:
            st.write(f"Ágio: {dropdown['agio']}%")
        with col3:
            st.write(f"Mês: {dropdown['mes']}")
        with col4:
            if st.button(f"Remover {i+1}"):
                st.session_state.dropdowns.pop(i)
                st.experimental_rerun()

# 3. Interação Crédito-Fluxo de Caixa
st.header("Impacto do Consórcio no Fluxo de Caixa")

# Gráfico combinado (placeholder)
fig_combinado = go.Figure()
fig_combinado.add_trace(go.Scatter(x=[0], y=[0], name='Fluxo de Caixa Original'))
fig_combinado.add_trace(go.Scatter(x=[0], y=[0], name='Fluxo de Caixa com Consórcio'))
fig_combinado.update_layout(title="Interação Crédito-Fluxo de Caixa", xaxis_title="Meses", yaxis_title="Valor (R$)")
combinado_chart = st.plotly_chart(fig_combinado, use_container_width=True)

# Métricas comparativas (placeholders)
col1, col2 = st.columns(2)
vpl_consorcio_metric = col1.empty()
melhoria_vpl_metric = col2.empty()

# Atualizar todos os gráficos e métricas quando qualquer input mudar
if all(key in st.session_state for key in ['valor_credito', 'prazo_meses', 'taxa_admin_anual', 'indice_correcao_anual', 'valor_lance', 'vgv', 'orcamento', 'prazo_empreendimento', 'perfil_vendas', 'perfil_despesas', 'taxa_desconto_vpl']):
    update_all()

st.sidebar.info("Constructa MVP - Versão 1.3.0")
