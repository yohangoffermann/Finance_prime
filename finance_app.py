import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from numpy import irr

VERSION = "1.3.0"

def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def calcular_consorcio(valor_credito, valor_lance, valor_parcela, prazo, percentual_agio, tlr_anual, ir, percentual_tempo_investido):
    try:
        valor_credito = float(valor_credito)
        valor_lance = float(valor_lance)
        valor_parcela = float(valor_parcela)
        prazo = int(prazo)
        percentual_agio = float(percentual_agio) / 100
        tlr_anual = float(tlr_anual) / 100
        ir = float(ir) / 100
        percentual_tempo_investido = float(percentual_tempo_investido) / 100

        if valor_lance >= valor_credito:
            raise ValueError("O valor do lance deve ser menor que o valor do crédito.")

        total_pago = valor_parcela * prazo
        saldo_devedor = max(0, valor_credito - (valor_parcela * prazo))
        valor_agio = saldo_devedor * percentual_agio
        credito_novo = valor_credito - valor_lance

        tlr_mensal = (1 + tlr_anual) ** (1 / 12) - 1
        tempo_investido = prazo * percentual_tempo_investido
        ganho_investimento = credito_novo * ((1 + tlr_mensal) ** tempo_investido - 1) * (1 - ir)

        custo_consorcio = total_pago - valor_credito
        resultado_liquido = valor_agio + ganho_investimento - custo_consorcio

        investimento_tlr = valor_lance * ((1 + tlr_anual) ** (prazo / 12) - 1) * (1 - ir)

        relacao_parcela_credito = (valor_parcela / credito_novo) * 100
        retorno_necessario = max(0, (investimento_tlr - resultado_liquido) / credito_novo * 100)

        fluxo_caixa = [-valor_lance] + [-valor_parcela] * (prazo - 1) + [valor_credito + valor_agio]
        tir = irr(fluxo_caixa)
        taxa_interna_retorno = max(0, (tir * 12 * 100))  # Convertendo para anual e percentual

        indice_lucratividade = (valor_agio + ganho_investimento) / total_pago

        return {
            "total_pago": total_pago,
            "saldo_devedor": saldo_devedor,
            "valor_agio": valor_agio,
            "credito_novo": credito_novo,
            "ganho_investimento": ganho_investimento,
            "custo_consorcio": custo_consorcio,
            "resultado_liquido": resultado_liquido,
            "investimento_tlr": investimento_tlr,
            "relacao_parcela_credito": relacao_parcela_credito,
            "retorno_necessario": retorno_necessario,
            "taxa_interna_retorno": taxa_interna_retorno,
            "indice_lucratividade": indice_lucratividade,
            "tlr_anual": tlr_anual * 100
        }
    except Exception as e:
        st.error(f"Ocorreu um erro: {str(e)}")
        return None

def sanity_checks(resultado):
    checks = []
    if resultado['saldo_devedor'] < 0:
        checks.append("Saldo devedor negativo")
    if resultado['custo_consorcio'] < 0:
        checks.append("Custo do consórcio negativo")
    if resultado['resultado_liquido'] > resultado['credito_novo'] * 2:
        checks.append("Resultado líquido excessivamente alto")
    if resultado['indice_lucratividade'] < 0 or resultado['indice_lucratividade'] > 3:
        checks.append("Índice de Lucratividade fora da faixa esperada")
    if resultado['taxa_interna_retorno'] < 0 or resultado['taxa_interna_retorno'] > 100:
        checks.append("Taxa Interna de Retorno fora da faixa esperada")
    return checks

def gerar_recomendacoes(resultado):
    recomendacoes = []
    if resultado['resultado_liquido'] > resultado['investimento_tlr']:
        recomendacoes.append(f"O consórcio é mais vantajoso que o investimento na TLR por {formatar_moeda(resultado['resultado_liquido'] - resultado['investimento_tlr'])}.")
    else:
        recomendacoes.append(f"O investimento na TLR é mais vantajoso que o consórcio por {formatar_moeda(resultado['investimento_tlr'] - resultado['resultado_liquido'])}.")

    if resultado['relacao_parcela_credito'] > 2:
        recomendacoes.append(f"A relação parcela/crédito novo de {resultado['relacao_parcela_credito']:.2f}% está alta. Considere reduzir o valor da parcela ou aumentar o lance.")

    if resultado['retorno_necessario'] > 10:
        recomendacoes.append(f"O retorno necessário de {resultado['retorno_necessario']:.2f}% para igualar a TLR é significativo. Avalie cuidadosamente os riscos e sua capacidade de obter este retorno.")

    if resultado['taxa_interna_retorno'] > resultado['tlr_anual']:
        recomendacoes.append(f"A taxa interna de retorno do consórcio ({resultado['taxa_interna_retorno']:.2f}%) é superior à TLR ({resultado['tlr_anual']:.2f}%), indicando uma boa oportunidade.")

    if resultado['indice_lucratividade'] > 1:
        recomendacoes.append(f"O índice de lucratividade de {resultado['indice_lucratividade']:.2f} indica que o consórcio é lucrativo.")
    else:
        recomendacoes.append(f"O índice de lucratividade de {resultado['indice_lucratividade']:.2f} indica que o consórcio não é lucrativo nas condições atuais.")

    return recomendacoes

