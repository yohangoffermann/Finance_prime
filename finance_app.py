import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from decimal import Decimal, ROUND_HALF_UP

# Configuração da página
st.set_page_config(page_title="Constructa MVP", layout="wide")

def format_currency(value):
    """Formata o valor para o padrão monetário brasileiro."""
    if isinstance(value, str):
        value = parse_currency(value)
    valor_str = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    partes = valor_str.split(",")
    partes[0] = ".".join([partes[0][i:i+3] for i in range(0, len(partes[0]), 3)][::-1])
    return f"R$ {','.join(partes)}"

def parse_currency(value):
    """Converte uma string no formato monetário brasileiro para Decimal."""
    if isinstance(value, (int, float, Decimal)):
        return Decimal(str(value))
    return Decimal(value.replace('R$', '').replace('.', '').replace(',', '.').strip())

def calcular_parcela(valor_credito, prazo_meses, taxa_admin_anual, indice_correcao_anual):
    valor_credito = Decimal(str(valor_credito))
    prazo_meses = Decimal(str(prazo_meses))
    taxa_admin_mensal = Decimal(str(taxa_admin_anual)) / Decimal('12') / Decimal('100')
    indice_correcao_mensal = (Decimal('1') + Decimal(str(indice_correcao_anual))/Decimal('100'))**(Decimal('1')/Decimal('12')) - Decimal('1')
    fator = (Decimal('1') + indice_correcao_mensal) / (Decimal('1') - (Decimal('1') + indice_correcao_mensal)**(-prazo_meses))
    parcela = valor_credito * (fator + taxa_admin_mensal)
    return parcela.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def calcular_saldo_devedor(valor_credito, parcela, taxa_admin_anual, indice_correcao_anual, meses_pagos):
    valor_credito = Decimal(str(valor_credito))
    parcela = Decimal(str(parcela))
    taxa_admin_mensal = Decimal(str(taxa_admin_anual)) / Decimal('12') / Decimal('100')
    indice_correcao_mensal = (Decimal('1') + Decimal(str(indice_correcao_anual))/Decimal('100'))**(Decimal('1')/Decimal('12')) - Decimal('1')
    saldo = valor_credito * (Decimal('1') + indice_correcao_mensal)**Decimal(str(meses_pagos))
    for _ in range(meses_pagos):
        saldo -= parcela - (saldo * taxa_admin_mensal)
    return max(saldo, Decimal('0')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def calcular_fluxo_caixa(vgv, orcamento, prazo, perfil_vendas, perfil_despesas):
    receitas = gerar_perfil(vgv, prazo, perfil_vendas)
    despesas = gerar_perfil(orcamento, prazo, perfil_despesas)
    fluxo_caixa = [receitas[i] - despesas[i] for i in range(prazo)]
    return fluxo_caixa

def gerar_perfil(valor_total, prazo, perfil):
    valor_total = Decimal(str(valor_total))
    prazo = Decimal(str(prazo))
    if perfil == 'Linear':
        return [valor_total / prazo] * int(prazo)
    elif perfil == 'Front-loaded':
        meio = int(prazo) // 2
        return [valor_total * Decimal('0.6') / Decimal(str(meio))] * meio + \
               [valor_total * Decimal('0.4') / (prazo - Decimal(str(meio)))] * (int(prazo) - meio)
    elif perfil == 'Back-loaded':
        meio = int(prazo) // 2
        return [valor_total * Decimal('0.4') / Decimal(str(meio))] * meio + \
               [valor_total * Decimal('0.6') / (prazo - Decimal(str(meio)))] * (int(prazo) - meio)

def aplicar_dropdown(saldo_devedor, valor_dropdown, agio):
    saldo_devedor = Decimal(str(saldo_devedor))
    valor_dropdown = Decimal(str(valor_dropdown))
    agio = Decimal(str(agio))
    valor_efetivo = valor_dropdown * (Decimal('1') + agio/Decimal('100'))
    novo_saldo = max(saldo_devedor - valor_efetivo, Decimal('0'))
    return novo_saldo.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

# Sidebar para inputs principais
st.sidebar.title("Parâmetros do Projeto")

# Módulo 1: Crédito Otimizado
valor_credito = st.sidebar.text_input("Valor do Crédito", value="R$ 1.000.000,00")
prazo_meses = st.sidebar.number_input("Prazo (meses)", min_value=1, value=60, step=1)
taxa_admin_anual = st.sidebar.number_input("Taxa de Administração Anual (%)", min_value=0.0, value=10.0, step=0.1)
indice_correcao_anual = st.sidebar.number_input("Índice de Correção Anual (%)", min_value=0.0, value=5.0, step=0.1)
valor_lance = st.sidebar.text_input("Valor do Lance", value="R$ 100.000,00")

# Módulo 2: Dados do Empreendimento
vgv = st.sidebar.text_input("VGV", value="R$ 10.000.000,00")
orcamento = st.sidebar.text_input("Orçamento", value="R$ 8.000.000,00")
prazo_empreendimento = st.sidebar.number_input("Prazo do Empreendimento (meses)", min_value=1, value=24, step=1)

# Corpo principal
st.title("Constructa MVP")

# Perfis de Despesas e Vendas
col1, col2 = st.columns(2)
with col1:
    perfil_vendas = st.selectbox("Perfil de Vendas", ['Linear', 'Front-loaded', 'Back-loaded'])
with col2:
    perfil_despesas = st.selectbox("Perfil de Despesas", ['Linear', 'Front-loaded', 'Back-loaded'])

# Cálculos e Exibição de Resultados
if st.button("Calcular"):
    valor_credito = parse_currency(valor_credito)
    valor_lance = parse_currency(valor_lance)
    vgv = parse_currency(vgv)
    orcamento = parse_currency(orcamento)

    parcela = calcular_parcela(valor_credito, prazo_meses, taxa_admin_anual, indice_correcao_anual)
    credito_novo = valor_credito - valor_lance
    relacao_parcela_credito = (parcela / credito_novo) * Decimal('100')
    
    fluxo_caixa = calcular_fluxo_caixa(vgv, orcamento, prazo_empreendimento, perfil_vendas, perfil_despesas)
    
    # Exibição de resultados principais
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Parcela Mensal", format_currency(parcela))
    with col2:
        st.metric("Relação Parcela/Crédito Novo", f"{relacao_parcela_credito:.2f}%")
    with col3:
        st.metric("VPL do Fluxo de Caixa", format_currency(sum(fluxo_caixa)))
    
    # Gráficos
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12))
    
    # Gráfico de amortização
    meses = list(range(1, prazo_meses + 1))
    saldos = [calcular_saldo_devedor(valor_credito, parcela, taxa_admin_anual, indice_correcao_anual, m) for m in meses]
    ax1.plot(meses, saldos)
    ax1.set_title("Amortização do Saldo Devedor")
    ax1.set_xlabel("Meses")
    ax1.set_ylabel("Saldo Devedor (R$)")
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format_currency(x)))
    
    # Gráfico de fluxo de caixa
    ax2.bar(range(1, prazo_empreendimento + 1), fluxo_caixa)
    ax2.set_title("Fluxo de Caixa do Empreendimento")
    ax2.set_xlabel("Meses")
    ax2.set_ylabel("Valor (R$)")
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format_currency(x)))
    
    st.pyplot(fig)
    
    # Tabela de fluxo de caixa
    df_fluxo = pd.DataFrame({
        'Mês': range(1, prazo_empreendimento + 1),
        'Fluxo de Caixa': [format_currency(fc) for fc in fluxo_caixa]
    })
    st.write(df_fluxo)

