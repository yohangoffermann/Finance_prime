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
    total_dropdown_value = 0
    total_agio = 0
    
    for month in range(1, months + 1):
        if month % 12 == 0 and month > 1:
            balance *= 1.05
            amortization = balance / (months - month + 1)
        
        if month in dropdowns:
            dropdown_value = dropdowns[month]
            agio_value = dropdown_value * (agio/100)
            total_dropdown_value += dropdown_value
            total_agio += agio_value
            balance -= (dropdown_value + agio_value)
            amortization = balance / (months - month + 1)
        
        admin_fee_value = balance * admin_fee
        monthly_payment = amortization + admin_fee_value
        
        payments.append(monthly_payment)
        balance -= amortization
        balances.append(balance)
        
        if balance <= 0 or monthly_payment < 500:
            break
    
    return payments, balances, total_dropdown_value, total_agio

def main():
    st.title("Simulador Constructa")

    # Sidebar
    with st.sidebar:
        principal = st.number_input("Valor do Crédito (R$)", min_value=10000, value=5000000, step=10000)
        months = st.number_input("Prazo (meses)", min_value=12, value=240, step=12)
        admin_fee = st.number_input("Taxa de Administração Mensal (%)", min_value=0.1, value=0.12, step=0.01) / 100
        agio = st.number_input("Ágio dos Dropdowns (%)", min_value=0.0, value=25.0, step=1.0)
        tlr = st.number_input("Taxa Livre de Risco (% a.a.)", min_value=0.0, value=11.00, step=0.1) / 100

    # Inicialização dos dropdowns
    if 'dropdowns' not in st.session_state:
        st.session_state.dropdowns = {}

    # Cálculos
    payments_with_drops, balances_with_drops, total_dropdown_value, total_agio = calculate_payments(principal, months, admin_fee, st.session_state.dropdowns, agio)
    payments_no_drops, balances_no_drops, _, _ = calculate_payments(principal, months, admin_fee, {}, agio)

    # Determinar o mês do último dropdown
    last_dropdown_month = max(st.session_state.dropdowns.keys()) if st.session_state.dropdowns else months

    # Resumo Financeiro e KPIs
    st.subheader("Resumo Financeiro e KPIs")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("Com Dropdowns")
        st.metric("Saldo no Mês " + str(last_dropdown_month), f"R$ {balances_with_drops[last_dropdown_month]:,.0f}")
        st.metric("Parcela no Mês " + str(last_dropdown_month), f"R$ {payments_with_drops[last_dropdown_month-1]:,.0f}")
        st.metric("Quitação", f"{len(payments_with_drops)} meses")

    with col2:
        st.write("Sem Dropdowns")
        st.metric("Saldo no Mês " + str(last_dropdown_month), f"R$ {balances_no_drops[last_dropdown_month]:,.0f}")
        st.metric("Parcela no Mês " + str(last_dropdown_month), f"R$ {payments_no_drops[last_dropdown_month-1]:,.0f}")
        st.metric("Quitação", f"{len(payments_no_drops)} meses")

    with col3:
        st.write("KPIs")
        p_cl = payments_with_drops[0] / principal * 100
        cet_total = (sum(payments_with_drops) / principal - 1) * 100
        cet_anual = ((1 + cet_total/100) ** (12/months) - 1) * 100
        st.metric("P/CL", f"{p_cl:.2f}%")
        st.metric("CET Total", f"{cet_total:.2f}%")
        st.metric("CET Anual", f"{cet_anual:.2f}%")

    economia = sum(payments_no_drops[:last_dropdown_month]) - sum(payments_with_drops[:last_dropdown_month])
    st.metric("Economia até o Mês " + str(last_dropdown_month), f"R$ {economia:,.0f}", f"{economia/sum(payments_no_drops[:last_dropdown_month])*100:.2f}% de redução")

    # Adicionar Dropdown
    st.subheader("Adicionar Dropdown")
    col1, col2, col3 = st.columns(3)
    with col1:
        dropdown_month = st.number_input("Mês do Dropdown", min_value=1, max_value=months, value=12)
    with col2:
        current_balance = balances_with_drops[dropdown_month] if dropdown_month < len(balances_with_drops) else balances_with_drops[-1]
        dropdown_amount = st.number_input("Valor do Dropdown (R$)", 
                                          min_value=0.0, 
                                          max_value=float(current_balance), 
                                          value=0.0,
                                          step=1000.0)
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

    # Gráfico opcional de evolução das parcelas
    if st.checkbox("Mostrar Evolução das Parcelas"):
        st.subheader("Evolução das Parcelas")
        fig_parcelas = go.Figure()
        fig_parcelas.add_trace(go.Scatter(x=list(range(len(payments_no_drops))), y=payments_no_drops, mode='lines', name='Sem Dropdowns'))
        fig_parcelas.add_trace(go.Scatter(x=list(range(len(payments_with_drops))), y=payments_with_drops, mode='lines', name='Com Dropdowns'))
        st.plotly_chart(fig_parcelas, use_container_width=True)

    # Análise de Arbitragem
    st.subheader("Análise de Arbitragem")
    valor_captado = principal
    valor_quitacao = sum(payments_with_drops) + total_dropdown_value
    ganho_arbitragem = (valor_captado + total_agio) - valor_quitacao
    roi = (total_agio / total_dropdown_value) * 100 if total_dropdown_value > 0 else 0

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Valor Captado", f"R$ {valor_captado/1e6:.2f}M")
    col2.metric("Valor Quitação", f"R$ {valor_quitacao/1e6:.2f}M")
    col3.metric("Ganho com Ágio", f"R$ {total_agio/1e6:.2f}M")
    col4.metric("Ganho na Arbitragem", f"R$ {ganho_arbitragem/1e6:.2f}M")
    col5.metric("ROI da Estratégia", f"{roi:.2f}%")

if __name__ == "__main__":
    main()
