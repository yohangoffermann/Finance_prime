import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from datetime import date, timedelta

# Configuração da página
st.set_page_config(page_title="Simulador Constructa", layout="wide", page_icon="🏗️")

# Estilo CSS personalizado
st.markdown("""
<style>
    .main {background-color: #f0f2f6;}
    .stButton>button {background-color: #4CAF50; color: white;}
    .stTextInput>div>div>input {color: #4CAF50;}
    .stSelectbox>div>div>select {color: #4CAF50;}
    .stNumberInput>div>div>input {color: #4CAF50;}
    h1 {color: #2c3e50;}
    h2 {color: #34495e;}
    h3 {color: #16a085;}
</style>
""", unsafe_allow_html=True)

def calculate_balance(principal, months, admin_fee, dropdowns, agio):
    balance = principal
    balance_no_drops = principal
    monthly_payment = (principal / months) + (principal * admin_fee)
    balances = []
    balances_no_drops = []
    total_paid = 0
    total_drops = 0
    quitacao_month = months

    for month in range(1, months+1):
        total_paid += monthly_payment
        if balance > 0:
            balance = max(0, balance - monthly_payment)
            balance_no_drops = max(0, balance_no_drops - monthly_payment)
        
        if month in dropdowns:
            dropdown_value = dropdowns[month]
            dropdown_impact = dropdown_value * (1 + agio/100)
            balance = max(0, balance - dropdown_impact)
            total_drops += dropdown_value
        
        if balance == 0 and quitacao_month == months:
            quitacao_month = month

        balances.append(balance)
        balances_no_drops.append(balance_no_drops)
    
    return balances, balances_no_drops, monthly_payment, total_paid, total_drops, quitacao_month

