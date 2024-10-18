import streamlit as st
import plotly.graph_objects as go
from datetime import date, timedelta

# [Mantenha as configurações de página e estilos CSS como estavam]

def calculate_balance(principal, months, admin_fee, dropdowns, agio):
    # [Mantenha esta função como estava]

def main():
    st.title("Simulador Constructa")

    col1, col2 = st.columns([1, 3])

    with col1:
        # [Mantenha as configurações e inputs como estavam]

    with col2:
        balances, balances_no_drops, monthly_payments, total_paid, total_drops, quitacao_month = calculate_balance(principal, months, admin_fee, st.session_state.dropdowns, agio)

        # Exibição dos valores de saldo devedor e parcelas
        st.subheader("Resumo Financeiro")
        col_saldo, col_parcela = st.columns(2)

        with col_saldo:
            st.write("Saldo Devedor Final")
            saldo_com_drops = balances[-1]
            saldo_sem_drops = balances_no_drops[-1]
            economia = saldo_sem_drops - saldo_com_drops
            
            st.metric(
                label="Com Dropdowns",
                value=f"R$ {saldo_com_drops:,.2f}",
                delta=f"-R$ {economia:,.2f}",
                delta_color="inverse"
            )
            st.metric(
                label="Sem Dropdowns",
                value=f"R$ {saldo_sem_drops:,.2f}"
            )

        with col_parcela:
            st.write("Parcela Mensal")
            parcela_inicial = monthly_payments[0]
            if st.session_state.dropdowns:
                last_dropdown_month = max(st.session_state.dropdowns.keys())
                parcela_final = monthly_payments[last_dropdown_month]
                reducao = parcela_inicial - parcela_final
                
                st.metric(
                    label="Com Dropdowns",
                    value=f"R$ {parcela_final:,.2f}",
                    delta=f"-R$ {reducao:,.2f}",
                    delta_color="inverse"
                )
            else:
                parcela_final = parcela_inicial
            
            st.metric(
                label="Sem Dropdowns",
                value=f"R$ {parcela_inicial:,.2f}"
            )

        # Gráfico de Saldo Devedor
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

        # Opção para mostrar evolução das parcelas
        if st.checkbox("Mostrar Evolução das Parcelas"):
            fig_parcelas = go.Figure()
            fig_parcelas.add_trace(go.Scatter(x=list(range(1, months + 1)), y=monthly_payments, mode='lines', name='Parcelas', line=dict(color='#2ecc71')))
            fig_parcelas.update_layout(
                title='Evolução das Parcelas',
                xaxis_title='Meses',
                yaxis_title='Valor da Parcela (R$)',
                template="plotly_white"
            )
            st.plotly_chart(fig_parcelas, use_container_width=True)

        # [Mantenha o resto do código como estava: Análise de Quitação Antecipada, Simulador de Datas, etc.]

if __name__ == "__main__":
    main()
