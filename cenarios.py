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
    "Auto Financiado": {"Lucro": 10.5, "Margem": 30.00, "Capital Inicial": 5.25, "Risco": 2},
    "Financiamento Tradicional": {"Lucro": 5.23, "Margem": 14.94, "Capital Inicial": 14.7, "Risco": 4},
    "Constructa": {"Lucro": 21.03, "Margem": 60.09, "Capital Inicial": 6.125, "Risco": 3}
}

# Criando DataFrame
df = pd.DataFrame(cenarios).T
df = df.reset_index().rename(columns={"index": "Cenário"})

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

# Gráfico de dispersão para Capital Inicial vs Risco
fig, ax = plt.subplots(figsize=(10, 6))
sns.scatterplot(x="Capital Inicial", y="Risco", hue="Cenário", size="Lucro", 
                sizes=(100, 1000), data=df, ax=ax, palette="viridis")
ax.set_title("Capital Inicial vs Risco")
ax.set_xlabel("Capital Inicial (milhões R$)")
ax.set_ylabel("Risco (1-5)")
plt.tight_layout()
st.pyplot(fig)

# Tabela comparativa
st.subheader("Tabela Comparativa")
st.table(df.set_index("Cenário"))

# Análise detalhada
st.subheader("Análise Detalhada")
st.write("""
O cenário Constructa apresenta o maior lucro e margem, com um capital inicial moderado e um nível de risco intermediário. 
O cenário Auto Financiado oferece um bom equilíbrio entre lucro, baixo risco e baixa necessidade de capital inicial. 
O Financiamento Tradicional, embora requeira mais capital inicial, resulta no menor lucro e na menor margem, além de apresentar o maior risco.
""")

# Slider para ajuste de parâmetros (exemplo)
st.subheader("Simulação de Cenários")
agio_constructa = st.slider("Ágio Constructa (%)", 0, 100, 47)
taxa_juros_tradicional = st.slider("Taxa de Juros Financiamento Tradicional (% a.a.)", 5, 20, 12)

# Recalcular resultados com base nos sliders
lucro_constructa = 10.5 + (24.5 * agio_constructa / 100)
margem_constructa = (lucro_constructa / 35) * 100

juros_tradicional = 9.8 * ((1 + taxa_juros_tradicional/100)**4 - 1)
lucro_tradicional = 35 - (24.5 + juros_tradicional)
margem_tradicional = (lucro_tradicional / 35) * 100

st.write(f"Lucro Constructa Ajustado: R$ {lucro_constructa:.2f} milhões")
st.write(f"Margem Constructa Ajustada: {margem_constructa:.2f}%")
st.write(f"Lucro Financiamento Tradicional Ajustado: R$ {lucro_tradicional:.2f} milhões")
st.write(f"Margem Financiamento Tradicional Ajustada: {margem_tradicional:.2f}%")
