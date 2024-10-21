import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def main():
    st.title("Comparativo de Cenários de Incorporação Imobiliária")

    # Inputs do usuário
    vgv = st.sidebar.number_input("VGV (milhões R$)", value=35.0, step=0.1)
    custo_obra_percentual = st.sidebar.slider("Custo da Obra (% do VGV)", 50, 90, 70)
    prazo_meses = st.sidebar.number_input("Prazo de Construção (meses)", value=48, step=1)
    taxa_selic = st.sidebar.number_input("Taxa Selic (% a.a.)", value=11.0, step=0.1)
    taxa_financiamento = st.sidebar.number_input("Taxa de Financiamento (% a.a.)", value=12.0, step=0.1)
    percentual_financiado = st.sidebar.slider("Percentual Financiado", 20, 80, 40)
    lance_consorcio = st.sidebar.slider("Lance do Consórcio (%)", 20, 40, 25)
    agio_consorcio = st.sidebar.slider("Ágio do Consórcio na Venda (%)", 20, 60, 40)

    # Cálculos
    custo_obra = vgv * (custo_obra_percentual / 100)
    lucro_operacional = vgv - custo_obra

    # Cenário Auto Financiado
    lucro_auto = lucro_operacional

    # Cenário Financiamento Tradicional
    valor_financiado = custo_obra * (percentual_financiado / 100)
    juros_financiamento = valor_financiado * ((1 + taxa_financiamento/100)**(prazo_meses/12) - 1)
    lucro_financiamento = lucro_operacional - juros_financiamento

    # Cenário Constructa
    lance = custo_obra * (lance_consorcio / 100)
    rendimento_selic = lance * ((1 + taxa_selic/100)**(prazo_meses/12) - 1)
    custo_consorcio = custo_obra * ((1 + taxa_selic/100)**(prazo_meses/12) - 1)
    agio = custo_obra * (agio_consorcio / 100)
    lucro_constructa = lucro_operacional + rendimento_selic + agio - custo_consorcio

    # Criando DataFrame com os resultados
    cenarios = {
        "Auto Financiado": {"Lucro": lucro_auto, "Margem": (lucro_auto/vgv)*100, "Capital Inicial": custo_obra},
        "Financiamento Tradicional": {"Lucro": lucro_financiamento, "Margem": (lucro_financiamento/vgv)*100, "Capital Inicial": custo_obra - valor_financiado},
        "Constructa": {"Lucro": lucro_constructa, "Margem": (lucro_constructa/vgv)*100, "Capital Inicial": lance}
    }

    df = pd.DataFrame(cenarios).T
    st.table(df.round(2))

    # Gráfico de barras comparativo
    fig, ax = plt.subplots(figsize=(10, 6))
    df['Lucro'].plot(kind='bar', ax=ax)
    ax.set_ylabel('Lucro (milhões R$)')
    ax.set_title('Comparativo de Lucro por Cenário')
    st.pyplot(fig)

    # Análise detalhada
    st.subheader("Análise Detalhada")
    st.write(f"""
    Com base nos parâmetros fornecidos:

    1. O cenário Auto Financiado resulta em um lucro de R$ {lucro_auto:.2f} milhões, com uma margem de {(lucro_auto/vgv)*100:.2f}%.

    2. O Financiamento Tradicional resulta em um lucro de R$ {lucro_financiamento:.2f} milhões, com uma margem de {(lucro_financiamento/vgv)*100:.2f}%.

    3. O modelo Constructa resulta em um lucro de R$ {lucro_constructa:.2f} milhões, com uma margem de {(lucro_constructa/vgv)*100:.2f}%.

    O modelo Constructa apresenta {
        "o maior" if lucro_constructa > max(lucro_auto, lucro_financiamento) else "um"
    } lucro e margem entre os cenários analisados. 

    É importante notar que o Constructa requer um capital inicial de R$ {lance:.2f} milhões, 
    que é {
        "menor" if lance < cenarios["Financiamento Tradicional"]["Capital Inicial"] else "maior"
    } que o requerido pelo Financiamento Tradicional (R$ {cenarios["Financiamento Tradicional"]["Capital Inicial"]:.2f} milhões) e {
        "menor" if lance < cenarios["Auto Financiado"]["Capital Inicial"] else "maior"
    } que o Auto Financiado (R$ {cenarios["Auto Financiado"]["Capital Inicial"]:.2f} milhões).

    A escolha entre os modelos deve considerar não apenas o retorno financeiro, 
    mas também o perfil de risco da incorporadora, as condições específicas do mercado e a capacidade de gestão do fluxo de caixa ao longo do projeto.
    """)

if __name__ == "__main__":
    main()
