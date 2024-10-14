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

st.title("Simulador de Consórcio Constructa")

col1, col2 = st.columns(2)
with col1:
    valor_credito = parse_currency(st.text_input("Valor do Crédito", value="R$ 2.536.401,20"))
    valor_parcela_inicial = parse_currency(st.text_input("Valor da Parcela Inicial", value="R$ 9.023,74"))
    prazo_original = int(parse_currency(st.text_input("Prazo Original (meses)", value="240")))
with col2:
    valor_lance_pago = parse_currency(st.text_input("Valor do Lance Pago", value="R$ 655.236,98"))
    valor_lance_embutido = parse_currency(st.text_input("Valor do Lance Embutido", value="R$ 655.236,98"))
    valor_parcela_apos_lance = parse_currency(st.text_input("Valor da Parcela Após Lance", value="R$ 8.819,52"))
    prazo_apos_lance = int(parse_currency(st.text_input("Prazo Após Lance (meses)", value="208")))

# Cálculos
valor_lance_total = valor_lance_pago + valor_lance_embutido
credito_novo = valor_credito - valor_lance_total
relacao_inicial = calcular_relacao_parcela_credito(valor_parcela_inicial, valor_credito)
relacao_apos_lance = calcular_relacao_parcela_credito(valor_parcela_apos_lance, credito_novo)

# Exibição das relações e crédito novo
st.write(f"Crédito Novo: {format_currency(credito_novo)}")
st.write(f"Relação Parcela/Dinheiro Novo Inicial: {relacao_inicial}%")
st.write(f"Relação Parcela/Dinheiro Novo Após Lance: {relacao_apos_lance}%")

if st.button("Simular"):
    # Simulação simplificada
    saldos_sem_lance = [valor_credito - (valor_parcela_inicial * i) for i in range(prazo_original + 1)]
    saldos_com_lance = [valor_credito] + [credito_novo - (valor_parcela_apos_lance * i) for i in range(1, prazo_apos_lance + 1)]
    
    # Visualização
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=list(range(prazo_original + 1)), y=saldos_sem_lance, name='Sem Lance'))
    fig.add_trace(go.Scatter(x=list(range(prazo_apos_lance + 1)), y=saldos_com_lance, name='Com Lance'))
    fig.update_layout(title="Evolução do Saldo Devedor", xaxis_title="Meses", yaxis_title="Saldo (R$)")
    st.plotly_chart(fig)
    
    # Métricas
    economia_total = (valor_parcela_inicial * prazo_original) - (valor_lance_pago + (valor_parcela_apos_lance * prazo_apos_lance))
    st.metric("Economia Total Estimada", format_currency(economia_total))
    st.metric("Redução no Prazo", f"{prazo_original - prazo_apos_lance} meses")

st.sidebar.info("Constructa - Módulo de Consórcio v1.4")
