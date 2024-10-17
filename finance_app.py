import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

def calculate_balance(principal, months, admin_fee, dropdowns, agio):
    balance = principal
    balance_no_drops = principal
    monthly_payment = (principal / months) + (principal * admin_fee)
    balances = []
    balances_no_drops = []
    
    for month in range(1, months+1):
        balance = balance - monthly_payment
        balance_no_drops = balance_no_drops - monthly_payment
        
        if month in dropdowns:
            dropdown_value = dropdowns[month]
            dropdown_impact = dropdown_value * (1 + agio/100)
            balance = max(0, balance - dropdown_impact)
        
        balances.append(max(0, balance))
        balances_no_drops.append(balance_no_drops)
    
    return balances, balances_no_drops, monthly_payment

def main():
    st.title("Simulador Constructa com Dropdowns")

    # Inputs
    principal = st.sidebar.number_input("Valor do Crédito", min_value=10000, value=100000, step=10000)
    months = st.sidebar.number_input("Prazo (meses)", min_value=12, value=200, step=12)
    admin_fee = st.sidebar.number_input("Taxa de Administração Mensal (%)", min_value=0.1, value=0.5, step=0.1) / 100
    agio = st.sidebar.number_input("Ágio dos Dropdowns (%)", min_value=0.0, value=20.0, step=1.0)

    # Inicializar dropdowns na sessão se não existir
    if 'dropdowns' not in st.session_state:
        st.session_state.dropdowns = {}

    # Dropdown inputs
    st.sidebar.subheader("Adicionar Dropdown")
    dropdown_month = st.sidebar.number_input("Mês do Dropdown", min_value=1, max_value=months, value=12)
    dropdown_amount = st.sidebar.number_input("Valor do Dropdown", min_value=1000, value=10000, step=1000)
    if st.sidebar.button("Adicionar Dropdown"):
        current_balance = principal - (dropdown_month * ((principal / months) + (principal * admin_fee)))
        if dropdown_amount <= current_balance:
            st.session_state.dropdowns[dropdown_month] = dropdown_amount
        else:
            st.sidebar.warning("Valor do dropdown não pode ser maior que o saldo atual.")

    # Display added dropdowns
    if st.session_state.dropdowns:
        st.sidebar.subheader("Dropdowns Adicionados")
        for month, amount in st.session_state.dropdowns.items():
            st.sidebar.write(f"Mês {month}: R$ {amount}")

    # Calculate balances
    balances, balances_no_drops, monthly_payment = calculate_balance(principal, months, admin_fee, st.session_state.dropdowns, agio)

    # Plot
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=list(range(1, months+1)), y=balances, mode='lines', name='Com Dropdowns'))
    fig.add_trace(go.Scatter(x=list(range(1, months+1)), y=balances_no_drops, mode='lines', name='Sem Dropdowns'))
    fig.update_layout(title='Evolução do Saldo Devedor', xaxis_title='Meses', yaxis_title='Saldo (R$)')
    st.plotly_chart(fig)

    # Monitors
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Saldo Devedor Final")
        st.write(f"Com Dropdowns: R$ {balances[-1]:,.2f}")
        st.write(f"Sem Dropdowns: R$ {balances_no_drops[-1]:,.2f}")
        st.write(f"Economia: R$ {balances_no_drops[-1] - balances[-1]:,.2f}")

    with col2:
        st.subheader("Parcela Mensal")
        st.write(f"Inicial: R$ {monthly_payment:,.2f}")
        if st.session_state.dropdowns:
            last_dropdown_month = max(st.session_state.dropdowns.keys())
            adjusted_balance = balances[last_dropdown_month-1]
            adjusted_months = months - last_dropdown_month + 1
            adjusted_payment = (adjusted_balance / adjusted_months) + (adjusted_balance * admin_fee)
            st.write(f"Após Último Dropdown: R$ {adjusted_payment:,.2f}")
            st.write(f"Redução: R$ {monthly_payment - adjusted_payment:,.2f}")
        else:
            st.write("Sem alteração (nenhum dropdown aplicado)")

    # Total impact of dropdowns
    if st.session_state.dropdowns:
        total_dropdown_value = sum(st.session_state.dropdowns.values())
        total_dropdown_impact = total_dropdown_value * (1 + agio/100)
        st.subheader("Impacto Total dos Dropdowns")
        st.write(f"Valor Total dos Dropdowns: R$ {total_dropdown_value:,.2f}")
        st.write(f"Impacto Total (com ágio): R$ {total_dropdown_impact:,.2f}")
        st.write(f"Ganho com Ágio: R$ {total_dropdown_impact - total_dropdown_value:,.2f}")

if __name__ == "__main__":
    main()
