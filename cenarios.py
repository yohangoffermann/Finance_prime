import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def main():
    st.set_page_config(page_title="Comparativo de Cenários de Incorporação", layout="wide")
    st.title("Comparativo de Cenários de Incorporação Imobiliária")

    params = get_user_inputs()
    results = calculate_scenarios(params)
    display_results(results, params)

def get_user_inputs():
    st.sidebar.header("Parâmetros Econômicos")
    params = {
        'vgv': st.sidebar.number_input("VGV (milhões R$)", value=35.0, step=0.1),
        'custo_construcao_percentual': st.sidebar.slider("Custo de Construção (% do VGV)", 50, 90, 70),
        'prazo_meses': st.sidebar.number_input("Prazo de Construção (meses)", value=48, step=1),
        'taxa_selic': st.sidebar.number_input("Taxa Selic (% a.a.)", value=11.0, step=0.1),
        'incc': st.sidebar.number_input("INCC (% a.a.)", value=6.0, step=0.1),
        'taxa_financiamento': st.sidebar.number_input("Taxa de Financiamento Tradicional (% a.a.)", value=12.0, step=0.1),
        'percentual_financiado': st.sidebar.slider("Percentual Financiado (Financiamento Tradicional)", 20, 80, 40),
        'lance_consorcio': st.sidebar.slider("Lance do Consórcio (%)", 20, 40, 25),
        'fluxo_caixa': st.sidebar.selectbox("Perfil do Fluxo de Caixa da Obra", ["Linear", "Front Loaded", "Back Loaded"]),
        'entrada_percentual': st.sidebar.slider("Entrada (%)", 0, 50, 20),
        'balao_percentual': st.sidebar.slider("Balões (%)", 0, 50, 20),
        'num_baloes': st.sidebar.number_input("Número de Balões", 0, 5, 2, step=1),
        'num_parcelas': st.sidebar.slider("Número de Parcelas do Saldo Devedor", 24, 180, 120),
        'taxa_correcao_parcelas': st.sidebar.number_input("Taxa de Correção das Parcelas (% a.a.)", value=6.0, step=0.1),
        'modelo_pagamento_constructa': st.sidebar.radio("Modelo de Pagamento Constructa", 
                                                        ("Tradicional", "Pagamento na Transferência do Consórcio"))
    }
    params['parcelas_percentual'] = 100 - params['entrada_percentual'] - params['balao_percentual']
    st.sidebar.write(f"Parcelas Mensais: {params['parcelas_percentual']}%")
    return params

def calculate_scenarios(params):
    custo_construcao = params['vgv'] * (params['custo_construcao_percentual'] / 100)
    lucro_operacional = params['vgv'] - custo_construcao

    # Cálculo do valor pago pelo cliente até o final da obra
    entrada = params['vgv'] * (params['entrada_percentual'] / 100)
    baloes = params['vgv'] * (params['balao_percentual'] / 100)
    
    saldo_devedor = params['vgv'] * (params['parcelas_percentual'] / 100)
    taxa_mensal = (1 + params['taxa_correcao_parcelas']/100)**(1/12) - 1
    valor_parcela = saldo_devedor * (taxa_mensal * (1 + taxa_mensal)**params['num_parcelas']) / ((1 + taxa_mensal)**params['num_parcelas'] - 1)
    
    parcelas_durante_obra = valor_parcela * min(params['prazo_meses'], params['num_parcelas'])
    valor_pago_cliente = entrada + baloes + parcelas_durante_obra

    # Cenário Auto Financiado
    lucro_auto = lucro_operacional

    # Cenário Financiamento Tradicional
    valor_financiado = custo_construcao * (params['percentual_financiado'] / 100)
    juros_financiamento = valor_financiado * ((1 + params['taxa_financiamento']/100)**(params['prazo_meses']/12) - 1)
    lucro_financiamento = lucro_operacional - juros_financiamento

    # Cenário Constructa
    lance = custo_construcao * (params['lance_consorcio'] / 100)
    rendimento_selic = lance * ((1 + params['taxa_selic']/100)**(params['prazo_meses']/12) - 1)
    custo_consorcio = custo_construcao * ((1 + params['incc']/100)**(params['prazo_meses']/12) - 1)
    
    saldo_devedor_consorcio = custo_construcao * (1 + params['incc']/100)**(params['prazo_meses']/12)

    if params['modelo_pagamento_constructa'] == "Tradicional":
        valor_faltante = params['vgv'] - valor_pago_cliente
        saldo_assumido_cliente = min(valor_faltante, saldo_devedor_consorcio)
        agio = max(0, valor_faltante - saldo_assumido_cliente)
        lucro_constructa = (valor_pago_cliente + agio + saldo_assumido_cliente - custo_construcao) + rendimento_selic - custo_consorcio
    else:
        saldo_assumido_cliente = saldo_devedor_consorcio
        agio = max(0, params['vgv'] - saldo_assumido_cliente)
        lucro_constructa = (agio + saldo_assumido_cliente - custo_construcao) + rendimento_selic - custo_consorcio

    percentual_agio = (agio / custo_construcao) * 100

    return {
        "Auto Financiado": {"Lucro": lucro_auto, "Margem": (lucro_auto/params['vgv'])*100, "Capital Inicial": custo_construcao - valor_pago_cliente},
        "Financiamento Tradicional": {"Lucro": lucro_financiamento, "Margem": (lucro_financiamento/params['vgv'])*100, "Capital Inicial": custo_construcao - valor_financiado},
        "Constructa": {"Lucro": lucro_constructa, "Margem": (lucro_constructa/params['vgv'])*100, "Capital Inicial": lance},
        "Detalhes Constructa": {
            "Valor Pago Cliente até o fim da obra": valor_pago_cliente,
            "Saldo Devedor Consórcio": saldo_devedor_consorcio,
            "Saldo Assumido Cliente": saldo_assumido_cliente,
            "Ágio": agio,
            "Percentual Ágio": percentual_agio,
            "Rendimento Selic": rendimento_selic,
            "Custo Consórcio": custo_consorcio
        }
    }

