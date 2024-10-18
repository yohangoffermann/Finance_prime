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
    last_month = months

    col1, col2 = st.columns(2)
    with col1:
        st.write("Saldo Devedor")
        st.metric("Inicial", f"R$ {principal:,.2f}")
        st.metric("Final", f"R$ {balances[-1]:,.2f}")

    with col2:
        st.write("Parcela Mensal")
        st.metric("Inicial", f"R$ {monthly_payments[0]:,.2f}")
        st.metric("Final", f"R$ {monthly_payments[-1]:,.2f}")

    total_pago = sum(monthly_payments)
    cet = (total_pago / principal - 1) * 100

    st.subheader("Análise Financeira")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Pago", f"R$ {total_pago:,.2f}")
    with col2:
        st.metric("Custo Efetivo Total (CET)", f"{cet:.2f}%")
    with col3:
        st.metric("Prazo Total", f"{months} meses")

    if st.session_state.dropdowns:
        amortizacao = total_dropdown_value
        ganho_agio = agio_gain
        economia_parcelas = sum(monthly_payments_no_drops) - sum(monthly_payments)
        economia_real = economia_parcelas - ganho_agio

        st.subheader("Impacto dos Dropdowns")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Amortização Antecipada", f"R$ {amortizacao:,.2f}")
        with col2:
            st.metric("Ganho com Ágio", f"R$ {ganho_agio:,.2f}")
        with col3:
            st.metric("Economia Real", f"R$ {economia_real:,.2f}")

        st.write(f"Impacto Total: R$ {amortizacao + ganho_agio + economia_real:,.2f}")

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

    # Simulador de Datas
    st.subheader("Simulador de Datas")
    start_date = st.date_input("Data de Início do Consórcio", date.today())
    end_date = start_date + timedelta(days=30*months)
    
    st.metric("Data de Término", end_date.strftime('%d/%m/%Y'))

    # Oportunidades de Reinvestimento
    if st.session_state.dropdowns:
        st.subheader("Oportunidades de Reinvestimento")
        st.write(f"Com a economia de R$ {economia_real:,.2f}, você poderia:")
        
        col1, col2 = st.columns(2)
        with col1:
            metro_quadrado_medio = 5000
            area_terreno = economia_real / metro_quadrado_medio
            st.info(f"1. Adquirir um terreno adicional de aproximadamente {area_terreno:.2f} m²")
            st.success(f"2. Investir em melhorias no empreendimento atual:")
            st.write(f"   - Upgrade de acabamentos: R$ {economia_real * 0.4:,.2f}")
            st.write(f"   - Áreas de lazer adicionais: R$ {economia_real * 0.3:,.2f}")
            st.write(f"   - Tecnologias sustentáveis: R$ {economia_real * 0.3:,.2f}")
        
        with col2:
            campanhas_marketing = economia_real * 0.2
            st.info(f"3. Investir R$ {campanhas_marketing:,.2f} em campanhas de marketing")
            novo_projeto = economia_real * 0.7
            st.success(f"4. Iniciar um fundo de R$ {novo_projeto:,.2f} para um novo projeto")
            retorno_estimado = economia_real * 1.15
            st.warning(f"5. Potencial retorno estimado de R$ {retorno_estimado:,.2f} se reinvestido (15% a.a.)")

if __name__ == "__main__":
    main()
