import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from decimal import Decimal, ROUND_HALF_UP

VERSION = "1.0.1"

def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def calcular_consorcio(valor_credito, valor_lance, valor_parcela, prazo, percentual_agio, tlr_anual, ir, percentual_tempo_investido):
    valor_credito = Decimal(valor_credito)
    valor_lance = Decimal(valor_lance)
    valor_parcela = Decimal(valor_parcela)
    prazo = Decimal(prazo)
    percentual_agio = Decimal(percentual_agio) / Decimal(100)
    tlr_anual = Decimal(tlr_anual) / Decimal(100)
    ir = Decimal(ir) / Decimal(100)
    percentual_tempo_investido = Decimal(percentual_tempo_investido) / Decimal(100)

    total_pago = valor_parcela * prazo + valor_lance
    saldo_devedor = valor_credito - valor_lance - (valor_parcela * prazo)
    valor_agio = valor_credito * percentual_agio

    tlr_mensal = (1 + tlr_anual) ** (Decimal(1) / Decimal(12)) - 1
    tempo_investido = prazo * percentual_tempo_investido
    ganho_investimento = valor_credito * ((1 + tlr_mensal) ** tempo_investido - 1) * (1 - ir)

    resultado_liquido = ganho_investimento + valor_agio - (total_pago - valor_credito)

    investimento_tlr = valor_credito * ((1 + tlr_anual) ** (prazo / Decimal(12)) - 1) * (1 - ir)

    return {
        "total_pago": total_pago,
        "saldo_devedor": saldo_devedor,
        "valor_agio": valor_agio,
        "ganho_investimento": ganho_investimento,
        "resultado_liquido": resultado_liquido,
        "investimento_tlr": investimento_tlr
    }

def main():
    st.title("FinanceX Prime - Análise de Consórcios")

    st.sidebar.header("Parâmetros de Entrada")
    valor_credito = st.sidebar.number_input("Valor total do crédito (R$)", min_value=1000.0, value=100000.0, step=1000.0)
    valor_lance = st.sidebar.number_input("Valor do lance (R$)", min_value=0.0, value=0.0, step=1000.0)
    valor_parcela = st.sidebar.number_input("Valor da parcela mensal (R$)", min_value=10.0, value=1000.0, step=10.0)
    prazo = st.sidebar.slider("Prazo total em meses", min_value=12, max_value=240, value=60, step=12)
    percentual_agio = st.sidebar.number_input("Percentual de ágio na venda da carta (%)", min_value=0.0, max_value=100.0, value=10.0, step=0.1)
    tlr_anual = st.sidebar.number_input("Taxa Livre de Risco (TLR) anual líquida (%)", min_value=0.1, max_value=20.0, value=5.0, step=0.1)
    ir = st.sidebar.number_input("Imposto de Renda sobre investimentos (%)", min_value=0.0, max_value=100.0, value=15.0, step=0.1)
    percentual_tempo_investido = st.sidebar.number_input("Percentual do tempo com crédito investido na TLR (%)", min_value=0.0, max_value=100.0, value=50.0, step=1.0)

    if st.sidebar.button("Calcular"):
        resultado = calcular_consorcio(valor_credito, valor_lance, valor_parcela, prazo, percentual_agio, tlr_anual, ir, percentual_tempo_investido)
        
        st.subheader("Resultados da Análise")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"Total pago em parcelas: {formatar_moeda(resultado['total_pago'])}")
            st.write(f"Saldo devedor ao final: {formatar_moeda(resultado['saldo_devedor'])}")
            st.write(f"Valor do ágio na venda: {formatar_moeda(resultado['valor_agio'])}")
        with col2:
            st.write(f"Ganho com investimento parcial: {formatar_moeda(resultado['ganho_investimento'])}")
            st.write(f"Resultado líquido: {formatar_moeda(resultado['resultado_liquido'])}")
            st.write(f"Investimento na TLR: {formatar_moeda(resultado['investimento_tlr'])}")

        # Gráfico comparativo usando Matplotlib
        fig, ax = plt.subplots()
        opcoes = ['Consórcio', 'Investimento TLR']
        valores = [float(resultado['resultado_liquido']), float(resultado['investimento_tlr'])]
        ax.bar(opcoes, valores)
        ax.set_title("Comparativo: Consórcio vs. Investimento TLR")
        ax.set_xlabel("Opção")
        ax.set_ylabel("Valor (R$)")
        for i, v in enumerate(valores):
            ax.text(i, v, f'{v:.2f}', ha='center', va='bottom')
        st.pyplot(fig)

    st.sidebar.info(f"Versão: {VERSION}")

if __name__ == "__main__":
    main()