def plot_comparativo(resultado):
    labels = ['Consórcio', 'Investimento TLR']
    valores = [resultado['resultado_liquido'], resultado['investimento_tlr']]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(labels, valores, color=['#1f77b4', '#ff7f0e'])
    ax.set_ylabel('Valor (R$)')
    ax.set_title('Comparativo: Consórcio vs. Investimento TLR')
    
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:,.2f}',
                ha='center', va='bottom')
    
    plt.tight_layout()
    return fig

def analise_sensibilidade(valor_credito, valor_lance, valor_parcela, prazo, percentual_agio, tlr_anual, ir, percentual_tempo_investido):
    resultados = {}
    params = {
        'valor_parcela': valor_parcela,
        'percentual_agio': percentual_agio,
        'tlr_anual': tlr_anual
    }
    
    for param, base_value in params.items():
        valores = [base_value * (1 + i * 0.1) for i in range(-2, 3)]
        resultados[param] = [
            calcular_consorcio(
                valor_credito, valor_lance,
                v if param == 'valor_parcela' else valor_parcela,
                prazo,
                v if param == 'percentual_agio' else percentual_agio,
                v if param == 'tlr_anual' else tlr_anual,
                ir, percentual_tempo_investido
            )['resultado_liquido']
            for v in valores
        ]
    
    return resultados

def plot_sensibilidade(analise):
    fig, ax = plt.subplots(figsize=(12, 7))
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
    
    for (param, valores), color in zip(analise.items(), colors):
        ax.plot(range(-2, 3), valores, label=param, color=color, marker='o')
    
    ax.set_xlabel('Variação (%)')
    ax.set_ylabel('Resultado Líquido (R$)')
    ax.set_title('Análise de Sensibilidade')
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    return fig

def main():
    st.set_page_config(page_title="FinanceX Prime", page_icon="", layout="wide")
    st.title("FinanceX Prime - Análise Avançada de Consórcios")

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
            sanity_results = sanity_checks(resultado)
            if sanity_results:
                st.warning("Atenção: Os seguintes problemas foram detectados nos cálculos:")
                for check in sanity_results:
                    st.write(f"- {check}")

            st.subheader("Resultados da Análise")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"Total pago em parcelas: {formatar_moeda(resultado['total_pago'])}")
                st.write(f"Saldo devedor ao final: {formatar_moeda(resultado['saldo_devedor'])}")
                st.write(f"Valor do ágio na venda: {formatar_moeda(resultado['valor_agio'])}")
            with col2:
                st.write(f"Crédito novo: {formatar_moeda(resultado['credito_novo'])}")
                st.write(f"Ganho com investimento: {formatar_moeda(resultado['ganho_investimento'])}")
                st.write(f"Custo do consórcio: {formatar_moeda(resultado['custo_consorcio'])}")
             with col3:
                st.write(f"Resultado líquido: {formatar_moeda(resultado['resultado_liquido'])}")
                st.write(f"Investimento na TLR: {formatar_moeda(resultado['investimento_tlr'])}")
                st.write(f"Taxa Interna de Retorno: {resultado['taxa_interna_retorno']:.2f}%")

            st.subheader("Métricas Adicionais")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"Relação parcela/crédito novo: {resultado['relacao_parcela_credito']:.2f}%")
                st.write(f"Retorno necessário para igualar TLR: {resultado['retorno_necessario']:.2f}%")
            with col2:
                st.write(f"Taxa Interna de Retorno: {resultado['taxa_interna_retorno']:.2f}%")
                st.write(f"Índice de Lucratividade: {resultado['indice_lucratividade']:.2f}")
            with col3:
                st.write(f"Ganho do Consórcio: {formatar_moeda(resultado['ganho_investimento'] + resultado['valor_agio'])}")
                st.write(f"Diferença para TLR: {formatar_moeda(resultado['resultado_liquido'] - resultado['investimento_tlr'])}")

            st.subheader("Análise Gráfica")
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Comparativo: Consórcio vs. Investimento TLR")
                fig_comparativo = plot_comparativo(resultado)
                st.pyplot(fig_comparativo)
            
            with col2:
                st.subheader("Análise de Sensibilidade")
                analise_sens = analise_sensibilidade(valor_credito, valor_lance, valor_parcela, prazo, percentual_agio, tlr_anual, ir, percentual_tempo_investido)
                fig_sensibilidade = plot_sensibilidade(analise_sens)
                st.pyplot(fig_sensibilidade)

            st.subheader("Recomendações")
            recomendacoes = gerar_recomendacoes(resultado)
            for rec in recomendacoes:
                st.write(f"- {rec}")

    st.sidebar.info(f"Versão: {VERSION}")
    st.sidebar.warning("Este é um modelo simplificado para fins educacionais. Consulte um profissional financeiro para decisões reais.")

if __name__ == "__main__":
    main()
