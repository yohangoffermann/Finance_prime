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

        # Filtrando apenas consórcio imobiliário (segmento 1)
        imoveis = df[df['Código_do_segmento'] == 1]
        
        # Calculando métricas de saúde dos grupos
        imoveis['taxa_adimplencia'] = imoveis['Quantidade_de_cotas_ativas_em_dia'] / imoveis['Quantidade_de_cotas_ativas_contempladas']
        imoveis['taxa_contemplacao'] = imoveis['Quantidade_acumulada_de_cotas_ativas_contempladas'] / imoveis['Quantidade_de_cotas_ativas_contempladas']
        imoveis['eficiencia_comercializacao'] = imoveis['Quantidade_de_cotas_comercializadas_no_mês'] / imoveis['Quantidade_de_cotas_excluídas_a_comercializar']
        
        # Criando um score de saúde
        imoveis['score_saude'] = (imoveis['taxa_adimplencia'] + imoveis['taxa_contemplacao'] + imoveis['eficiencia_comercializacao']) / 3
        
        # Ranking dos grupos mais saudáveis
        st.subheader("Top 10 Grupos Mais Saudáveis")
        grupos_saudaveis = imoveis.sort_values('score_saude', ascending=False).head(10)
        st.dataframe(grupos_saudaveis[['Nome_da_Administradora', 'score_saude']])
        
        # Análise de contemplações
        total_contemplados = imoveis['Quantidade_acumulada_de_cotas_ativas_contempladas'].sum()
        contemplados_mes = imoveis['Quantidade_de_cotas_ativas_contempladas_no_mês'].sum()
        
        col1, col2 = st.columns(2)
        col1.metric("Total de Contemplados", f"{total_contemplados:,}")
        col2.metric("Contemplados no Último Mês", f"{contemplados_mes:,}")
        
        # Inferência sobre lances
        imoveis['taxa_contemplacao_mensal'] = imoveis['Quantidade_de_cotas_ativas_contempladas_no_mês'] / imoveis['Quantidade_de_cotas_ativas_não_contempladas']
        media_contemplacao_mensal = imoveis['taxa_contemplacao_mensal'].mean()
        
        st.metric("Taxa Média de Contemplação Mensal", f"{media_contemplacao_mensal:.2%}")
        
        # Gráfico de dispersão: Taxa de Administração vs Score de Saúde
        fig = px.scatter(imoveis, x='Taxa_de_administração', y='score_saude', 
                         hover_name='Nome_da_Administradora', 
                         title='Taxa de Administração vs Score de Saúde')
        st.plotly_chart(fig)

    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {str(e)}")
        st.write("Por favor, verifique se o arquivo está no formato correto e tente novamente.")
else:
    st.info("Por favor, faça upload do arquivo CSV para começar a análise.")
