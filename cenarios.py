import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="Comparativo de Cenários de Incorporação", layout="wide")

st.title("Comparativo de Cenários de Incorporação Imobiliária")

# Inputs do usuário
st.sidebar.header("Parâmetros Econômicos")

vgv = st.sidebar.number_input("Valor Geral de Vendas (VGV) em milhões R$", value=35.0, step=0.1)
custo_construcao_percentual = st.sidebar.slider("Custo de Construção (% do VGV)", 50, 90, 70)
prazo_meses = st.sidebar.number_input("Prazo de Construção (meses)", value=48, step=1)
taxa_selic = st.sidebar.number_input("Taxa Selic (% a.a.)", value=11.0, step=0.1)
incc = st.sidebar.number_input("INCC (% a.a.)", value=6.0, step=0.1)
taxa_financiamento = st.sidebar.number_input("Taxa de Financiamento Tradicional (% a.a.)", value=12.0, step=0.1)
percentual_financiado = st.sidebar.slider("Percentual Financiado (Financiamento Tradicional)", 20, 80, 40)
lance_consorcio = st.sidebar.slider("Lance do Consórcio (%)", 20, 40, 25)
agio_consorcio = st.sidebar.slider("Ágio do Consórcio na Venda (%)", 20, 60, 47)

# Novos inputs para fluxo de caixa e estrutura de recebíveis
st.sidebar.header("Fluxo de Caixa e Recebíveis")

fluxo_caixa = st.sidebar.selectbox("Perfil do Fluxo de Caixa da Obra", 
                                   ["Linear", "Front Loaded", "Back Loaded"])

entrada_percentual = st.sidebar.slider("Entrada (%)", 0, 50, 20)
balao_percentual = st.sidebar.slider("Balões (%)", 0, 50, 20)
parcelas_percentual = 100 - entrada_percentual - balao_percentual

st.sidebar.write(f"Parcelas Mensais: {parcelas_percentual}%")

num_baloes = st.sidebar.number_input("Número de Balões", 0, 5, 2, step=1)

# Função para gerar o fluxo de caixa da obra
def gerar_fluxo_caixa(perfil, prazo):
    if perfil == "Linear":
        return np.ones(prazo) / prazo
    elif perfil == "Front Loaded":
        return np.array([2/prazo if i < prazo/2 else 1/(2*prazo) for i in range(prazo)])
    else:  # Back Loaded
        return np.array([1/(2*prazo) if i < prazo/2 else 2/prazo for i in range(prazo)])

# Função para gerar o fluxo de recebíveis
def gerar_recebíveis(prazo, entrada, balao, parcelas, num_baloes):
    fluxo = np.zeros(prazo)
    fluxo[0] = entrada
    balao_individual = balao / num_baloes
    balao_meses = np.linspace(0, prazo-1, num_baloes+2)[1:-1].astype(int)
    fluxo[balao_meses] += balao_individual
    parcela_mensal = parcelas / (prazo - 1)
    fluxo[1:] += parcela_mensal
    return fluxo

# Cálculos
custo_construcao = vgv * (custo_construcao_percentual / 100)
lucro_operacional = vgv - custo_construcao

fluxo_obra = gerar_fluxo_caixa(fluxo_caixa, prazo_meses)
fluxo_recebiveis = gerar_recebíveis(prazo_meses, entrada_percentual/100, balao_percentual/100, 
                                    parcelas_percentual/100, num_baloes)

# Cenário Auto Financiado
lucro_auto = lucro_operacional

# Cenário Financiamento Tradicional
valor_financiado = custo_construcao * (percentual_financiado / 100)
juros_financiamento = valor_financiado * ((1 + taxa_financiamento/100)**(prazo_meses/12) - 1)
lucro_financiamento = lucro_operacional - juros_financiamento

# Cenário Constructa
lance = custo_construcao * (lance_consorcio / 100)
rendimento_selic = lance * ((1 + taxa_selic/100)**(prazo_meses/12) - 1)
custo_consorcio = custo_construcao * ((1 + incc/100)**(prazo_meses/12) - 1) - custo_construcao
agio = custo_construcao * (agio_consorcio / 100)
lucro_constructa = lucro_operacional + rendimento_selic + agio - custo_consorcio

# Criando DataFrame com os resultados
cenarios = {
    "Auto Financiado": {"Lucro": lucro_auto, "Margem": (lucro_auto/vgv)*100, "Capital Inicial": 0},
    "Financiamento Tradicional": {"Lucro": lucro_financiamento, "Margem": (lucro_financiamento/vgv)*100, "Capital Inicial": custo_construcao - valor_financiado},
    "Constructa": {"Lucro": lucro_constructa, "Margem": (lucro_constructa/vgv)*100, "Capital Inicial": lance}
}

df = pd.DataFrame(cenarios).T.reset_index()
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

# Gráfico de fluxo de caixa (mantido para visualização)
st.subheader("Fluxo de Caixa Acumulado")
fig, ax = plt.subplots(figsize=(12, 6))
fluxo_caixa_auto = fluxo_recebiveis * vgv - fluxo_obra * custo_construcao
fluxo_caixa_financiamento = fluxo_caixa_auto.copy()
fluxo_caixa_financiamento[0] += valor_financiado
fluxo_caixa_financiamento[-1] -= (valor_financiado + juros_financiamento)
fluxo_caixa_constructa = fluxo_caixa_auto.copy()
fluxo_caixa_constructa[0] -= lance
fluxo_caixa_constructa += fluxo_obra * (custo_construcao / prazo_meses)
fluxo_caixa_constructa[-1] += agio + rendimento_selic - custo_consorcio
ax.plot(np.cumsum(fluxo_caixa_auto), label="Auto Financiado")
ax.plot(np.cumsum(fluxo_caixa_financiamento), label="Financiamento Tradicional")
ax.plot(np.cumsum(fluxo_caixa_constructa), label="Constructa")
ax.set_xlabel("Meses")
ax.set_ylabel("Fluxo de Caixa Acumulado (milhões R$)")
ax.legend()
st.pyplot(fig)

# Análise detalhada
st.subheader("Análise Detalhada")
st.write(f"""
Com base nos parâmetros fornecidos e considerando o fluxo de caixa {fluxo_caixa.lower()} da obra e a estrutura de recebíveis definida:

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

O fluxo de caixa {fluxo_caixa.lower()} da obra e a estrutura de recebíveis escolhida impactam o desempenho de cada modelo, 
como demonstrado no gráfico de fluxo de caixa acumulado.

A escolha entre os modelos deve considerar não apenas o retorno financeiro, 
mas também o perfil de risco da incorporadora, as condições específicas do mercado e a capacidade de gestão do fluxo de caixa ao longo do projeto.
""")
