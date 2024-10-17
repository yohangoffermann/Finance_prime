import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from datetime import date, timedelta

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
    st.title("Simulador Constructa com Dropdowns")

    # Inputs
    principal = st.sidebar.number_input("Valor do Crédito", min_value=10000, value=100000, step=10000)
    months = st.sidebar.number_input("Prazo (meses)", min_value=12, value=200, step=12)
    admin_fee = st.sidebar.number_input("Taxa de Administração Mensal (%)", min_value=0.1, value=0.5, step=0.1) / 100
    agio = st.sidebar.number_input("Ágio dos Dropdowns (%)", min_value=0.0, value=20.0, step=1.0)

    # Inicializar dropdowns na sessão se não existir
    if 'dropdowns' not in st.session_state:
        st.session_state.dropdowns = {}

    # Dropdown inputs
    st.sidebar.subheader("Adicionar Dropdown")
    dropdown_month = st.sidebar.number_input("Mês do Dropdown", min_value=1, max_value=months, value=12)
    dropdown_amount = st.sidebar.number_input("Valor do Dropdown", min_value=1000, value=10000, step=1000)
    if st.sidebar.button("Adicionar Dropdown"):
        current_balance = principal - (dropdown_month * ((principal / months) + (principal * admin_fee)))
        if dropdown_amount <= current_balance:
            st.session_state.dropdowns[dropdown_month] = dropdown_amount
        else:
            st.sidebar.warning("Valor do dropdown não pode ser maior que o saldo atual.")

    # Display added dropdowns
    if st.session_state.dropdowns:
        st.sidebar.subheader("Dropdowns Adicionados")
        for month, amount in st.session_state.dropdowns.items():
            st.sidebar.write(f"Mês {month}: R$ {amount}")

    # Calculate balances
    balances, balances_no_drops, monthly_payment, total_paid, total_drops, quitacao_month = calculate_balance(principal, months, admin_fee, st.session_state.dropdowns, agio)

    # Plot
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=list(range(1, months+1)), y=balances, mode='lines', name='Com Dropdowns'))
    fig.add_trace(go.Scatter(x=list(range(1, months+1)), y=balances_no_drops, mode='lines', name='Sem Dropdowns'))
    fig.update_layout(title='Evolução do Saldo Devedor', xaxis_title='Meses', yaxis_title='Saldo (R$)')
    fig.add_annotation(
        text="Ambas as curvas param em zero quando o saldo é quitado",
        xref="paper", yref="paper",
        x=0.5, y=-0.15,
        showarrow=False
    )
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
        if st.session_state.dropdowns:
            last_dropdown_month = max(st.session_state.dropdowns.keys())
            adjusted_balance = balances[last_dropdown_month-1]
            adjusted_months = months - last_dropdown_month + 1
            adjusted_payment = (adjusted_balance / adjusted_months) + (adjusted_balance * admin_fee)
            st.write(f"Após Último Dropdown: R$ {adjusted_payment:,.2f}")
            st.write(f"Redução: R$ {monthly_payment - adjusted_payment:,.2f}")
        else:
            st.write("Sem alteração (nenhum dropdown aplicado)")

    # Análise de Quitação Antecipada
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

    # Total impact of dropdowns
    if st.session_state.dropdowns:
        total_dropdown_value = sum(st.session_state.dropdowns.values())
        total_dropdown_impact = total_dropdown_value * (1 + agio/100)
        st.subheader("Impacto Total dos Dropdowns")
        st.write(f"Valor Total dos Dropdowns: R$ {total_dropdown_value:,.2f}")
        st.write(f"Impacto Total (com ágio): R$ {total_dropdown_impact:,.2f}")
        st.write(f"Ganho com Ágio: R$ {total_dropdown_impact - total_dropdown_value:,.2f}")

    # Simulador de Datas
    st.subheader("Simulador de Datas")
    start_date = st.date_input("Data de Início do Consórcio", date.today())
    
    end_date_no_drops = start_date + timedelta(days=30*months)
    end_date_with_drops = start_date + timedelta(days=30*quitacao_month)
    
    st.write(f"Data de Término sem Dropdowns: {end_date_no_drops.strftime('%d/%m/%Y')}")
    st.write(f"Data de Término com Dropdowns: {end_date_with_drops.strftime('%d/%m/%Y')}")
    
    if quitacao_month < months:
        dias_economizados = (end_date_no_drops - end_date_with_drops).days
        st.write(f"Você economizou {dias_economizados} dias com os dropdowns!")
        
        # Calculadora de Oportunidades para Incorporadores
        st.subheader("Oportunidades de Reinvestimento")
        valor_economizado = economia
        st.write(f"Com a economia de R$ {valor_economizado:,.2f}, você poderia:")
        
        # 1. Aquisição de Terreno
        metro_quadrado_medio = 1000  # Valor médio do m² para exemplo
        area_terreno = valor_economizado / metro_quadrado_medio
        st.write(f"1. Adquirir um terreno adicional de aproximadamente {area_terreno:.2f} m²")
        
        # 2. Melhorias no Empreendimento Atual
        st.write(f"2. Investir em melhorias no empreendimento atual:")
        st.write(f"   - Upgrade de acabamentos: R$ {valor_economizado * 0.4:,.2f}")
        st.write(f"   - Áreas de lazer adicionais: R$ {valor_economizado * 0.3:,.2f}")
        st.write(f"   - Tecnologias sustentáveis: R$ {valor_economizado * 0.3:,.2f}")
        
        # 3. Marketing e Vendas
        campanhas_marketing = valor_economizado * 0.2
        st.write(f"3. Investir R$ {campanhas_marketing:,.2f} em campanhas de marketing, potencialmente acelerando vendas")
        
        # 4. Fundo para Novo Projeto
        novo_projeto = valor_economizado * 0.7
        st.write(f"4. Iniciar um fundo de R$ {novo_projeto:,.2f} para um novo projeto de incorporação")
        
        # 5. Análise de Retorno
        retorno_estimado = valor_economizado * 1.15
        st.write(f"5. Se reinvestido no próximo projeto, esse valor pode gerar um retorno estimado de R$ {retorno_estimado:,.2f} (considerando 15% de retorno)")

        # 6. Antecipação de Cronograma
        st.write(f"6. Antecipar o cronograma de obras em {dias_economizados} dias, potencialmente lançando o próximo projeto mais cedo")

if __name__ == "__main__":
    main()
