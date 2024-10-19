import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import io

st.set_page_config(page_title="Análise de Consórcios", layout="wide")

st.title("Análise de Consórcios Imobiliários")

uploaded_file = st.file_uploader("Escolha o arquivo CSV", type="csv")

if uploaded_file is not None:
    try:
        # Ler o conteúdo do arquivo
        content = uploaded_file.read().decode('latin1')
        
        # Mostrar as primeiras linhas do arquivo bruto
        st.subheader("Primeiras 5 linhas do arquivo bruto:")
        lines = content.split('\n')
        for line in lines[:5]:
            st.text(line)
        
        # Usar o StringIO para criar um objeto tipo arquivo
        csv_io = io.StringIO(content)
        
        # Tentar ler o CSV com o separador correto (;)
        df = pd.read_csv(csv_io, sep=';')
        
        # Mostrar as primeiras linhas do DataFrame
        st.subheader("Primeiras linhas do DataFrame:")
        st.write(df.head())

        # Mostrar informações sobre as colunas
        st.subheader("Informações sobre as colunas:")
        st.write(df.dtypes)

        # Mostrar estatísticas básicas
        st.subheader("Estatísticas básicas:")
        st.write(df.describe())

        # Verificar valores nulos
        st.subheader("Contagem de valores nulos por coluna:")
        st.write(df.isnull().sum())

        # Filtrando apenas consórcio imobiliário (segmento 1)
        imoveis = df[df['Código_do_segmento'] == 1]

        # Mostrar as primeiras linhas do DataFrame filtrado
        st.subheader("Primeiras linhas do DataFrame filtrado (apenas imóveis):")
        st.write(imoveis.head())

        # Mostrar informações sobre as colunas do DataFrame filtrado
        st.subheader("Informações sobre as colunas do DataFrame filtrado:")
        st.write(imoveis.dtypes)

    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {str(e)}")
        st.write("Por favor, verifique se o arquivo está no formato correto e tente novamente.")
        st.write("Detalhes do erro:", str(e))
        
        # Adicionar mais informações de debug
        st.subheader("Informações de Debug:")
        st.write("Colunas do DataFrame:")
        st.write(df.columns)
else:
    st.info("Por favor, faça upload do arquivo CSV para começar a análise.")
