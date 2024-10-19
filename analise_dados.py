import pandas as pd
import streamlit as st

st.title("Análise Simplificada de Consórcios")

uploaded_file = st.file_uploader("Escolha o arquivo CSV", type="csv")

if uploaded_file is not None:
    # Ler o CSV
    df = pd.read_csv(uploaded_file, sep=';')

    # Mostrar as primeiras linhas
    st.subheader("Primeiras linhas do arquivo:")
    st.write(df.head())

    # Contar tipos de consórcio
    st.subheader("Quantidade de consórcios por tipo:")
    st.write(df['Código_do_segmento'].value_counts())

    # Top 5 administradoras com mais grupos ativos
    st.subheader("Top 5 administradoras com mais grupos ativos:")
    top_5 = df.groupby('Nome_da_Administradora')['Quantidade_de_grupos_ativos'].sum().sort_values(ascending=False).head()
    st.write(top_5)

    # Taxa de administração média
    st.subheader("Taxa de administração média:")
    taxa_media = df['Taxa_de_administração'].mean()
    st.write(f"{taxa_media:.2f}%")

else:
    st.info("Por favor, faça upload do arquivo CSV para começar a análise.")
