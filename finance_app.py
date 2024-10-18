import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta

# Configuração da página
st.set_page_config(page_title="Simulador Constructa", layout="wide")

# Função para calcular o saldo devedor e parcelas
def calculate_balance(principal, months, admin_fee, dropdowns, agio):
    # [O conteúdo desta função permanece o mesmo]

def main():
    st.title("Simulador Constructa")

    # Sidebar para inputs principais
    with st.sidebar:
        st.header("Configurações Principais")
        principal = st.number_input("Valor do Crédito (R$)", min_value=10000, value=100000, step=10000)
        months = st.number_input("Prazo (meses)", min_value=12, value=200, step=12)
        admin_fee = st.number_input("Taxa de Administração Mensal (%)", min_value=0.1, value=0.5, step=0.1) / 100
        agio = st.number_input("Ágio dos Dropdowns (%)", min_value=0.0, value=20.0, step=1.0)

    # Gerenciamento de Dropdowns
    if 'dropdowns' not in st.session_state:
        st.session_state.dropdowns = {}

    st.subheader("Adicionar Dropdown")
    col1, col2, col3 = st.columns(3)
    with col1:
        dropdown_month = st.number_input("Mês do Dropdown", min_value=1, max_value=months, value=12)
    with col2:
        dropdown_amount = st.number_input("Valor do Dropdown (R$)", min_value=1000, value=10000, step=1000)
    with col3:
        if st.button("Adicionar Dropdown"):
            st.session_state.dropdowns[dropdown_month] = dropdown_amount

    # Exibir Dropdowns adicionados
    if st.session_state.dropdowns:
        st.subheader("Dropdowns Adicionados")
        for month, amount in st.session_state.dropdowns.items():
            col1, col2 = st.columns([3, 1])
            col1.write(f"Mês {month}: R$ {amount:,.2f}")
            if col2.button("Remover", key=f"remove_{month}"):
                del st.session_state.dropdowns[month]
                st.experimental_rerun()

    # Cálculos
    balances, balances_no_drops, monthly_payments, monthly_payments_no_drops = calculate_balance(
        principal, months, admin_fee, st.session_state.dropdowns, agio
    )

    # Gráfico de Saldo Devedor
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=list(range(months + 1)), y=balances_no_drops, mode='lines', name='Sem Dropdowns', line=dict(color='#e74c3c', dash='dash')))
    fig.add_trace(go.Scatter(x=list(range(months + 1)), y=balances, mode='lines', name='Com Dropdowns', line=dict(color='#1e3799')))
    fig.update_layout(title='Evolução do Saldo Devedor', xaxis_title='Meses', yaxis_title='Saldo (R$)')
    st.plotly_chart(fig, use_container_width=True)

    # Resumo Financeiro
    st.subheader("Resumo Financeiro")
    col1, col2 = st.columns(2)
    with col1:
        st.write("Saldo Devedor Final")
        st.write(f"Com Dropdowns: R$ {balances[-1]:,.2f}")
        st.write(f"Sem Dropdowns: R$ {balances_no_drops[-1]:,.2f}")
        st.write(f"Economia: R$ {balances_no_drops[-1] - balances[-1]:,.2f}")
    with col2:
        st.write("Parcela Mensal")
        st.write(f"Inicial: R$ {monthly_payments[0]:,.2f}")
        st.write(f"Final (com Dropdowns): R$ {monthly_payments[-1]:,.2f}")
        st.write(f"Economia: R$ {monthly_payments[0] - monthly_payments[-1]:,.2f}")

if __name__ == "__main__":
    main()
