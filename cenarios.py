import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def main():
    st.title("Comparativo de Cenários de Incorporação Imobiliária")

    # Inputs do usuário
    vgv = st.sidebar.number_input("VGV (milhões R$)", value=50.0, step=0.1)
    custo_obra_percentual = st.sidebar.slider("Custo da Obra (% do VGV)", 50, 90, 70)
    prazo_meses = st.sidebar.number_input("Prazo de Construção (meses)", value=48, step=1)
    taxa_selic = st.sidebar.number_input("Taxa Selic (% a.a.)", value=11.0, step=0.1)
    incc = st.sidebar.number_input("INCC (% a.a.)", value=6.0, step=0.1)
    taxa_financiamento = st.sidebar.number_input("Taxa de Financiamento (% a.a.)", value=12.0, step=0.1)
    percentual_financiado = st.sidebar.slider("Percentual Financiado", 20, 80, 60)
    lance_consorcio = st.sidebar.slider("Lance do Consórcio (%)", 20, 40, 30)
    agio_consorcio = st.sidebar.slider("Ágio do Consórcio na Venda (%)", 10, 50, 20)

    # Cálculos
    custo_obra = vgv * (custo_obra_percentual / 100)
    
    # Fluxo de vendas simplificado
    entrada = vgv * 0.2  # 20% de entrada
    vendas_mensais = (vgv * 0.8) / prazo_meses  # Resto distribuído igualmente

    # Cenário Auto Financiado
    fluxo_auto = calcular_fluxo_auto(vgv, custo_obra, prazo_meses, entrada, vendas_mensais)
    
    # Cenário Financiamento Tradicional
    fluxo_financiamento = calcular_fluxo_financiamento(vgv, custo_obra, prazo_meses, entrada, vendas_mensais, 
                                                       percentual_financiado, taxa_financiamento)
    
    # Cenário Constructa
    fluxo_constructa = calcular_fluxo_constructa(vgv, custo_obra, prazo_meses, entrada, vendas_mensais, 
                                                 lance_consorcio, agio_consorcio, taxa_selic, incc)

    # Exibir resultados
    exibir_graficos(fluxo_auto, fluxo_financiamento, fluxo_constructa)
    exibir_metricas(fluxo_auto, fluxo_financiamento, fluxo_constructa, vgv)

def calcular_fluxo_auto(vgv, custo_obra, prazo_meses, entrada, vendas_mensais):
    fluxo = pd.DataFrame(index=range(prazo_meses), columns=['Receitas', 'Custos', 'Saldo'])
    fluxo.loc[0, 'Receitas'] = entrada
    fluxo.loc[1:, 'Receitas'] = vendas_mensais
    fluxo['Custos'] = custo_obra / prazo_meses
    fluxo['Saldo'] = (fluxo['Receitas'] - fluxo['Custos']).cumsum()
    return fluxo

def calcular_fluxo_financiamento(vgv, custo_obra, prazo_meses, entrada, vendas_mensais, percentual_financiado, taxa_financiamento):
    fluxo = pd.DataFrame(index=range(prazo_meses), columns=['Receitas', 'Custos', 'Saldo'])
    fluxo.loc[0, 'Receitas'] = entrada
    fluxo.loc[1:, 'Receitas'] = vendas_mensais
    
    valor_financiado = custo_obra * (percentual_financiado / 100)
    juros_totais = valor_financiado * ((1 + taxa_financiamento/100)**(prazo_meses/12) - 1)
    
    fluxo['Custos'] = custo_obra / prazo_meses
    fluxo.loc[prazo_meses-1, 'Custos'] += valor_financiado + juros_totais
    
    fluxo.loc[0, 'Saldo'] = valor_financiado + entrada - fluxo.loc[0, 'Custos']
    for i in range(1, prazo_meses):
        fluxo.loc[i, 'Saldo'] = fluxo.loc[i-1, 'Saldo'] + fluxo.loc[i, 'Receitas'] - fluxo.loc[i, 'Custos']
    
    return fluxo

