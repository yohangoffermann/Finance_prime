import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def main():
    st.set_page_config(page_title="Modelo Constructa Avançado", layout="wide")
    st.title("Modelo Constructa: Otimização de Ágio e Fluxo de Caixa")

    params = get_user_inputs()
    results = calculate_scenarios(params)
    display_results(results, params)

def get_user_inputs():
    st.sidebar.header("Parâmetros do Projeto")
    params = {
        'vgv': st.sidebar.number_input("VGV (milhões R$)", value=35.0, step=0.1),
        'custo_construcao_percentual': st.sidebar.slider("Custo de Construção (% do VGV)", 50, 90, 70),
        'prazo_meses': st.sidebar.number_input("Prazo de Construção (meses)", value=48, step=1),
        'taxa_selic': st.sidebar.number_input("Taxa Selic (% a.a.)", value=11.0, step=0.1),
        'incc': st.sidebar.number_input("INCC (% a.a.)", value=6.0, step=0.1),
        'lance_consorcio': st.sidebar.slider("Lance do Consórcio (%)", 20, 40, 25),
        'entrada_percentual': st.sidebar.slider("Entrada (%)", 0, 50, 20),
        'num_baloes': st.sidebar.number_input("Número de Balões", 1, 5, 3, step=1),
    }
    
    baloes = []
    total_baloes = 0
    for i in range(params['num_baloes']):
        balao = st.sidebar.slider(f"Balão {i+1} (%)", 0, 50-total_baloes, 10)
        baloes.append(balao)
        total_baloes += balao
    params['baloes'] = baloes

    params['parcelas_percentual'] = 100 - params['entrada_percentual'] - sum(baloes)
    st.sidebar.write(f"Parcelas Mensais: {params['parcelas_percentual']}%")

    return params

def calculate_scenarios(params):
    custo_construcao = params['vgv'] * (params['custo_construcao_percentual'] / 100)
    credito_consorcio = custo_construcao
    lance = credito_consorcio * (params['lance_consorcio'] / 100)

    fluxo_caixa = calcular_fluxo_caixa(params, custo_construcao, credito_consorcio, lance)
    oportunidades_agio = calcular_oportunidades_agio(params, fluxo_caixa, credito_consorcio)
    resultados = calcular_resultados_finais(params, fluxo_caixa, oportunidades_agio)

    return {
        "Fluxo de Caixa": fluxo_caixa,
        "Oportunidades de Ágio": oportunidades_agio,
        "Resultados Finais": resultados
    }

def calcular_fluxo_caixa(params, custo_construcao, credito_consorcio, lance):
    meses = params['prazo_meses']
    fluxo = pd.DataFrame(index=range(meses), columns=['Receitas', 'Custos', 'Saldo'])
    
    # Entrada
    fluxo.loc[0, 'Receitas'] = params['vgv'] * (params['entrada_percentual'] / 100)
    
    # Balões
    for i, balao in enumerate(params['baloes']):
        mes = int((i + 1) * meses / (len(params['baloes']) + 1))
        fluxo.loc[mes, 'Receitas'] += params['vgv'] * (balao / 100)
    
    # Parcelas
    valor_parcela = (params['vgv'] * (params['parcelas_percentual'] / 100)) / meses
    fluxo['Receitas'] = fluxo['Receitas'].fillna(valor_parcela)
    
    # Custos de construção (distribuição linear simplificada)
    fluxo['Custos'] = custo_construcao / meses
    
    # Saldo
    fluxo['Saldo'] = fluxo['Receitas'].cumsum() - fluxo['Custos'].cumsum()
    
    return fluxo

def calcular_oportunidades_agio(params, fluxo_caixa, credito_consorcio):
    oportunidades = []
    saldo_consorcio = credito_consorcio
    valor_parcela = (params['vgv'] * (params['parcelas_percentual'] / 100)) / params['prazo_meses']
    
    for mes, row in fluxo_caixa.iterrows():
        if row['Receitas'] > valor_parcela * 1.1 or mes == 0:  # Entrada, balão ou valor significativamente maior
            agio_potencial = min(saldo_consorcio, row['Receitas']) * 0.2  # 20% de ágio estimado
            oportunidades.append({
                'Mês': mes,
                'Valor Recebido': row['Receitas'],
                'Saldo Consórcio': saldo_consorcio,
                'Ágio Potencial': agio_potencial
            })
            saldo_consorcio -= min(saldo_consorcio, row['Receitas'])
    
    return pd.DataFrame(oportunidades)

def calcular_resultados_finais(params, fluxo_caixa, oportunidades_agio):
    vgv = params['vgv']
    custo_construcao = vgv * (params['custo_construcao_percentual'] / 100)
    
    receita_total = fluxo_caixa['Receitas'].sum()
    custo_total = fluxo_caixa['Custos'].sum()
    agio_total = oportunidades_agio['Ágio Potencial'].sum()
    
    lucro_operacional = vgv - custo_construcao
    lucro_total = lucro_operacional + agio_total
    
    return {
        'VGV': vgv,
        'Custo de Construção': custo_construcao,
        'Lucro Operacional': lucro_operacional,
        'Ágio Total': agio_total,
        'Lucro Total': lucro_total,
        'Margem Operacional': (lucro_operacional / vgv) * 100,
        'Margem Total': (lucro_total / vgv) * 100
    }

def display_results(results, params):
    st.header("Resultados da Análise")

    # Exibir gráfico de fluxo de caixa
    st.subheader("Fluxo de Caixa do Projeto")
    plot_fluxo_caixa(results["Fluxo de Caixa"])

    # Exibir oportunidades de ágio
    st.subheader("Oportunidades de Ágio")
    plot_oportunidades_agio(results["Oportunidades de Ágio"])

    # Exibir resultados finais
    st.subheader("Resultados Financeiros")
    display_resultados_finais(results["Resultados Finais"])

def plot_fluxo_caixa(fluxo_caixa):
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(fluxo_caixa.index, fluxo_caixa['Saldo'], label='Saldo Acumulado')
    ax.bar(fluxo_caixa.index, fluxo_caixa['Receitas'], alpha=0.3, label='Receitas')
    ax.bar(fluxo_caixa.index, -fluxo_caixa['Custos'], alpha=0.3, label='Custos')
    ax.set_xlabel('Meses')
    ax.set_ylabel('Valor (R$ milhões)')
    ax.legend()
    st.pyplot(fig)

def plot_oportunidades_agio(oportunidades_agio):
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(oportunidades_agio['Mês'], oportunidades_agio['Ágio Potencial'])
    ax.set_xlabel('Meses')
    ax.set_ylabel('Ágio Potencial (R$ milhões)')
    st.pyplot(fig)

def display_resultados_finais(resultados):
    st.table(pd.DataFrame([resultados]).T)

if __name__ == "__main__":
    main()
