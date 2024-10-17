import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

def calculate_balance(principal, months, rate, dropdowns):
    balance = principal
    balance_no_drops = principal
    monthly_payment = (principal * (rate/12) * (1 + rate/12)**months) / ((1 + rate/12)**months - 1)
    balances = []
    balances_no_drops = []
    
    for month in range(1, months+1):
        interest = balance * (rate/12)
        balance = balance - monthly_payment + interest
        balance_no_drops = balance_no_drops - monthly_payment + (balance_no_drops * (rate/12))
        
        if month in dropdowns:
            balance -= dropdowns[month]
        
        balances.append(balance)
        balances_no_drops.append(balance_no_drops)
    
    return balances, balances_no_drops, monthly_payment

def main():
    st.title("Simulador Constructa com Dropdowns")

    # Inputs
    principal = st.sidebar.number_input("Valor do Crédito", min_value=10000, value=100000, step=10000)
    months = st.sidebar.number_input("Prazo (meses)", min_value=12, value=200, step=12)
    rate = st.sidebar.number_input("Taxa de Juros Anual (%)", min_value=0.1, value=6.0, step=0.1) / 100

    # Dropdown inputs
    st.sidebar.subheader("Adicionar Dropdowns")
    dropdown_month = st.sidebar.number_input("Mês do Dropdown", min_value=1, max_value=months, value=12)
    dropdown_amount = st.sidebar.number_input("Valor do Dropdown", min_value=1000, value=10000, step=1000)
    if st.sidebar.button("Adicionar Dropdown"):
        if 'dropdowns' not in st.session_state:
            st.session_state.dropdowns = {}
        st.session_state.dropdowns[dropdown_month] = dropdown_amount

    # Display added dropdowns
    if 'dropdowns' in st.session_state:
        st.sidebar.subheader("Dropdowns Adicionados")
        for month, amount in st.session_state.dropdowns.items():
            st.sidebar.write(f"Mês {month}: R$ {amount}")

    # Calculate balances
    dropdowns = st.session_state.dropdowns if 'dropdowns' in st.session_state else {}
    balances, balances_no_drops, monthly_payment = calculate_balance(principal, months, rate, dropdowns)

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
        if len(dropdowns) > 0:
            last_dropdown_month = max(dropdowns.keys())
            adjusted_balance = balances[last_dropdown_month-1]
            adjusted_months = months - last_dropdown_month + 1
            adjusted_payment = (adjusted_balance * (rate/12) * (1 + rate/12)**adjusted_months) / ((1 + rate/12)**adjusted_months - 1)
            st.write(f"Após Último Dropdown: R$ {adjusted_payment:,.2f}")
            st.write(f"Redução: R$ {monthly_payment - adjusted_payment:,.2f}")
        else:
            st.write("Sem alteração (nenhum dropdown aplicado)")

if __name__ == "__main__":
    main()
