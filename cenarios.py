import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Configuração da página
st.set_page_config(page_title="Comparativo de Cenários de Incorporação", layout="wide")

# Título
st.title("Comparativo de Cenários de Incorporação Imobiliária")

# Dados dos cenários
cenarios = {
    "Auto Financiado": {"Lucro": 10.5, "Margem": 30.00, "Capital Inicial": 5.25},
    "Financiamento Tradicional": {"Lucro": 5.23, "Margem": 14.94, "Capital Inicial": 14.7},
    "Constructa": {"Lucro": 21.03, "Margem": 60.09, "Capital Inicial": 6.125}
}

# Matriz de risco atualizada
fatores_risco = {
    "Mercado": {"Auto Financiado": 3, "Financiamento Tradicional": 3, "Constructa": 2},
    "Liquidez": {"Auto Financiado": 4, "Financiamento Tradicional": 3, "Constructa": 2},
    "Crédito": {"Auto Financiado": 4, "Financiamento Tradicional": 3, "Constructa": 2},
    "Taxa de Juros": {"Auto Financiado": 1, "Financiamento Tradicional": 5, "Constructa": 2},
    "Operacional": {"Auto Financiado": 3, "Financiamento Tradicional": 3, "Constructa": 3},
    "Financiamento": {"Auto Financiado": 2, "Financiamento Tradicional": 4, "Constructa": 3},
    "Execução": {"Auto Financiado": 2, "Financiamento Tradicional": 3, "Constructa": 2},
    "Regulatório": {"Auto Financiado": 2, "Financiamento Tradicional": 2, "Constructa": 2}
}

# Cálculo do risco total
risco_total = {cenario: sum(fatores_risco[fator][cenario] for fator in fatores_risco) / len(fatores_risco) 
               for cenario in cenarios.keys()}

# Adicionar risco total ao dicionário de cenários
for cenario, risco in risco_total.items():
    cenarios[cenario]["Risco Total"] = risco

# Criar DataFrame
df = pd.DataFrame(cenarios).T.reset_index()
df.columns = ["Cenário", "Lucro", "Margem", "Capital Inicial", "Risco Total"]

# Gráfico de barras para Lucro e Margem
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

sns.barplot(x="Cenário", y="Lucro", data=df, ax=ax1, palette="viridis")
ax1.set_title("Lucro por Cenário (em milhões R$)")
ax1.set_ylabel("Lucro (milhões R$)")

sns.barplot(x="Cenário", y="Margem", data=df, ax=ax2, palette="viridis")
ax2.set_title("Margem por Cenário (%)")
ax2.set_ylabel("Margem (%)")

plt.tight_layout()
st.pyplot(fig)

# Gráfico de dispersão para Capital Inicial vs Risco Total
fig, ax = plt.subplots(figsize=(10, 6))
sns.scatterplot(x="Capital Inicial", y="Risco Total", hue="Cenário", size="Lucro", 
                sizes=(100, 1000), data=df, ax=ax, palette="viridis")
ax.set_title("Capital Inicial vs Risco Total")
ax.set_xlabel("Capital Inicial (milhões R$)")
ax.set_ylabel("Risco Total")
plt.tight_layout()
st.pyplot(fig)

# Tabela comparativa
st.subheader("Tabela Comparativa")
st.table(df.set_index("Cenário"))

# Matriz de risco detalhada
st.subheader("Matriz de Risco Detalhada")
risco_df = pd.DataFrame(fatores_risco)
st.table(risco_df)

# Gráfico de radar para comparação dos riscos
st.subheader("Comparação de Riscos por Cenário")
fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))

angles = [n / float(len(fatores_risco)) * 2 * 3.141593 for n in range(len(fatores_risco))]
angles += angles[:1]

for cenario in cenarios.keys():
    valores = [fatores_risco[fator][cenario] for fator in fatores_risco]
    valores += valores[:1]
    ax.plot(angles, valores, linewidth=1, linestyle='solid', label=cenario)
    ax.fill(angles, valores, alpha=0.1)

ax.set_xticks(angles[:-1])
ax.set_xticklabels(fatores_risco.keys())
ax.set_ylim(0, 5)
plt.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))

st.pyplot(fig)

# Análise detalhada
st.subheader("Análise Detalhada")
st.write("""
Após a atualização da matriz de risco, o cenário Constructa se destaca ainda mais:

1. Lucro e Margem: O Constructa mantém a liderança significativa em termos de lucro e margem.
2. Capital Inicial: Requer um investimento inicial moderado, menor que o Financiamento Tradicional.
3. Risco Total: Apresenta o menor risco total entre os três cenários, refletindo uma melhor gestão de riscos em várias dimensões.
4. Destaques de Risco:
   - Menor exposição a riscos de mercado, liquidez e crédito.
   - Risco de taxa de juros significativamente menor que o Financiamento Tradicional.
   - Risco de execução comparável ao Auto Financiado, graças ao suporte das administradoras de consórcio.
   - Risco regulatório equalizado, refletindo a evolução positiva do setor de consórcios.

O Constructa oferece um equilíbrio atrativo entre alto retorno potencial e gestão eficiente de riscos, posicionando-se como uma opção valiosa para incorporadoras que buscam otimizar seus projetos imobiliários.
""")
