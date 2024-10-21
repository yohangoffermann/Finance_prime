import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def main():
    st.set_page_config(page_title="Comparativo de Cenários de Incorporação", layout="wide")
    st.title("Comparativo de Cenários de Incorporação Imobiliária")

    # Inputs do usuário
    params = get_user_inputs()

    # Cálculos
    results = calculate_scenarios(params)

    # Visualizações
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
        'modelo_pagamento_constructa': st.sidebar.radio("Modelo de Pagamento Constructa", 
                                                        ("Tradicional", "Pagamento na Transferência do Consórcio"))
    }
    params['parcelas_percentual'] = 100 - params['entrada_percentual'] - params['balao_percentual']
    st.sidebar.write(f"Parcelas Mensais: {params['parcelas_percentual']}%")
    return params

def calculate_scenarios(params):
    custo_construcao = params['vgv'] * (params['custo_construcao_percentual'] / 100)
    lucro_operacional = params['vgv'] - custo_construcao

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
    
    valor_pago_cliente = (params['entrada_percentual'] + params['balao_percentual'] + params['parcelas_percentual']) * params['vgv'] / 100
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
        "Auto Financiado": {"Lucro": lucro_auto, "Margem": (lucro_auto/params['vgv'])*100, "Capital Inicial": 0},
        "Financiamento Tradicional": {"Lucro": lucro_financiamento, "Margem": (lucro_financiamento/params['vgv'])*100, "Capital Inicial": custo_construcao - valor_financiado},
        "Constructa": {"Lucro": lucro_constructa, "Margem": (lucro_constructa/params['vgv'])*100, "Capital Inicial": lance},
        "Detalhes Constructa": {
            "Valor Pago Cliente": valor_pago_cliente,
            "Saldo Devedor Consórcio": saldo_devedor_consorcio,
            "Saldo Assumido Cliente": saldo_assumido_cliente,
            "Ágio": agio,
            "Percentual Ágio": percentual_agio
        }
    }

def display_results(results, params):
    df = pd.DataFrame(results).T.reset_index()
    df = df[df.index != "Detalhes Constructa"]
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
        st.write(f"{key}: R$ {value:.2f} milhões")

    # Análise detalhada
    st.subheader("Análise Detalhada")
    write_analysis(results, params)

def write_analysis(results, params):
    auto = results["Auto Financiado"]
    financiamento = results["Financiamento Tradicional"]
    constructa = results["Constructa"]
    
    st.write(f"""
    Com base nos parâmetros fornecidos:

    1. O cenário Auto Financiado resulta em um lucro de R$ {auto['Lucro']:.2f} milhões, com uma margem de {auto['Margem']:.2f}%.

    2. O Financiamento Tradicional resulta em um lucro de R$ {financiamento['Lucro']:.2f} milhões, com uma margem de {financiamento['Margem']:.2f}%.

    3. O modelo Constructa resulta em um lucro de R$ {constructa['Lucro']:.2f} milhões, com uma margem de {constructa['Margem']:.2f}%.

    O modelo de pagamento escolhido para o Constructa foi "{params['modelo_pagamento_constructa']}".
    
    O modelo Constructa apresenta {
        "o maior" if constructa['Lucro'] > max(auto['Lucro'], financiamento['Lucro']) else "um"
    } lucro e margem entre os cenários analisados. 

    É importante notar que o Constructa requer um capital inicial de R$ {constructa['Capital Inicial']:.2f} milhões, 
    que é {
        "menor" if constructa['Capital Inicial'] < financiamento['Capital Inicial'] else "maior"
    } que o requerido pelo Financiamento Tradicional (R$ {financiamento['Capital Inicial']:.2f} milhões) e {
        "menor" if constructa['Capital Inicial'] < auto['Capital Inicial'] else "maior"
    } que o Auto Financiado (R$ {auto['Capital Inicial']:.2f} milhões).

    A escolha entre os modelos deve considerar não apenas o retorno financeiro, 
    mas também o perfil de risco da incorporadora, as condições específicas do mercado e a capacidade de gestão do fluxo de caixa ao longo do projeto.
    """)

if __name__ == "__main__":
    main()
