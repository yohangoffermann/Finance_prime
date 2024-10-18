import streamlit as st
import plotly.graph_objects as go
from datetime import date, timedelta

# Configuração da página
st.set_page_config(page_title="Simulador Constructa", layout="wide")

# Estilo CSS personalizado
st.markdown("""
<style>
    .main {background-color: #f0f2f6;}
    .stButton>button {background-color: #1e3799; color: white;}
    .stTextInput>div>div>input {color: #2c3e50;}
    .stSelectbox>div>div>select {color: #2c3e50;}
    .stNumberInput>div>div>input {color: #2c3e50;}
    h1 {color: #1e3799;}
    h2 {color: #34495e;}
    h3 {color: #2980b9;}
</style>
""", unsafe_allow_html=True)

def calculate_balance(principal, months, admin_fee, dropdowns, agio):
    balance = principal
    balance_no_drops = principal
    amortization = principal / months
    balances = [principal]
    balances_no_drops = [principal]
    total_paid = 0
    total_drops = 0
    quitacao_month = months
    monthly_payments = []

    for month in range(1, months + 1):
        admin_fee_value = balance * admin_fee
        monthly_payment = amortization + admin_fee_value
        
        balance -= amortization
        balance_no_drops -= amortization
        
        total_paid += monthly_payment
        
        if month in dropdowns:
            dropdown_value = dropdowns[month]
            dropdown_impact = dropdown_value * (1 + agio/100)
            balance -= dropdown_impact
            total_drops += dropdown_value
            
            # Recalcular amortização após o dropdown
            remaining_months = months - month
            if remaining_months > 0:
                amortization = balance / remaining_months
        
        balance = max(0, balance)
        balance_no_drops = max(0, balance_no_drops)
        
        balances.append(balance)
        balances_no_drops.append(balance_no_drops)
        monthly_payments.append(monthly_payment)
        
        if balance == 0 and quitacao_month == months:
            quitacao_month = month

    return balances, balances_no_drops, monthly_payments, total_paid, total_drops, quitacao_month

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
            current_balance = principal - (dropdown_month * (principal / months))
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
        balances, balances_no_drops, monthly_payments, total_paid, total_drops, quitacao_month = calculate_balance(principal, months, admin_fee, st.session_state.dropdowns, agio)

        col_saldo, col_parcela = st.columns(2)

        with col_saldo:
            st.subheader("Saldo Devedor Final")
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
            st.subheader("Parcela Mensal")
            parcela_inicial = monthly_payments[0]
            if st.session_state.dropdowns:
                last_dropdown_month = max(st.session_state.dropdowns.keys())
                parcela_final = monthly_payments[last_dropdown_month]
                reducao = parcela_inicial - parcela_final
                
                st.metric(
                    label="Parcela Final",
                    value=f"R$ {parcela_final:,.2f}",
                    delta=f"-R$ {reducao:,.2f}",
                    delta_color="inverse"
                )
            else:
                parcela_final = parcela_inicial
            
            st.metric(
                label="Parcela Inicial",
                value=f"R$ {parcela_inicial:,.2f}"
            )

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

        st.subheader("Simulador de Datas")
        start_date = st.date_input("Data de Início do Consórcio", date.today())
        
        end_date_no_drops = start_date + timedelta(days=30*months)
        end_date_with_drops = start_date + timedelta(days=30*quitacao_month)
        
        st.write(f"Data de Término sem Dropdowns: {end_date_no_drops.strftime('%d/%m/%Y')}")
        st.write(f"Data de Término com Dropdowns: {end_date_with_drops.strftime('%d/%m/%Y')}")
        
        if quitacao_month < months:
            dias_economizados = (end_date_no_drops - end_date_with_drops).days
            st.write(f"Dias economizados: {dias_economizados}")
            
            st.subheader("Oportunidades de Reinvestimento")
            valor_economizado = economia
            st.write(f"Com a economia de R$ {valor_economizado:,.2f}, você poderia:")
            
            metro_quadrado_medio = 1000
            area_terreno = valor_economizado / metro_quadrado_medio
            st.write(f"1. Adquirir um terreno adicional de aproximadamente {area_terreno:.2f} m²")
            
            st.write(f"2. Investir em melhorias no empreendimento atual:")
            st.write(f"   - Upgrade de acabamentos: R$ {valor_economizado * 0.4:,.2f}")
            st.write(f"   - Áreas de lazer adicionais: R$ {valor_economizado * 0.3:,.2f}")
            st.write(f"   - Tecnologias sustentáveis: R$ {valor_economizado * 0.3:,.2f}")
            
            campanhas_marketing = valor_economizado * 0.2
            st.write(f"3. Investir R$ {campanhas_marketing:,.2f} em campanhas de marketing")
            
            novo_projeto = valor_economizado * 0.7
            st.write(f"4. Iniciar um fundo de R$ {novo_projeto:,.2f} para um novo projeto")
            
            retorno_estimado = valor_economizado * 1.15
            st.write(f"5. Potencial retorno estimado de R$ {retorno_estimado:,.2f} se reinvestido (15% a.a.)")

            st.write(f"6. Antecipar o cronograma de obras em {dias_economizados} dias")

if __name__ == "__main__":
    main()
