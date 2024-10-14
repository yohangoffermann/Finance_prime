import streamlit as st
import plotly.graph_objects as go
from decimal import Decimal, ROUND_HALF_UP, ROUND_UP

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

# Inicialização da sessão
if 'dropdowns' not in st.session_state:
    st.session_state.dropdowns = []

# Funções de cálculo
def calcular_lance_embutido(dnd, plt):
    lp = dnd * (plt / (Decimal('2') - plt))
    ct = (dnd + lp) / (Decimal('1') - (plt / Decimal('2')))
    le = lp  # Lance embutido igual ao lance pago
    cl = ct - le
    return ct, lp, le, cl

def calcular_parcela(valor_credito, prazo_meses):
    parcela = valor_credito / Decimal(str(prazo_meses))
    return parcela.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def aplicar_dropdown(saldo_devedor, valor_dropdown):
    return max(saldo_devedor - valor_dropdown, Decimal('0'))

# Função para atualizar o gráfico e métricas
def update_simulation():
    dnd = parse_currency(st.session_state.dinheiro_novo_desejado)
    plt = Decimal(str(st.session_state.percentual_lance_total)) / Decimal('100')
    prazo_meses = st.session_state.prazo_meses
    
    ct, lp, le, cl = calcular_lance_embutido(dnd, plt)
    st.session_state.ct, st.session_state.lp, st.session_state.le, st.session_state.cl = ct, lp, le, cl
    
    parcela_inicial = calcular_parcela(cl, prazo_meses)
    
    saldos_padrao = [cl - (parcela_inicial * m) for m in range(prazo_meses + 1)]
    
    saldos_com_dropdowns = saldos_padrao.copy()
    parcelas_restantes = prazo_meses
    
    for dropdown in st.session_state.dropdowns:
        mes = dropdown['mes']
        valor = parse_currency(dropdown['valor'])
        
        # Calcula o saldo antes do dropdown
        saldo_antes_dropdown = saldos_com_dropdowns[mes]
        
        # Aplica o dropdown
        saldo_apos_dropdown = aplicar_dropdown(saldo_antes_dropdown, valor)
        
        # Recalcula o número de parcelas restantes
        parcelas_restantes = max(1, (saldo_apos_dropdown / parcela_inicial).quantize(Decimal('1'), rounding=ROUND_UP))
        
        # Atualiza os saldos futuros
        for m in range(mes, prazo_meses + 1):
            parcelas_passadas = m - mes
            if parcelas_passadas < parcelas_restantes:
                saldos_com_dropdowns[m] = saldo_apos_dropdown - (parcela_inicial * parcelas_passadas)
            else:
                saldos_com_dropdowns[m] = Decimal('0')
    
    st.session_state.saldos_com_dropdowns = saldos_com_dropdowns
    st.session_state.parcela_padrao = parcela_inicial
    st.session_state.saldo_com_dropdown_ultimo = saldos_com_dropdowns[-1]
    st.session_state.parcela_com_dropdown = parcela_inicial  # A parcela não muda com dropdowns

    # Cálculo das relações percentuais
    st.session_state.relacao_parcela_cl = (parcela_inicial / cl * 100).quantize(Decimal('0.01'))
    st.session_state.relacao_parcela_dn = (parcela_inicial / dnd * 100).quantize(Decimal('0.01'))

    # Cálculo da eficiência do modelo
    st.session_state.eficiencia_modelo = dnd / lp

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
st.title("Constructa - Simulador de Consórcio com Padrão Lance Embutido")

# Sidebar para inputs principais
with st.sidebar:
    st.header("Parâmetros do Consórcio")
    
    if 'dinheiro_novo_desejado' not in st.session_state:
        st.session_state.dinheiro_novo_desejado = "R$ 1.300.000,00"
    dinheiro_novo_desejado = st.text_input("Dinheiro Novo Desejado", value=st.session_state.dinheiro_novo_desejado, key="input_dinheiro_novo_desejado")
    if dinheiro_novo_desejado != st.session_state.dinheiro_novo_desejado:
        st.session_state.dinheiro_novo_desejado = format_input_currency(dinheiro_novo_desejado)

    if 'percentual_lance_total' not in st.session_state:
        st.session_state.percentual_lance_total = 55.0
    percentual_lance_total = st.slider("Percentual de Lance Total (%)", min_value=50.0, max_value=60.0, value=st.session_state.percentual_lance_total, step=0.1, key="slider_percentual_lance_total")
    if percentual_lance_total != st.session_state.percentual_lance_total:
        st.session_state.percentual_lance_total = percentual_lance_total

    if 'prazo_meses' not in st.session_state:
        st.session_state.prazo_meses = 240
    prazo_meses = st.number_input("Prazo (meses)", min_value=180, max_value=240, value=st.session_state.prazo_meses, step=1, key="input_prazo_meses")
    if prazo_meses != st.session_state.prazo_meses:
        st.session_state.prazo_meses = prazo_meses

    st.session_state.indice_correcao_anual = st.number_input("Índice de Correção Anual (%) - Informativo", min_value=0.0, value=5.0, step=0.1, key="input_indice_correcao_anual")
    st.caption("Nota: Este índice não é usado no cálculo inicial da parcela, mas pode ser usado para simulações futuras de correção pelo INCC.")