def main():
    st.title("🏗️ Simulador Constructa")

    col1, col2 = st.columns([1, 3])

    with col1:
        st.subheader("Configurações")
        principal = st.number_input("Valor do Crédito (R$)", min_value=10000, value=100000, step=10000)
        months = st.number_input("Prazo (meses)", min_value=12, value=200, step=12)
        admin_fee = st.number_input("Taxa de Administração Mensal (%)", min_value=0.1, value=0.5, step=0.1) / 100
        agio = st.number_input("Ágio dos Dropdowns (%)", min_value=0.0, value=20.0, step=1.0)

        # Inicializar dropdowns na sessão se não existir
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

        # Display added dropdowns with delete option
        if st.session_state.dropdowns:
            st.subheader("Dropdowns Adicionados")
            for month, amount in list(st.session_state.dropdowns.items()):
                col1, col2 = st.columns([3, 1])
                col1.write(f"Mês {month}: R$ {amount:,.2f}")
                if col2.button("🗑️", key=f"delete_{month}"):
                    del st.session_state.dropdowns[month]
                    st.experimental_rerun()

    with col2:
        # Calculate balances
        balances, balances_no_drops, monthly_payment, total_paid, total_drops, quitacao_month = calculate_balance(principal, months, admin_fee, st.session_state.dropdowns, agio)

        # Plot
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=list(range(1, months+1)), y=balances, mode='lines', name='Com Dropdowns', line=dict(color='#2ecc71')))
        fig.add_trace(go.Scatter(x=list(range(1, months+1)), y=balances_no_drops, mode='lines', name='Sem Dropdowns', line=dict(color='#e74c3c')))
        fig.update_layout(
            title='Evolução do Saldo Devedor',
            xaxis_title='Meses',
            yaxis_title='Saldo (R$)',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            template="plotly_white"
        )
        st.plotly_chart(fig, use_container_width=True)

        # Monitors
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Saldo Devedor Final")
            st.info(f"Com Dropdowns: R$ {balances[-1]:,.2f}")
            st.error(f"Sem Dropdowns: R$ {balances_no_drops[-1]:,.2f}")
            st.success(f"Economia: R$ {balances_no_drops[-1] - balances[-1]:,.2f}")

        with col2:
            st.subheader("Parcela Mensal")
            st.info(f"Inicial: R$ {monthly_payment:,.2f}")
            if st.session_state.dropdowns:
                last_dropdown_month = max(st.session_state.dropdowns.keys())
                adjusted_balance = balances[last_dropdown_month-1]
                adjusted_months = months - last_dropdown_month + 1
                adjusted_payment = (adjusted_balance / adjusted_months) + (adjusted_balance * admin_fee)
                st.success(f"Após Último Dropdown: R$ {adjusted_payment:,.2f}")
                st.info(f"Redução: R$ {monthly_payment - adjusted_payment:,.2f}")
            else:
                st.warning("Sem alteração (nenhum dropdown aplicado)")

        # Análise de Quitação Antecipada
        if quitacao_month < months:
            st.subheader("Análise de Quitação Antecipada")
            valor_captado = total_paid + total_drops
            valor_quitacao = principal - sum(st.session_state.dropdowns.values())
            economia = valor_captado - valor_quitacao
            col1, col2, col3 = st.columns(3)
            col1.metric("Mês de Quitação", quitacao_month)
            col2.metric("Valor Total Captado", f"R$ {valor_captado:,.2f}")
            col3.metric("Valor Usado para Quitar", f"R$ {valor_quitacao:,.2f}")
            st.success(f"Economia Real: R$ {economia:,.2f}")
            st.info(f"Percentual de Economia: {(economia/principal)*100:.2f}%")

        # Simulador de Datas
        st.subheader("Simulador de Datas")
        start_date = st.date_input("Data de Início do Consórcio", date.today())
        
        end_date_no_drops = start_date + timedelta(days=30*months)
        end_date_with_drops = start_date + timedelta(days=30*quitacao_month)
        
        col1, col2 = st.columns(2)
        col1.info(f"Data de Término sem Dropdowns: {end_date_no_drops.strftime('%d/%m/%Y')}")
        col2.success(f"Data de Término com Dropdowns: {end_date_with_drops.strftime('%d/%m/%Y')}")
        
        if quitacao_month < months:
            dias_economizados = (end_date_no_drops - end_date_with_drops).days
            st.success(f"Você economizou {dias_economizados} dias com os dropdowns!")
            
            # Calculadora de Oportunidades para Incorporadores
            st.subheader("Oportunidades de Reinvestimento")
            valor_economizado = economia
            st.write(f"Com a economia de R$ {valor_economizado:,.2f}, você poderia:")
            
            col1, col2 = st.columns(2)
            with col1:
                metro_quadrado_medio = 1000  # Valor médio do m² para exemplo
                area_terreno = valor_economizado / metro_quadrado_medio
                st.info(f"1. Adquirir um terreno adicional de aproximadamente {area_terreno:.2f} m²")
                
                st.success(f"2. Investir em melhorias no empreendimento atual:")
                st.write(f"   - Upgrade de acabamentos: R$ {valor_economizado * 0.4:,.2f}")
                st.write(f"   - Áreas de lazer adicionais: R$ {valor_economizado * 0.3:,.2f}")
                st.write(f"   - Tecnologias sustentáveis: R$ {valor_economizado * 0.3:,.2f}")
                
                campanhas_marketing = valor_economizado * 0.2
                st.info(f"3. Investir R$ {campanhas_marketing:,.2f} em campanhas de marketing, potencialmente acelerando vendas")
            
            with col2:
                novo_projeto = valor_economizado * 0.7
                st.success(f"4. Iniciar um fundo de R$ {novo_projeto:,.2f} para um novo projeto de incorporação")
                
                retorno_estimado = valor_economizado * 1.15
                st.info(f"5. Se reinvestido no próximo projeto, esse valor pode gerar um retorno estimado de R$ {retorno_estimado:,.2f} (considerando 15% de retorno)")

                st.success(f"6. Antecipar o cronograma de obras em {dias_economizados} dias, potencialmente lançando o próximo projeto mais cedo")

if __name__ == "__main__":
    main()
