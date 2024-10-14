import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def calcular_relacao_parcela_credito(valor_cota, taxa_admin_anual, prazo_meses):
    taxa_admin_mensal = taxa_admin_anual / 12 / 100
    parcela = (valor_cota / prazo_meses) + (valor_cota * taxa_admin_mensal)
    relacao = (parcela / valor_cota) * 100
    return relacao

def calcular_economia(valor_total, taxa_tradicional_anual, taxa_constructa_anual, prazo_meses):
    taxa_tradicional_mensal = (1 + taxa_tradicional_anual/100)**(1/12) - 1
    taxa_constructa_mensal = (1 + taxa_constructa_anual/100)**(1/12) - 1
    
    custo_tradicional = valor_total * ((1 + taxa_tradicional_mensal)**prazo_meses - 1) / taxa_tradicional_mensal
    custo_constructa = valor_total * ((1 + taxa_constructa_mensal)**prazo_meses - 1) / taxa_constructa_mensal
    
    economia = custo_tradicional - custo_constructa
    return economia

def calcular_fluxo_caixa(valor_total, prazo_meses, percentual_lance, taxa_admin_anual):
    lance = valor_total * (percentual_lance / 100)
    credito_novo = valor_total - lance
    taxa_admin_mensal = taxa_admin_anual / 12 / 100
    parcela = (credito_novo / prazo_meses) + (valor_total * taxa_admin_mensal)
    
    fluxo_caixa = [-lance]  # Mês 0: pagamento do lance
    for _ in range(prazo_meses):
        fluxo_caixa.append(-parcela)
    
    return fluxo_caixa

def simular_dropdown(valor_total, prazo_meses, percentual_lance, taxa_admin_anual, mes_dropdown, percentual_dropdown):
    fluxo_inicial = calcular_fluxo_caixa(valor_total, prazo_meses, percentual_lance, taxa_admin_anual)
    
    valor_dropdown = valor_total * (percentual_dropdown / 100)
    credito_apos_dropdown = valor_total - valor_dropdown
    parcela_apos_dropdown = (credito_apos_dropdown / prazo_meses) + (credito_apos_dropdown * taxa_admin_anual / 12 / 100)
    
    for i in range(mes_dropdown, prazo_meses):
        fluxo_inicial[i] = -parcela_apos_dropdown
    
    fluxo_inicial[mes_dropdown] += valor_dropdown  # Receita do dropdown
    
    return fluxo_inicial

def plot_fluxo_caixa(fluxo_caixa, titulo):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(range(len(fluxo_caixa)), fluxo_caixa, marker='o')
    ax.set_title(titulo)
    ax.set_xlabel('Mês')
    ax.set_ylabel('Fluxo de Caixa (R$)')
    ax.grid(True)
    return fig

def main():
    st.title("Constructa - Simulador de Crédito Otimizado")

    st.header("Dados do Projeto")
    valor_total = st.number_input("Valor total do projeto (R$)", min_value=0.0, value=1000000.0, step=100000.0)
    prazo = st.number_input("Prazo do projeto (meses)", min_value=1, max_value=240, value=60)
    valor_terreno = st.number_input("Valor do terreno (R$, opcional)", min_value=0.0, value=0.0, step=100000.0)

    st.header("Dados do Consórcio")
    valor_cota = st.number_input("Valor da cota (R$)", min_value=0.0, max_value=valor_total, value=valor_total, step=100000.0)
    num_cotas = st.number_input("Número de cotas", min_value=1, value=1)
    taxa_admin = st.number_input("Taxa de administração anual (%)", min_value=0.0, max_value=20.0, value=1.2, step=0.1)
    percentual_lance = st.number_input("Percentual de lance (%)", min_value=0.0, max_value=100.0, value=20.0, step=1.0)

    st.header("Simulação de Dropdown")
    mes_dropdown = st.number_input("Mês do dropdown", min_value=1, max_value=prazo, value=24)
    percentual_dropdown = st.number_input("Percentual do dropdown (%)", min_value=0.0, max_value=100.0, value=30.0, step=1.0)

    if st.button("Calcular"):
        # Cálculos
        relacao_parcela_credito = calcular_relacao_parcela_credito(valor_cota, taxa_admin, prazo)
        
        taxa_constructa = taxa_admin  # Simplificação para esta versão
        taxa_tradicional = 12.0  # Taxa fixa para comparação
        economia = calcular_economia(valor_total, taxa_tradicional, taxa_constructa, prazo)
        
        lance = valor_total * (percentual_lance / 100)
        credito_novo = valor_total - lance
        
        fluxo_caixa_sem_dropdown = calcular_fluxo_caixa(valor_total, prazo, percentual_lance, taxa_admin)
        fluxo_caixa_com_dropdown = simular_dropdown(valor_total, prazo, percentual_lance, taxa_admin, mes_dropdown, percentual_dropdown)

        # Exibição dos resultados
        st.header("Resultados")
        st.write(f"Relação parcela/crédito novo: {relacao_parcela_credito:.2f}%")
        st.write(f"Economia estimada: R$ {economia:,.2f}")
        st.write(f"Valor do lance: R$ {lance:,.2f}")
        st.write(f"Crédito novo: R$ {credito_novo:,.2f}")

        # Gráficos
        fig_sem_dropdown = plot_fluxo_caixa(fluxo_caixa_sem_dropdown, "Fluxo de Caixa sem Dropdown")
        st.pyplot(fig_sem_dropdown)

        fig_com_dropdown = plot_fluxo_caixa(fluxo_caixa_com_dropdown, "Fluxo de Caixa com Dropdown")
        st.pyplot(fig_com_dropdown)

        # Tabela de fluxo de caixa
        df = pd.DataFrame({
            'Mês': range(len(fluxo_caixa_sem_dropdown)),
            'Fluxo sem Dropdown': fluxo_caixa_sem_dropdown,
            'Fluxo com Dropdown': fluxo_caixa_com_dropdown
        })
        st.write(df)

if __name__ == "__main__":
    main()