# Módulo 3: Dropdown
st.subheader("Simulação de Dropdown")

# Lista para armazenar os dropdowns
if 'dropdowns' not in st.session_state:
    st.session_state.dropdowns = []

col1, col2, col3 = st.columns(3)
with col1:
    valor_dropdown = st.text_input("Valor do Dropdown", value="R$ 500.000,00")
with col2:
    agio = st.number_input("Ágio (%)", min_value=0.0, value=5.0, step=0.1)
with col3:
    mes_dropdown = st.number_input("Mês do Dropdown", min_value=1, value=12, step=1)

if st.button("Adicionar Dropdown"):
    st.session_state.dropdowns.append({
        "valor": parse_currency(valor_dropdown),
        "agio": agio,
        "mes": mes_dropdown
    })

# Exibir lista de dropdowns
if st.session_state.dropdowns:
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

# Recálculo com dropdowns
if st.button("Recalcular com Dropdowns"):
    saldo_atual = valor_credito
    nova_parcela = parcela
    for dropdown in sorted(st.session_state.dropdowns, key=lambda x: x['mes']):
        saldo_atual = calcular_saldo_devedor(saldo_atual, nova_parcela, taxa_admin_anual, indice_correcao_anual, dropdown['mes'])
        saldo_atual = aplicar_dropdown(saldo_atual, dropdown['valor'], dropdown['agio'])
        prazo_restante = prazo_meses - dropdown['mes']
        nova_parcela = calcular_parcela(saldo_atual, prazo_restante, taxa_admin_anual, indice_correcao_anual)
    
    st.metric("Nova Parcela após Dropdowns", format_currency(nova_parcela))
    st.metric("Saldo Final", format_currency(saldo_atual))

st.sidebar.info("Constructa MVP - Versão 1.0.4")
