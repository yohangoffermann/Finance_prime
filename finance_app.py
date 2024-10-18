import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
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
    st.title("Simulador Constructa")

    col1, col2 = st.columns([1, 3])

    with col1:
        st.subheader("Configurações")
        principal = st.number_input("Valor do Crédito (R$)", min_value=10000, value=100000, step=10000)
        months = st.number_input("Prazo (meses)", min_value=12, value=200, step=12)
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

        # Novo código do gráfico
        offset = max(balances_no_drops) * 0.01  # 1% do valor máximo como offset
        balances_offset = [b + offset for b in balances_no_drops]

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=list(range(1, months+1)), y=balances_offset, mode='lines', name='Sem Dropdowns', line=dict(color='#e74c3c', dash='dash')))
        fig.add_trace(go.Scatter(x=list(range(1, months+1)), y=balances, mode='lines', name='Com Dropdowns', line=dict(color='#1e3799')))
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
                adjusted_balance = balances[last_dropdown_month-1]
                adjusted_months = months - last_dropdown_month + 1
                adjusted_payment = (adjusted_balance / adjusted_months) + (adjusted_balance * admin_fee)
                st.write(f"Após Último Dropdown: R$ {adjusted_payment:,.2f}")
                st.write(f"Redução: R$ {monthly_payment - adjusted_payment:,.2f}")
            else:
                st.write("Sem alteração (nenhum dropdown aplicado)")

        if quitacao_month < months:
            st.subheader("Análise de Quitação Antecipada")
            valor_captado = total_paid + total_drops
            valor_quitacao = principal - sum(st.session_state.dropdowns.values())
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