# Atualizar simulação em tempo real
if all(key in st.session_state for key in ['dinheiro_novo_desejado', 'percentual_lance_total', 'prazo_meses']):
    update_simulation()

# Exibir resultados do Padrão Lance Embutido
if 'ct' in st.session_state:
    st.subheader("Resultados do Padrão Lance Embutido")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Crédito Total", format_currency(st.session_state.ct))
        st.metric("Lance Pago", format_currency(st.session_state.lp))
    with col2:
        st.metric("Lance Embutido", format_currency(st.session_state.le))
        st.metric("Crédito Liberado", format_currency(st.session_state.cl))

    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Parcela Mensal", format_currency(st.session_state.parcela_padrao))
    with col2:
        st.metric("Relação Parcela/Crédito Liberado", f"{st.session_state.relacao_parcela_cl}%")
        st.caption("Importante para gestão de fluxo de caixa")
    with col3:
        st.metric("Relação Parcela/Dinheiro Novo", f"{st.session_state.relacao_parcela_dn}%")
        st.caption("Indica o custo mensal do dinheiro novo obtido")

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Eficiência do Modelo", f"{st.session_state.eficiencia_modelo:.2f}")
    with col2:
        prazo_efetivo = next((i for i, saldo in enumerate(st.session_state.saldos_com_dropdowns) if saldo <= 0), st.session_state.prazo_meses)
        st.metric("Prazo Efetivo (meses)", prazo_efetivo)

    # Validações
    st.subheader("Validações do Modelo")
    col1, col2, col3 = st.columns(3)
    with col1:
        parcela_padrao = Decimal(str(st.session_state.parcela_padrao))
        cl = Decimal(str(st.session_state.cl))
        parcela_vs_cl = parcela_padrao <= Decimal('0.005') * cl
        st.write(f"Parcela ≤ 0.5% do Crédito Liberado: {'' if parcela_vs_cl else ''}")
    with col2:
        dnd = parse_currency(st.session_state.dinheiro_novo_desejado)
        parcela_vs_dn = parcela_padrao <= Decimal('0.01') * dnd
        st.write(f"Parcela ≤ 1% do Dinheiro Novo: {'' if parcela_vs_dn else ''}")
    with col3:
        lance_pago_embutido_iguais = st.session_state.lp == st.session_state.le
        st.write(f"Lance Pago = Lance Embutido: {'' if lance_pago_embutido_iguais else ''}")

# Exibir gráfico
if 'fig' in st.session_state:
    st.plotly_chart(st.session_state.fig, use_container_width=True)

# Seção de Dropdowns
st.subheader("Simulação de Dropdowns")

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
            st.success(f"Dropdown de {novo_dropdown['valor']} adicionado com sucesso.")
            update_simulation()
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
                update_simulation()
                st.experimental_rerun()

# Exibir métricas finais
if 'saldo_com_dropdown_ultimo' in st.session_state:
    st.subheader("Resultado Final com Dropdowns")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Saldo Devedor Final", format_currency(st.session_state.saldo_com_dropdown_ultimo))
    with col2:
        st.metric("Parcela Final", format_currency(st.session_state.parcela_com_dropdown))
    with col3:
        if st.session_state.saldo_com_dropdown_ultimo > 0:
            relacao_final = (st.session_state.parcela_com_dropdown / st.session_state.saldo_com_dropdown_ultimo * 100).quantize(Decimal('0.01'))
            st.metric("Relação Parcela/Saldo Final", f"{relacao_final}%")
        else:
            st.metric("Relação Parcela/Saldo Final", "N/A (Saldo Zero)")

# Informações adicionais
st.subheader("Detalhes da Simulação")
st.write(f"Dinheiro Novo Desejado: {st.session_state.dinheiro_novo_desejado}")
st.write(f"Crédito Total: {format_currency(st.session_state.ct)}")
st.write(f"Lance Pago: {format_currency(st.session_state.lp)}")
st.write(f"Lance Embutido: {format_currency(st.session_state.le)}")
st.write(f"Crédito Liberado: {format_currency(st.session_state.cl)}")

# Cálculo do custo total dos dropdowns
custo_total_dropdowns = sum(parse_currency(d['valor']) * (1 + d['agio']/100) for d in st.session_state.dropdowns)
st.write(f"Custo Total dos Dropdowns (incluindo ágio): {format_currency(custo_total_dropdowns)}")

st.sidebar.info("Constructa - Módulo de Consórcio v2.4")