def display_results(results, params):
    df = pd.DataFrame({k: v for k, v in results.items() if k != "Detalhes Constructa"}).T
    df = df.reset_index()
    df.columns = ["Cenário", "Lucro", "Margem", "Capital Inicial"]

    # Visualizações
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    sns.barplot(x="Cenário", y="Lucro", data=df, ax=ax1, palette="viridis")
    ax1.set_title("Lucro por Cenário (em milhões R$)")
    ax1.set_ylabel("Lucro (milhões R$)")
    sns.barplot(x="Cenário", y="Margem", data=df, ax=ax2, palette="viridis")
    ax2.set_title("Margem por Cenário (%)")
    ax2.set_ylabel("Margem (%)")
    plt.tight_layout()
    st.pyplot(fig)

    # Tabela comparativa
    st.subheader("Tabela Comparativa")
    st.table(df.set_index("Cenário").round(2))

    # Detalhes do Constructa
    st.subheader("Detalhes do Cenário Constructa")
    detalhes = results["Detalhes Constructa"]
    for key, value in detalhes.items():
        if key == "Percentual Ágio":
            st.write(f"{key}: {value:.2f}%")
        else:
            st.write(f"{key}: R$ {value:.2f} milhões")

    # Análise detalhada
    st.subheader("Análise Detalhada")
    write_analysis(results, params)

def write_analysis(results, params):
    auto = results["Auto Financiado"]
    financiamento = results["Financiamento Tradicional"]
    constructa = results["Constructa"]
    detalhes = results["Detalhes Constructa"]
    
    st.write(f"""
    Com base nos parâmetros fornecidos:

    1. O cenário Auto Financiado resulta em um lucro de R$ {auto['Lucro']:.2f} milhões, com uma margem de {auto['Margem']:.2f}%.

    2. O Financiamento Tradicional resulta em um lucro de R$ {financiamento['Lucro']:.2f} milhões, com uma margem de {financiamento['Margem']:.2f}%.

    3. O modelo Constructa resulta em um lucro de R$ {constructa['Lucro']:.2f} milhões, com uma margem de {constructa['Margem']:.2f}%.

    Detalhes do Constructa:
    - Valor pago pelo cliente até o fim da obra: R$ {detalhes['Valor Pago Cliente até o fim da obra']:.2f} milhões
    - Saldo devedor do consórcio: R$ {detalhes['Saldo Devedor Consórcio']:.2f} milhões
    - Ágio: R$ {detalhes['Ágio']:.2f} milhões ({detalhes['Percentual Ágio']:.2f}% do custo de construção)
    - Rendimento Selic: R$ {detalhes['Rendimento Selic']:.2f} milhões
    - Custo do Consórcio: R$ {detalhes['Custo Consórcio']:.2f} milhões

    O modelo de pagamento escolhido para o Constructa foi "{params['modelo_pagamento_constructa']}".
    
    Comparação:
    - O Constructa apresenta uma margem {constructa['Margem'] - financiamento['Margem']:.2f} pontos percentuais maior que o Financiamento Tradicional.
    - O Constructa requer um capital inicial R$ {financiamento['Capital Inicial'] - constructa['Capital Inicial']:.2f} milhões menor que o Financiamento Tradicional.
    - Em relação ao Auto Financiado, o Constructa tem uma margem {constructa['Margem'] - auto['Margem']:.2f} pontos percentuais {
        'maior' if constructa['Margem'] > auto['Margem'] else 'menor'
    }, e requer R$ {abs(constructa['Capital Inicial'] - auto['Capital Inicial']):.2f} milhões {
        'a mais' if constructa['Capital Inicial'] > auto['Capital Inicial'] else 'a menos'
    } de capital inicial.

    A escolha entre os modelos deve considerar não apenas o retorno financeiro, 
    mas também o perfil de risco da incorporadora, as condições específicas do mercado e a capacidade de gestão do fluxo de caixa ao longo do projeto.

    Pontos-chave do modelo Constructa:
    1. {'Menor' if constructa['Capital Inicial'] < financiamento['Capital Inicial'] else 'Maior'} necessidade de capital inicial comparado ao Financiamento Tradicional.
    2. Potencial de ganho adicional através do ágio e rendimento Selic.
    3. Maior flexibilidade na estruturação financeira do projeto.
    4. Possibilidade de oferecer condições diferenciadas aos compradores.

    O modelo escolhido deve estar alinhado com a estratégia global da incorporadora e as condições específicas de cada projeto.
    """)

if __name__ == "__main__":
    main()
