import streamlit as st
import pandas as pd
import plotly.graph_objects as go

def main():
    st.title("Constructa Simulator")

    # Sidebar para inputs principais
    st.sidebar.header("Configurações Iniciais")
    dnd = st.sidebar.number_input("Dinheiro Novo Desejado (R$)", min_value=100000, value=1000000)
    prazo = st.sidebar.slider("Prazo (meses)", min_value=60, max_value=240, value=200)
    modelo = st.sidebar.radio("Modelo", ["PLE", "CCC"])

    # Linha do Tempo Principal
    st.header("Linha do Tempo do Empreendimento")
    etapas = ["Captação", "Empreendimento", "Saída"]
    etapa_atual = st.selectbox("Selecione a Etapa", etapas)

    if etapa_atual == "Captação":
        mostrar_etapa_captacao(modelo, dnd, prazo)
    elif etapa_atual == "Empreendimento":
        mostrar_etapa_empreendimento(modelo, dnd, prazo)
    elif etapa_atual == "Saída":
        mostrar_etapa_saida(modelo, dnd, prazo)

def mostrar_etapa_captacao(modelo, dnd, prazo):
    st.subheader("Etapa de Captação")
    if modelo == "PLE":
        lance_pago = st.slider("Lance Pago (R$)", min_value=0, max_value=int(dnd/2), value=int(dnd/4))
        lance_embutido = lance_pago  # Assumindo lance embutido igual ao pago
        credito_liberado = dnd - lance_pago - lance_embutido
        st.write(f"Crédito Liberado: R$ {credito_liberado:,}")
    else:  # CCC
        st.write("Simulação de acúmulo de crédito ao longo do tempo")
        # Aqui viria a lógica de simulação do CCC

    # Simulação de Dropdown
    st.subheader("Simulação de Dropdown")
    meses_para_dropdown = st.slider("Meses até o Dropdown", min_value=1, max_value=prazo, value=12)
    valor_dropdown = st.number_input("Valor do Dropdown (R$)", min_value=0, max_value=int(dnd/2), value=int(dnd/10))
    agio = st.slider("Ágio (%)", min_value=0, max_value=50, value=20)

    impacto_dropdown = valor_dropdown * (1 + agio/100)
    st.write(f"Impacto do Dropdown: R$ {impacto_dropdown:,}")

    # Gráfico com Dropdown
    st.plotly_chart(criar_grafico_com_dropdown(dnd, prazo, meses_para_dropdown, impacto_dropdown))

def mostrar_etapa_empreendimento(modelo, dnd, prazo):
    st.subheader("Etapa do Empreendimento")
    # Lógica específica para a etapa do empreendimento
    st.write("Simulação de uso do crédito no empreendimento")

def mostrar_etapa_saida(modelo, dnd, prazo):
    st.subheader("Etapa de Saída")
    # Lógica específica para a etapa de saída
    st.write("Simulação de estratégias de saída e dropdowns")

def criar_grafico_com_dropdown(dnd, prazo, mes_dropdown, impacto_dropdown):
    # Cria um gráfico com o efeito do dropdown
    meses = list(range(prazo + 1))
    saldo_sem_dropdown = [dnd - (dnd/prazo)*m for m in meses]
    saldo_com_dropdown = [
        dnd - (dnd/prazo)*m if m < mes_dropdown 
        else dnd - (dnd/prazo)*m - impacto_dropdown 
        for m in meses
    ]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=meses, y=saldo_sem_dropdown, mode='lines', name='Sem Dropdown'))
    fig.add_trace(go.Scatter(x=meses, y=saldo_com_dropdown, mode='lines', name='Com Dropdown'))
    fig.update_layout(title='Impacto do Dropdown no Saldo Devedor', xaxis_title='Meses', yaxis_title='Saldo Devedor (R$)')
    return fig

if __name__ == "__main__":
    main()
