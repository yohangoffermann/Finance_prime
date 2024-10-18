import streamlit as st
import plotly.graph_objects as go
from datetime import date, timedelta

def calculate_balance(principal, months, admin_fee, dropdowns, agio):
    balance = principal
    balance_no_drops = principal
    monthly_payment = (principal / months) + (principal * admin_fee)
    balances = [principal]
    balances_no_drops = [principal]
    total_paid = 0
    total_drops = 0
    quitacao_month = months

    for month in range(1, months + 1):
        total_paid += monthly_payment
        balance -= monthly_payment
        balance_no_drops -= monthly_payment
        
        if month in dropdowns:
            dropdown_value = dropdowns[month]
            dropdown_impact = dropdown_value * (1 + agio/100)
            balance -= dropdown_impact
            total_drops += dropdown_value
        
        balance = max(0, balance)
        balance_no_drops = max(0, balance_no_drops)
        
        balances.append(balance)
        balances_no_drops.append(balance_no_drops)
        
        if balance == 0 and quitacao_month == months:
            quitacao_month = month

    return balances, balances_no_drops, monthly_payment, total_paid, total_drops, quitacao_month

def main():
    st.title("Simulador Constructa")

    col1, col2 = st.columns([1, 3])

    with col1:
        st.subheader("Configurações")
        principal = st.number_input("Valor do Crédito (R$)", min_value=10000, value=100000, step=10000)
        months = st.number_input("Prazo (meses)", min_value=12, value=272, step=12)
        admin_fee = st.number_input("Taxa de Administração Mensal (%)", min_value=0.1, value=0.5, step=0.1) / 100
        agio = st.number_input("Ágio dos Dropdowns (%)", min_value=0.0, value=20.0, step=1.0)

        if 'dropdowns' not in st.session_state:
            st.session_state.dropdowns = {}

        st.subheader("Adicionar Dropdown")
        dropdown_month = st.number_input("Mês do Dropdown", min_value=1, max_value=months, value=12)
        dropdown_amount = st.number_input("Valor do Dropdown (R$)", min_value=1000, value=10000, step=1000)
        if st.button("Adicionar Dropdown", key="add_dropdown"):
            current_balance = principal - (dropdown_month * ((principal / months) + (principal * admin_fee)))
            if dropdown_amount <= current_balance:
                st.session_state.dropdowns[dropdown_month] = dropdown_amount
            else:
                st.warning("Valor do dropdown não pode ser maior que o saldo atual.")

        if st.session_state.dropdowns:
            st.subheader("Dropdowns Adicionados")
            for month, amount in list(st.session_state.dropdowns.items()):
                col1, col2 = st.columns([3, 1])
                col1.write(f"Mês {month}: R$ {amount:,.2f}")
                if col2.button("Remover", key=f"delete_{month}"):
                    del st.session_state.dropdowns[month]
                    st.experimental_rerun()

    with col2:
        balances, balances_no_drops, monthly_payment, total_paid, total_drops, quitacao_month = calculate_balance(principal, months, admin_fee, st.session_state.dropdowns, agio)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=list(range(months + 1)), y=balances_no_drops, mode='lines', name='Sem Dropdowns', line=dict(color='#e74c3c', dash='dash')))
        fig.add_trace(go.Scatter(x=list(range(months + 1)), y=balances, mode='lines', name='Com Dropdowns', line=dict(color='#1e3799')))
        fig.update_layout(
            title='Evolução do Saldo Devedor',
            xaxis_title='Meses',
            yaxis_title='Saldo (R$)',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            template="plotly_white"
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Análise Financeira")
        col1, col2 = st.columns(2)
        with col1:
            st.write("Saldo Devedor Final")
            st.write(f"Com Dropdowns: R$ {balances[-1]:,.2f}")
            st.write(f"Sem Dropdowns: R$ {balances_no_drops[-1]:,.2f}")
            st.write(f"Economia: R$ {balances_no_drops[-1] - balances[-1]:,.2f}")

        with col2:
            st.write("Parcela Mensal")
            st.write(f"Inicial: R$ {monthly_payment:,.2f}")
            if st.session_state.dropdowns:
                last_dropdown_month = max(st.session_state.dropdowns.keys())
                adjusted_balance = balances[last_dropdown_month]
                adjusted_months = months - last_dropdown_month
                adjusted_payment = (adjusted_balance / adjusted_months) + (adjusted_balance * admin_fee)
                st.write(f"Após Último Dropdown: R$ {adjusted_payment:,.2f}")
                st.write(f"Redução: R$ {monthly_payment - adjusted_payment:,.2f}")
            else:
                st.write("Sem alteração (nenhum dropdown aplicado)")

        if quitacao_month < months:
            st.subheader("Análise de Quitação Antecipada")
            valor_captado = total_paid + total_drops
            valor_quitacao = principal
            economia = valor_captado - valor_quitacao
            st.write(f"Mês de Quitação: {quitacao_month}")
            st.write(f"Valor Total Captado: R$ {valor_captado:,.2f}")
            st.write(f"Valor Usado para Quitar: R$ {valor_quitacao:,.2f}")
            st.write(f"Economia Real: R$ {economia:,.2f}")
            st.write(f"Percentual de Economia: {(economia/principal)*100:.2f}%")

        # ... [resto do código permanece o mesmo]

if __name__ == "__main__":
    main()
