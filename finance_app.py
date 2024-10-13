import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from decimal import Decimal, ROUND_HALF_UP
import base64
import io

VERSION = "1.1.0"

def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def calcular_consorcio(valor_credito, valor_lance, valor_parcela, prazo, percentual_agio, tlr_anual, ir, percentual_tempo_investido):
    try:
        valor_credito = Decimal(valor_credito)
        valor_lance = Decimal(valor_lance)
        valor_parcela = Decimal(valor_parcela)
        prazo = Decimal(prazo)
        percentual_agio = Decimal(percentual_agio) / Decimal(100)
        tlr_anual = Decimal(tlr_anual) / Decimal(100)
        ir = Decimal(ir) / Decimal(100)
        percentual_tempo_investido = Decimal(percentual_tempo_investido) / Decimal(100)

        if valor_lance >= valor_credito:
            raise ValueError("O valor do lance deve ser menor que o valor do crédito.")

        total_pago = valor_parcela * prazo
        saldo_devedor = valor_credito - (valor_parcela * prazo)
        valor_agio = saldo_devedor * percentual_agio
        credito_novo = valor_credito - valor_lance

        tlr_mensal = (1 + tlr_anual) ** (Decimal(1) / Decimal(12)) - 1
        tempo_investido = prazo * percentual_tempo_investido
        ganho_investimento = credito_novo * ((1 + tlr_mensal) ** tempo_investido - 1) * (1 - ir)

        custo_consorcio = total_pago - valor_credito
        resultado_liquido = ganho_investimento + valor_agio - custo_consorcio

        investimento_tlr = valor_lance * ((1 + tlr_anual) ** (prazo / Decimal(12)) - 1) * (1 - ir)

        relacao_parcela_credito = (valor_parcela / credito_novo) * 100
        retorno_necessario = (investimento_tlr - resultado_liquido) / credito_novo * 100

        return {
            "total_pago": total_pago,
            "saldo_devedor": saldo_devedor,
            "valor_agio": valor_agio,
            "credito_novo": credito_novo,
            "ganho_investimento": ganho_investimento,
            "resultado_liquido": resultado_liquido,
            "investimento_tlr": investimento_tlr,
            "relacao_parcela_credito": relacao_parcela_credito,
            "retorno_necessario": retorno_necessario
        }
    except ZeroDivisionError:
        st.error("Erro: Divisão por zero. Verifique os valores inseridos.")
    except ValueError as e:
        st.error(f"Erro: {str(e)}")
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado: {str(e)}")

def gerar_recomendacoes(resultado):
    recomendacoes = []
    if resultado['resultado_liquido'] > resultado['investimento_tlr']:
        recomendacoes.append("O consórcio parece ser mais vantajoso que o investimento na TLR.")
    else:
        recomendacoes.append("O investimento na TLR parece ser mais vantajoso que o consórcio.")

    if resultado['relacao_parcela_credito'] > 2:
        recomendacoes.append("A relação parcela/crédito novo está alta. Considere reduzir o valor da parcela.")

    if resultado['retorno_necessario'] > 10:
        recomendacoes.append("O retorno necessário para igualar a TLR é significativo. Avalie cuidadosamente os riscos.")

    return recomendacoes

def exportar_csv(resultado):
    df = pd.DataFrame([resultado])
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="resultado_financex_prime.csv">Download CSV</a>'
    return href

def plot_comparativo(resultado):
    labels = ['Consórcio', 'Investimento TLR']
    valores = [float(resultado['resultado_liquido']), float(resultado['investimento_tlr'])]
    
    fig, ax = plt.subplots()
    ax.bar(labels, valores)
    ax.set_ylabel('Valor (R$)')
    ax.set_title('Comparativo: Consórcio vs. Investimento TLR')
    
    for i, v in enumerate(valores):
        ax.text(i, v, f'{v:.2f}', ha='center', va='bottom')
    
    return fig

