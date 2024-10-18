import streamlit as st
import plotly.graph_objects as go

# Configuração da página
st.set_page_config(page_title="Simulador Constructa", layout="wide")

def calculate_balance(principal, months, admin_fee, dropdowns, agio):
    balance = principal
    balance_no_drops = principal
    amortization = principal / months
    balances = [principal]
    balances_no_drops = [principal]
    monthly_payments = []
    monthly_payments_no_drops = []
    total_dropdown_value = 0
    total_dropdown_impact = 0

    for month in range(1, months + 1):
        admin_fee_value = balance * admin_fee
        monthly_payment = amortization + admin_fee_value
        
        balance -= amortization
        balance_no_drops -= amortization
        
        if month in dropdowns:
            dropdown_value = dropdowns[month]
            dropdown_impact = dropdown_value * (1 + agio/100)
            balance -= dropdown_impact
            total_dropdown_value += dropdown_value
            total_dropdown_impact += dropdown_impact
            
            # Recalcular amortização após o dropdown
            remaining_months = months - month + 1
            if remaining_months > 0:
                amortization = balance / remaining_months
        
        balance = max(0, balance)
        balance_no_drops = max(0, balance_no_drops)
        
        balances.append(balance)
        balances_no_drops.append(balance_no_drops)
        monthly_payments.append(monthly_payment)
        monthly_payments_no_drops.append(amortization + balance_no_drops * admin_fee)

    agio_gain = total_dropdown_impact - total_dropdown_value
    return balances, balances_no_drops, monthly_payments, monthly_payments_no_drops, agio_gain

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

    # Cálculos iniciais
    balances, balances_no_drops, monthly_payments, monthly_payments_no_drops, agio_gain = calculate_balance(
        principal, months, admin_fee, st.session_state.dropdowns, agio
    )

    # Mostrar saldo devedor atual
    current_balance = balances[-1]
    st.subheader(f"Saldo Devedor Atual: R$ {current_balance:,.2f}")

    # Seção de Adicionar Dropdown
    st.subheader("Adicionar Dropdown")
    col1, col2, col3 = st.columns(3)
    with col1:
        dropdown_month = st.number_input("Mês do Dropdown", min_value=1, max_value=months, value=min(12, months))
    with col2:
        max_dropdown = balances[dropdown_month-1] if dropdown_month <= len(balances) else current_balance
        dropdown_amount = st.number_input("Valor do Dropdown (R$)", min_value=0, max_value=float(max_dropdown), value=min(10000, float(max_dropdown)), step=1000)
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

    # Resumo Financeiro
    st.subheader("Resumo Financeiro")
    col1, col2, col3 = st.columns(3)
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
    with col3:
        st.write("Ganho com Ágio")
        st.write(f"Valor: R$ {agio_gain:,.2f}")

if __name__ == "__main__":
    main()
