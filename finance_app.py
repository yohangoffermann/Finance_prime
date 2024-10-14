import streamlit as st
import plotly.graph_objects as go
from decimal import Decimal, ROUND_HALF_UP

def format_currency(value):
    return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

def parse_currency(value):
    try:
        return Decimal(value.replace('R$', '').replace('.', '').replace(',', '.').strip())
    except:
        return Decimal('0')

def calcular_relacao_parcela_credito(parcela, credito):
    return (parcela / credito * 100).quantize(Decimal('0.0001'))

def aplicar_dropdown(saldo, valor_dropdown, agio):
    valor_efetivo = valor_dropdown * (1 + Decimal(str(agio)) / Decimal('100'))
    return max(saldo - valor_efetivo, Decimal('0'))

st.title("Simulador de Consórcio Constructa com Dropdowns")

col1, col2 = st.columns(2)
with col1:
    valor_credito = parse_currency(st.text_input("Valor do Crédito", value="R$ 2.536.401,20"))
    valor_lance_pago = parse_currency(st.text_input("Valor do Lance Pago", value="R$ 655.236,98"))
    valor_lance_embutido = parse_currency(st.text_input("Valor do Lance Embutido", value="R$ 655.236,98"))
with col2:
    valor_parcela_apos_lance = parse_currency(st.text_input("Valor da Parcela Após Lance", value="R$ 8.819,52"))
    prazo_apos_lance = int(parse_currency(st.text_input("Prazo Após Lance (meses)", value="208")))

# Cálculos iniciais
valor_lance_total = valor_lance_pago + valor_lance_embutido
credito_novo = valor_credito - valor_lance_total
relacao_apos_lance = calcular_relacao_parcela_credito(valor_parcela_apos_lance, credito_novo)

# Exibição das informações iniciais
st.write(f"Crédito Novo: {format_currency(credito_novo)}")
st.write(f"Relação Parcela/Dinheiro Novo Após Lance: {relacao_apos_lance}%")

# Seção de Dropdowns
st.subheader("Simulação de Dropdowns")
if 'dropdowns' not in st.session_state:
    st.session_state.dropdowns = []

col1, col2, col3, col4 = st.columns(4)
with col1:
    valor_dropdown = parse_currency(st.text_input("Valor do Dropdown", value="R$ 100.000,00"))
with col2:
    agio = st.number_input("Ágio (%)", min_value=0.0, value=5.0, step=0.1)
with col3:
    mes_dropdown = st.number_input("Mês do Dropdown", min_value=1, max_value=prazo_apos_lance, value=12)
with col4:
    if st.button("Adicionar Dropdown"):
        st.session_state.dropdowns.append({"valor": valor_dropdown, "agio": agio, "mes": mes_dropdown})

# Exibir dropdowns adicionados
if st.session_state.dropdowns:
    st.write("Dropdowns Adicionados:")
    for i, dropdown in enumerate(st.session_state.dropdowns):
        st.write(f"Dropdown {i+1}: {format_currency(dropdown['valor'])} no mês {dropdown['mes']} com ágio de {dropdown['agio']}%")
        if st.button(f"Remover Dropdown {i+1}"):
            st.session_state.dropdowns.pop(i)
            st.experimental_rerun()

if st.button("Simular"):
    # Simulação com lance e dropdowns
    saldos_com_lance = [credito_novo - (valor_parcela_apos_lance * i) for i in range(prazo_apos_lance + 1)]
    
    # Aplicar dropdowns
    for dropdown in sorted(st.session_state.dropdowns, key=lambda x: x['mes']):
        mes, valor, agio = dropdown['mes'], dropdown['valor'], dropdown['agio']
        if mes < len(saldos_com_lance):
            saldo_antes_dropdown = saldos_com_lance[mes]
            saldo_apos_dropdown = aplicar_dropdown(saldo_antes_dropdown, valor, agio)
            reducao = saldo_antes_dropdown - saldo_apos_dropdown
            for i in range(mes, len(saldos_com_lance)):
                saldos_com_lance[i] -= reducao

    # Visualização
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=list(range(prazo_apos_lance + 1)), y=[valor_credito] + saldos_com_lance, name='Saldo Devedor'))
    
    # Adicionar marcadores para os dropdowns
    for dropdown in st.session_state.dropdowns:
        mes, valor = dropdown['mes'], dropdown['valor']
        if mes < len(saldos_com_lance):
            fig.add_trace(go.Scatter(
                x=[mes], 
                y=[saldos_com_lance[mes]], 
                mode='markers',
                marker=dict(size=10, color='red'),
                name=f'Dropdown de {format_currency(valor)}'
            ))

    fig.update_layout(title="Evolução do Saldo Devedor com Dropdowns", xaxis_title="Meses", yaxis_title="Saldo (R$)")
    st.plotly_chart(fig)
    
    # Métricas
    novo_prazo = next((i for i, saldo in enumerate(saldos_com_lance) if saldo <= 0), prazo_apos_lance)
    total_pago = valor_lance_pago + (valor_parcela_apos_lance * novo_prazo) + sum(d['valor'] for d in st.session_state.dropdowns)
    economia_total = valor_credito - total_pago
    st.metric("Economia Total Estimada", format_currency(economia_total))
    st.metric("Redução no Prazo", f"{prazo_apos_lance - novo_prazo} meses")

st.sidebar.info("Constructa - Módulo de Consórcio v1.6")
