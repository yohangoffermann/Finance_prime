import streamlit as st
import plotly.graph_objects as go
from datetime import date, timedelta

# Configuração da página
st.set_page_config(page_title="Simulador Constructa", layout="wide")

def calculate_balance(principal, months, admin_fee, dropdowns, agio):
    balance = principal
    balance_no_drops = principal
    original_amortization = principal / months
    balances = [principal]
    balances_no_drops = [principal]
    monthly_payments = []
    monthly_payments_no_drops = []
    total_dropdown_value = 0
    total_dropdown_impact = 0

    for month in range(1, months + 1):
        admin_fee_value = balance * admin_fee
        monthly_payment = original_amortization + admin_fee_value
        monthly_payment_no_drops = original_amortization + (balance_no_drops * admin_fee)
        
        if month in dropdowns:
            dropdown_value = dropdowns[month]
            dropdown_impact = dropdown_value * (1 + agio/100)
            balance -= dropdown_impact
            total_dropdown_value += dropdown_value
            total_dropdown_impact += dropdown_impact
            
            # Recalcular apenas a parcela, mantendo o prazo original
            admin_fee_value = balance * admin_fee
            monthly_payment = original_amortization + admin_fee_value
        
        balance -= original_amortization
        balance_no_drops -= original_amortization
        
        balance = max(0, balance)
        balance_no_drops = max(0, balance_no_drops)
        
        balances.append(balance)
        balances_no_drops.append(balance_no_drops)
        monthly_payments.append(monthly_payment)
        monthly_payments_no_drops.append(monthly_payment_no_drops)

    agio_gain = total_dropdown_impact - total_dropdown_value
    return balances, balances_no_drops, monthly_payments, monthly_payments_no_drops, agio_gain, total_dropdown_value

def main():
    st.title("Simulador Constructa")

    # Sidebar para inputs principais
    with st.sidebar:
        st.header("Configurações Principais")
        principal = st.number_input("Valor do Crédito (R$)", min_value=10000, value=1800000, step=10000)
        months = st.number_input("Prazo (meses)", min_value=12, value=210, step=12)
        admin_fee = st.number_input("Taxa de Administração Mensal (%)", min_value=0.1, value=0.12, step=0.01) / 100
        agio = st.number_input("Ágio dos Dropdowns (%)", min_value=0.0, value=25.0, step=1.0)

    # Inicialização dos dropdowns
    if 'dropdowns' not in st.session_state:
        st.session_state.dropdowns = {}

    # Cálculos
    balances, balances_no_drops, monthly_payments, monthly_payments_no_drops, agio_gain, total_dropdown_value = calculate_balance(
        principal, months, admin_fee, st.session_state.dropdowns, agio
    )

    # Resumo Financeiro
    st.subheader("Resumo Financeiro")
    last_dropdown_month = max(st.session_state.dropdowns.keys()) if st.session_state.dropdowns else months

    col1, col2 = st.columns(2)
    with col1:
        st.write(f"Saldo Devedor (no mês {last_dropdown_month})")
        saldo_com_drops = balances[last_dropdown_month]
        saldo_sem_drops = balances_no_drops[last_dropdown_month]
        reducao_saldo = saldo_sem_drops - saldo_com_drops
        st.metric("Com Dropdowns", f"R$ {saldo_com_drops:,.2f}", delta=f"-R$ {reducao_saldo:,.2f}", delta_color="inverse")
        st.metric("Sem Dropdowns", f"R$ {saldo_sem_drops:,.2f}")

    with col2:
        st.write(f"Parcela Mensal (no mês {last_dropdown_month})")
        parcela_com_drops = monthly_payments[last_dropdown_month-1]
        parcela_sem_drops = monthly_payments_no_drops[last_dropdown_month-1]
        reducao_parcela = parcela_sem_drops - parcela_com_drops
        st.metric("Com Dropdowns", f"R$ {parcela_com_drops:,.2f}", delta=f"-R$ {reducao_parcela:,.2f}", delta_color="inverse")
        st.metric("Sem Dropdowns", f"R$ {parcela_sem_drops:,.2f}")

    # Adicionar Dropdown
    st.subheader("Adicionar Dropdown")
    col1, col2, col3 = st.columns(3)
    with col1:
        dropdown_month = st.number_input("Mês do Dropdown", min_value=1, max_value=months, value=min(12, months))
    with col2:
        current_balance = balances[dropdown_month-1] if dropdown_month <= len(balances) else balances[-1]
        dropdown_amount = st.number_input("Valor do Dropdown (R$)", min_value=0, max_value=int(current_balance), value=min(10000, int(current_balance)), step=1000)
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

    # Gráfico de Saldo Devedor
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=list(range(months + 1)), y=balances_no_drops, mode='lines', name='Sem Dropdowns', line=dict(color='#e74c3c', dash='dash')))
    fig.add_trace(go.Scatter(x=list(range(months + 1)), y=balances, mode='lines', name='Com Dropdowns', line=dict(color='#1e3799')))
    fig.update_layout(title='Evolução do Saldo Devedor', xaxis_title='Meses', yaxis_title='Saldo (R$)')
    st.plotly_chart(fig, use_container_width=True)

    # Análise de Arbitragem Financeira
    st.subheader("Análise de Arbitragem Financeira")
    valor_captado = principal
    valor_quitacao = sum(monthly_payments[:last_dropdown_month]) + sum(st.session_state.dropdowns.values())
    ganho_arbitragem = valor_captado - valor_quitacao

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Valor Captado", f"R$ {valor_captado:,.2f}")
    with col2:
        st.metric("Valor Usado para Quitar", f"R$ {valor_quitacao:,.2f}")
    with col3:
        st.metric("Ganho na Arbitragem", f"R$ {ganho_arbitragem:,.2f}")

    # Cálculo do ROI
    if st.session_state.dropdowns:
        investimento_drops = sum(st.session_state.dropdowns.values())
        roi = (ganho_arbitragem / investimento_drops - 1) * 100
        st.metric("ROI da Estratégia", f"{roi:.2f}%")

    # Tempo para recuperar o investimento em dropdowns
    if ganho_arbitragem > 0:
        tempo_recuperacao = investimento_drops / (ganho_arbitragem / last_dropdown_month)
        st.write(f"Tempo estimado para recuperar o investimento em dropdowns: {tempo_recuperacao:.1f} meses")

    st.write(f"Esta estratégia permite captar R$ {valor_captado:,.2f} e quitar por R$ {valor_quitacao:,.2f}, " 
             f"resultando em um ganho de R$ {ganho_arbitragem:,.2f}.")

    # Simulador de Datas
    st.subheader("Simulador de Datas")
    start_date = st.date_input("Data de Início do Consórcio", date.today())
    end_date = start_date + timedelta(days=30*months)
    
    st.metric("Data de Término", end_date.strftime('%d/%m/%Y'))

if __name__ == "__main__":
    main()
