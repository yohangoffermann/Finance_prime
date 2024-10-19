import streamlit as st
import plotly.graph_objects as go
import numpy as np

# Configuração da página
st.set_page_config(page_title="Simulador Constructa", layout="wide")

def calculate_payments(principal, months, admin_fee, dropdowns, agio):
    balance = principal
    amortization = principal / months
    payments = []
    balances = [principal]
    
    for month in range(1, months + 1):
        if month % 12 == 0 and month > 1:
            balance *= 1.05
            amortization = balance / (months - month + 1)
        
        admin_fee_value = balance * admin_fee
        monthly_payment = amortization + admin_fee_value
        
        if month in dropdowns:
            dropdown_value = dropdowns[month]
            dropdown_impact = dropdown_value * (1 + agio/100)
            balance -= dropdown_impact
            amortization = balance / (months - month + 1)
        
        payments.append(monthly_payment)
        balance -= amortization
        balances.append(balance)
        
        if balance <= 0 or monthly_payment < 500:
            break
    
    return payments, balances

def main():
    st.title("Simulador Constructa")

    # Sidebar
    with st.sidebar:
        principal = st.number_input("Valor do Crédito (R$)", min_value=10000, value=1800000, step=10000)
        months = st.number_input("Prazo (meses)", min_value=12, value=210, step=12)
        admin_fee = st.number_input("Taxa de Administração Mensal (%)", min_value=0.1, value=0.12, step=0.01) / 100
        agio = st.number_input("Ágio dos Dropdowns (%)", min_value=0.0, value=25.0, step=1.0)
        tlr = st.number_input("Taxa Livre de Risco (% a.a.)", min_value=0.0, value=10.75, step=0.1) / 100

    # Inicialização dos dropdowns
    if 'dropdowns' not in st.session_state:
        st.session_state.dropdowns = {}

    # Cálculos
    payments_with_drops, balances_with_drops = calculate_payments(principal, months, admin_fee, st.session_state.dropdowns, agio)
    payments_no_drops, balances_no_drops = calculate_payments(principal, months, admin_fee, {}, agio)

    # Resumo Financeiro e KPIs
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Resumo Financeiro")
        st.write("Com Dropdowns:")
        st.write(f"Saldo: R$ {balances_with_drops[-1]:,.2f}")
        st.write(f"Parcela: R$ {payments_with_drops[-1]:,.2f}")
        st.write(f"Quitação: {len(payments_with_drops)} meses")
        
        st.write("Sem Dropdowns:")
        st.write(f"Saldo: R$ {balances_no_drops[-1]:,.2f}")
        st.write(f"Parcela: R$ {payments_no_drops[-1]:,.2f}")
        st.write(f"Quitação: {len(payments_no_drops)} meses")
        
        economia = sum(payments_no_drops) - sum(payments_with_drops)
        st.write(f"Economia Total: R$ {economia:,.2f} ({economia/sum(payments_no_drops)*100:.2f}% de redução)")

    with col2:
        st.subheader("KPIs")
        p_cl = payments_with_drops[0] / principal * 100
        p_dn = payments_with_drops[0] / (principal - sum(st.session_state.dropdowns.values())) * 100
        cet = (sum(payments_with_drops) / principal - 1) * 100
        st.write(f"P/CL: {p_cl:.2f}%")
        st.write(f"P/DN: {p_dn:.2f}%")
        st.write(f"CET: {cet:.2f}%")

    # Adicionar Dropdown
    st.subheader("Adicionar Dropdown")
    col1, col2, col3 = st.columns(3)
    with col1:
        dropdown_month = st.number_input("Mês do Dropdown", min_value=1, max_value=months, value=12)
    with col2:
        dropdown_amount = st.number_input("Valor do Dropdown (R$)", min_value=0, max_value=int(balances_with_drops[dropdown_month]), value=10000, step=1000)
    with col3:
        if st.button("Adicionar Dropdown"):
            st.session_state.dropdowns[dropdown_month] = dropdown_amount
            st.experimental_rerun()

    # Exibir Dropdowns adicionados
    if st.session_state.dropdowns:
        st.subheader("Dropdowns Adicionados")
        for month, amount in sorted(st.session_state.dropdowns.items()):
            col1, col2 = st.columns([3, 1])
            col1.write(f"Mês {month}: R$ {amount:,.2f}")
            if col2.button("Remover", key=f"remove_{month}"):
                del st.session_state.dropdowns[month]
                st.experimental_rerun()

    # Gráficos
    st.subheader("Evolução do Saldo Devedor")
    fig_saldo = go.Figure()
    fig_saldo.add_trace(go.Scatter(x=list(range(len(balances_no_drops))), y=balances_no_drops, mode='lines', name='Sem Dropdowns'))
    fig_saldo.add_trace(go.Scatter(x=list(range(len(balances_with_drops))), y=balances_with_drops, mode='lines', name='Com Dropdowns'))
    st.plotly_chart(fig_saldo, use_container_width=True)

    st.subheader("Evolução das Parcelas")
    fig_parcelas = go.Figure()
    fig_parcelas.add_trace(go.Scatter(x=list(range(len(payments_no_drops))), y=payments_no_drops, mode='lines', name='Sem Dropdowns'))
    fig_parcelas.add_trace(go.Scatter(x=list(range(len(payments_with_drops))), y=payments_with_drops, mode='lines', name='Com Dropdowns'))
    st.plotly_chart(fig_parcelas, use_container_width=True)

    # Análise de Arbitragem
    st.subheader("Análise de Arbitragem")
    valor_captado = principal
    valor_quitacao = sum(payments_with_drops) + sum(st.session_state.dropdowns.values())
    ganho_arbitragem = valor_captado - valor_quitacao
    roi = (ganho_arbitragem / sum(st.session_state.dropdowns.values()) - 1) * 100 if st.session_state.dropdowns else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Valor Captado", f"R$ {valor_captado:,.2f}")
    col2.metric("Valor Quitação", f"R$ {valor_quitacao:,.2f}")
    col3.metric("Ganho na Arbitragem", f"R$ {ganho_arbitragem:,.2f}")
    col4.metric("ROI da Estratégia", f"{roi:.2f}%")

if __name__ == "__main__":
    main()
