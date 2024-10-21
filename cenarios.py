import streamlit as st
from streamlit_option_menu import option_menu
import plotly.express as px
import pandas as pd
import numpy as np

# Configuração da página
st.set_page_config(page_title="Aplicativo de Exemplo", layout="wide")

# Menu de navegação lateral
with st.sidebar:
    selected = option_menu(
        "Menu Principal", ["Home", "Warehouse", "Query Optimization", "Contact Us"],
        icons=["house", "archive", "graph-up-arrow", "envelope"],
        menu_icon="cast", default_index=0
    )

# Conteúdo principal
st.title("Aplicativo de Exemplo")

# Exemplo de gráficos usando Plotly
if selected == "Home":
    st.header("Home")
    df = pd.DataFrame(np.random.randn(20, 3), columns=['a', 'b', 'c'])
    fig = px.line(df, x=df.index, y=['a', 'b', 'c'], title="Gráfico de Linhas")
    st.plotly_chart(fig, use_container_width=True)

elif selected == "Warehouse":
    st.header("Warehouse")
    df = pd.DataFrame(np.random.randn(20, 3), columns=['a', 'b', 'c'])
    fig = px.bar(df, x=df.index, y=['a', 'b', 'c'], title="Gráfico de Barras")
    st.plotly_chart(fig, use_container_width=True)

elif selected == "Query Optimization":
    st.header("Query Optimization")
    df = pd.DataFrame(np.random.randn(20, 3), columns=['a', 'b', 'c'])
    fig = px.area(df, x=df.index, y=['a', 'b', 'c'], title="Gráfico de Área")
    st.plotly_chart(fig, use_container_width=True)

elif selected == "Contact Us":
    st.header("Contact Us")
    st.write("Informações de contato aqui...")
