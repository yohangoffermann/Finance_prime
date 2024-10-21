import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def main():
    st.title("Comparativo de Cenários de Incorporação")

    vgv = st.sidebar.number_input("VGV (milhões R$)", value=35.0, step=0.1)
    custo_obra_percentual = st.sidebar.slider("Custo da Obra (% do VGV)", 50, 90, 70)
    prazo_meses = 48  # Fixo em 48 meses
    entrada_percentual = st.sidebar.slider("Entrada (%)", 10, 30, 20)
    venda_mensal_percentual = st.sidebar.slider("Vendas Mensais (% do VGV)", 1, 10, 5)
    agio_percentual = st.sidebar.slider("Ágio Constructa (%)", 5, 30, 15)

    fluxo_padrao = calcular_fluxo_padrao(vgv, custo_obra_percentual, prazo_meses, entrada_percentual, venda_mensal_percentual)
    fluxo_constructa = calcular_fluxo_constructa(vgv, custo_obra_percentual, prazo_meses, entrada_percentual, venda_mensal_percentual, agio_percentual)

    exibir_resultados(fluxo_padrao, fluxo_constructa)

def calcular_fluxo_padrao(vgv, custo_obra_percentual, prazo_meses, entrada_percentual, venda_mensal_percentual):
    custo_obra = vgv * (custo_obra_percentual / 100)
    fluxo = pd.DataFrame(index=range(prazo_meses), columns=['Receitas', 'Custos', 'Saldo'])
    
    # Distribuição das receitas
    fluxo.loc[0, 'Receitas'] = vgv * (entrada_percentual / 100)  # Entrada
    vendas_mensais = vgv * (venda_mensal_percentual / 100)
    for mes in range(1, prazo_meses):
        fluxo.loc[mes, 'Receitas'] = vendas_mensais
    fluxo.loc[prazo_meses-1, 'Receitas'] += vgv - fluxo['Receitas'].sum()  # Restante na entrega

    # Distribuição linear dos custos
    fluxo['Custos'] = custo_obra / prazo_meses

    fluxo['Saldo'] = fluxo['Receitas'].cumsum() - fluxo['Custos'].cumsum()
    return fluxo

def calcular_fluxo_constructa(vgv, custo_obra_percentual, prazo_meses, entrada_percentual, venda_mensal_percentual, agio_percentual):
    custo_obra = vgv * (custo_obra_percentual / 100)
    fluxo = pd.DataFrame(index=range(prazo_meses), columns=['Receitas', 'Custos', 'Saldo'])
    
    # Recebimento do crédito do consórcio
    fluxo.loc[0, 'Receitas'] = custo_obra
    
    # Distribuição das receitas com ágio
    fluxo.loc[0, 'Receitas'] += vgv * (entrada_percentual / 100) * (1 + agio_percentual / 100)  # Entrada com ágio
    vendas_mensais = vgv * (venda_mensal_percentual / 100) * (1 + agio_percentual / 100)
    for mes in range(1, prazo_meses):
        fluxo.loc[mes, 'Receitas'] = vendas_mensais
    fluxo.loc[prazo_meses-1, 'Receitas'] += (vgv - fluxo['Receitas'].sum() + custo_obra) * (1 + agio_percentual / 100)  # Restante na entrega com ágio

    # Distribuição dos custos (incluindo pagamento do consórcio)
    fluxo['Custos'] = (custo_obra * 1.1) / prazo_meses  # 10% a mais para simular custos do consórcio

    fluxo['Saldo'] = fluxo['Receitas'].cumsum() - fluxo['Custos'].cumsum()
    return fluxo

def exibir_resultados(fluxo_padrao, fluxo_constructa):
    st.subheader("Comparação de Fluxos de Caixa")
    
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(fluxo_padrao.index, fluxo_padrao['Saldo'], label='Fluxo Padrão')
    ax.plot(fluxo_constructa.index, fluxo_constructa['Saldo'], label='Fluxo Constructa')
    ax.set_xlabel('Meses')
    ax.set_ylabel('Saldo Acumulado (R$ milhões)')
    ax.legend()
    st.pyplot(fig)

    st.subheader("Métricas Comparativas")
    vpl_padrao = fluxo_padrao['Saldo'].iloc[-1]
    vpl_constructa = fluxo_constructa['Saldo'].iloc[-1]
    exposicao_padrao = fluxo_padrao['Saldo'].min()
    exposicao_constructa = fluxo_constructa['Saldo'].min()

    st.write(f"VPL Padrão: R$ {vpl_padrao:.2f} milhões")
    st.write(f"VPL Constructa: R$ {vpl_constructa:.2f} milhões")
    st.write(f"Melhoria no VPL: R$ {vpl_constructa - vpl_padrao:.2f} milhões")
    st.write(f"Exposição Máxima Padrão: R$ {exposicao_padrao:.2f} milhões")
    st.write(f"Exposição Máxima Constructa: R$ {exposicao_constructa:.2f} milhões")
    st.write(f"Redução na Exposição: R$ {exposicao_padrao - exposicao_constructa:.2f} milhões")

if __name__ == "__main__":
    main()