def main():
    st.title("FinanceX Prime - Análise de Consórcios")

    # Cenários predefinidos
    cenarios = {
        "Conservador": {"valor_credito": 80000, "valor_lance": 10000, "valor_parcela": 800, "prazo": 60, "percentual_agio": 5, "tlr_anual": 4, "ir": 15, "percentual_tempo_investido": 30},
        "Moderado": {"valor_credito": 100000, "valor_lance": 15000, "valor_parcela": 1000, "prazo": 72, "percentual_agio": 8, "tlr_anual": 5, "ir": 15, "percentual_tempo_investido": 50},
        "Agressivo": {"valor_credito": 150000, "valor_lance": 25000, "valor_parcela": 1500, "prazo": 84, "percentual_agio": 12, "tlr_anual": 6, "ir": 15, "percentual_tempo_investido": 70}
    }

    cenario_selecionado = st.sidebar.selectbox("Selecione um cenário", ["Personalizado"] + list(cenarios.keys()))

    if cenario_selecionado != "Personalizado":
        valores = cenarios[cenario_selecionado]
    else:
        valores = {
            "valor_credito": 100000.0,
            "valor_lance": 0.0,
            "valor_parcela": 1000.0,
            "prazo": 60,
            "percentual_agio": 10.0,
            "tlr_anual": 5.0,
            "ir": 15.0,
            "percentual_tempo_investido": 50.0
        }

    st.sidebar.header("Parâmetros de Entrada")
    valor_credito = st.sidebar.number_input("Valor total do crédito (R$)", min_value=1000.0, value=valores["valor_credito"], step=1000.0, help="Valor total do crédito do consórcio")
    valor_lance = st.sidebar.number_input("Valor do lance (R$)", min_value=0.0, value=valores["valor_lance"], step=1000.0, help="Valor do lance oferecido no consórcio")
    valor_parcela = st.sidebar.number_input("Valor da parcela mensal (R$)", min_value=10.0, value=valores["valor_parcela"], step=10.0, help="Valor da parcela mensal do consórcio")
    prazo = st.sidebar.slider("Prazo total em meses", min_value=12, max_value=240, value=valores["prazo"], step=12, help="Prazo total do consórcio em meses")
    percentual_agio = st.sidebar.number_input("Percentual de ágio na venda da carta (%)", min_value=0.0, max_value=100.0, value=valores["percentual_agio"], step=0.1, help="Percentual de ágio na venda da carta de crédito")
    tlr_anual = st.sidebar.number_input("Taxa Livre de Risco (TLR) anual líquida (%)", min_value=0.1, max_value=20.0, value=valores["tlr_anual"], step=0.1, help="Taxa Livre de Risco anual líquida para comparação")
    ir = st.sidebar.number_input("Imposto de Renda sobre investimentos (%)", min_value=0.0, max_value=100.0, value=valores["ir"], step=0.1, help="Percentual de Imposto de Renda sobre os investimentos")
    percentual_tempo_investido = st.sidebar.number_input("Percentual do tempo com crédito investido na TLR (%)", min_value=0.0, max_value=100.0, value=valores["percentual_tempo_investido"], step=1.0, help="Percentual do tempo em que o crédito ficará investido na TLR")

    if st.sidebar.button("Limpar"):
        st.experimental_rerun()

    if st.sidebar.button("Calcular"):
        resultado = calcular_consorcio(valor_credito, valor_lance, valor_parcela, prazo, percentual_agio, tlr_anual, ir, percentual_tempo_investido)
        
        if resultado:
            st.subheader("Resultados da Análise")
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"Total pago em parcelas: {formatar_moeda(resultado['total_pago'])}")
                st.write(f"Saldo devedor ao final: {formatar_moeda(resultado['saldo_devedor'])}")
                st.write(f"Valor do ágio na venda: {formatar_moeda(resultado['valor_agio'])}")
                st.write(f"Crédito novo: {formatar_moeda(resultado['credito_novo'])}")
            with col2:
                st.write(f"Ganho com investimento parcial: {formatar_moeda(resultado['ganho_investimento'])}")
                st.write(f"Resultado líquido: {formatar_moeda(resultado['resultado_liquido'])}")
                st.write(f"Investimento na TLR: {formatar_moeda(resultado['investimento_tlr'])}")
                st.write(f"Relação parcela/crédito novo: {resultado['relacao_parcela_credito']:.2f}%")
                st.write(f"Retorno necessário para igualar TLR: {resultado['retorno_necessario']:.2f}%")

            st.subheader("Análise Detalhada")
            st.write("O resultado líquido representa o ganho total considerando o ágio na venda da carta, o ganho com investimento parcial e o custo do consórcio.")
            st.write("A relação parcela/crédito novo indica o percentual que a parcela representa do crédito disponível após o lance.")
            st.write("O retorno necessário para igualar a TLR é o percentual que o consórcio precisa render para ter o mesmo resultado que o investimento na Taxa Livre de Risco.")

            st.subheader("Gráfico Comparativo")
            fig = plot_comparativo(resultado)
            st.pyplot(fig)

            recomendacoes = gerar_recomendacoes(resultado)
            st.subheader("Recomendações")
            for rec in recomendacoes:
                st.write(f"- {rec}")

            st.subheader("Exportar Resultados")
            st.markdown(exportar_csv(resultado), unsafe_allow_html=True)

    st.sidebar.info(f"Versão: {VERSION}")

if __name__ == "__main__":
    main()
