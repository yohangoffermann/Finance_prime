import streamlit as st
import pandas as pd
import plotly.graph_objects as go

def main():
    st.title("Constructa Simulator")

    # Sidebar para inputs principais
    with st.sidebar:
        st.header("Configurações Iniciais")
        dnd = st.number_input("Dinheiro Novo Desejado (R$)", min_value=100000, value=1000000)
        prazo = st.slider("Prazo (meses)", min_value=60, max_value=240, value=200)
        capital_disponivel = st.number_input("Capital Disponível (R$)", min_value=0, value=100000)
        modelo = st.radio("Modelo", ["PLE", "CCC"])

    # Tela principal
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Gráfico de Saldo Devedor")
        fig = plot_saldo_devedor(dnd, prazo, capital_disponivel, modelo)
        st.plotly_chart(fig)

    with col2:
        st.subheader("KPIs")
        kpis = calcular_kpis(dnd, prazo, capital_disponivel, modelo)
        st.metric("P/CL", f"{kpis['P/CL']:.2f}%")
        st.metric("P/DN", f"{kpis['P/DN']:.2f}%")
        st.metric("CET", f"{kpis['CET']:.2f}%")

    st.subheader("Linha do Tempo para Dropdowns")
    adicionar_dropdown = st.button("Adicionar Dropdown")
    if adicionar_dropdown:
        st.write("Funcionalidade de adicionar dropdown será implementada aqui")

    st.subheader("Detalhes da Simulação")
    detalhes = calcular_detalhes(dnd, prazo, capital_disponivel, modelo)
    st.write(f"Parcela Mensal: R$ {detalhes['parcela']:.2f}")
    st.write(f"Crédito Total: R$ {detalhes['credito_total']:.2f}")
    st.write(f"Crédito Liberado: R$ {detalhes['credito_liberado']:.2f}")

def plot_saldo_devedor(dnd, prazo, capital_disponivel, modelo):
    # Simulação simplificada do saldo devedor
    x = list(range(prazo + 1))
    y_sem_constructa = [dnd - (dnd/prazo)*i for i in x]
    y_com_constructa = [dnd - (dnd/prazo)*i*1.2 for i in x]  # Exemplo simplificado

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y_sem_constructa, mode='lines', name='Sem Constructa'))
    fig.add_trace(go.Scatter(x=x, y=y_com_constructa, mode='lines', name='Com Constructa'))
    fig.update_layout(title='Evolução do Saldo Devedor', xaxis_title='Meses', yaxis_title='Saldo (R$)')
    return fig

def calcular_kpis(dnd, prazo, capital_disponivel, modelo):
    # Cálculos simplificados dos KPIs
    return {
        "P/CL": 0.8,
        "P/DN": 0.7,
        "CET": 0.55
    }

def calcular_detalhes(dnd, prazo, capital_disponivel, modelo):
    # Cálculos simplificados dos detalhes
    return {
        "parcela": dnd / prazo,
        "credito_total": dnd,
        "credito_liberado": dnd - capital_disponivel
    }

if __name__ == "__main__":
    main()