def calcular_fluxo_constructa(vgv, custo_obra, prazo_meses, entrada, vendas_mensais, lance_consorcio, agio_consorcio, taxa_selic, incc):
    fluxo = pd.DataFrame(index=range(prazo_meses), columns=['Receitas', 'Custos', 'Saldo'])
    
    lance = custo_obra * (lance_consorcio / 100)
    credito_contemplado = custo_obra - lance
    rendimento_selic = lance * ((1 + taxa_selic/100)**(prazo_meses/12) - 1)
    custo_consorcio = custo_obra * ((1 + incc/100)**(prazo_meses/12) - 1)
    
    fluxo.loc[0, 'Receitas'] = entrada + credito_contemplado
    fluxo.loc[1:, 'Receitas'] = vendas_mensais * (1 + agio_consorcio/100)
    fluxo.loc[prazo_meses-1, 'Receitas'] += rendimento_selic
    
    fluxo['Custos'] = (custo_obra + custo_consorcio) / prazo_meses
    
    fluxo.loc[0, 'Saldo'] = fluxo.loc[0, 'Receitas'] - lance - fluxo.loc[0, 'Custos']
    for i in range(1, prazo_meses):
        fluxo.loc[i, 'Saldo'] = fluxo.loc[i-1, 'Saldo'] + fluxo.loc[i, 'Receitas'] - fluxo.loc[i, 'Custos']
    
    return fluxo

def exibir_graficos(fluxo_auto, fluxo_financiamento, fluxo_constructa):
    st.subheader("Fluxo de Caixa ao Longo do Tempo")
    
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(fluxo_auto.index, fluxo_auto['Saldo'], label='Auto Financiado')
    ax.plot(fluxo_financiamento.index, fluxo_financiamento['Saldo'], label='Financiamento Tradicional')
    ax.plot(fluxo_constructa.index, fluxo_constructa['Saldo'], label='Constructa')
    ax.set_xlabel('Meses')
    ax.set_ylabel('Saldo (milhões R$)')
    ax.legend()
    st.pyplot(fig)

    st.subheader("Lucro Final por Cenário")
    
    lucros = {
        'Auto Financiado': fluxo_auto['Saldo'].iloc[-1],
        'Financiamento Tradicional': fluxo_financiamento['Saldo'].iloc[-1],
        'Constructa': fluxo_constructa['Saldo'].iloc[-1]
    }
    
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(lucros.keys(), lucros.values())
    ax.set_ylabel('Lucro (milhões R$)')
    for i, v in enumerate(lucros.values()):
        ax.text(i, v, f'{v:.2f}', ha='center', va='bottom')
    st.pyplot(fig)

def exibir_metricas(fluxo_auto, fluxo_financiamento, fluxo_constructa, vgv):
    st.subheader("Métricas Comparativas")
    
    metricas = {
        'Cenário': ['Auto Financiado', 'Financiamento Tradicional', 'Constructa'],
        'Lucro Final (milhões R$)': [
            fluxo_auto['Saldo'].iloc[-1],
            fluxo_financiamento['Saldo'].iloc[-1],
            fluxo_constructa['Saldo'].iloc[-1]
        ],
        'Margem (%)': [
            (fluxo_auto['Saldo'].iloc[-1] / vgv) * 100,
            (fluxo_financiamento['Saldo'].iloc[-1] / vgv) * 100,
            (fluxo_constructa['Saldo'].iloc[-1] / vgv) * 100
        ],
        'Capital Inicial (milhões R$)': [
            -fluxo_auto['Saldo'].min(),
            -fluxo_financiamento['Saldo'].min(),
            -fluxo_constructa['Saldo'].min()
        ],
        'Exposição Máxima (milhões R$)': [
            -fluxo_auto['Saldo'].min(),
            -fluxo_financiamento['Saldo'].min(),
            -fluxo_constructa['Saldo'].min()
        ]
    }
    
    df_metricas = pd.DataFrame(metricas).set_index('Cenário')
    st.table(df_metricas.round(2))

if __name__ == "__main__":
    main()
