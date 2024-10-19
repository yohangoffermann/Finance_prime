import pandas as pd
import streamlit as st

# Criando o DataFrame com as linhas que você compartilhou
data = [
    ["ADEMICON ADM CONS S.A.", 84911098, 202408, 1, 23.66916, 67, 2, 0, 13580, 7708, 20139, 152359, 463, 151308, 2016, 19174, 127773, 2527, 4596],
    ["ADEMICON ADM CONS S.A.", 84911098, 202408, 2, 13.80067, 52, 0, 2, 553, 3518, 19365, 17693, 302, 33720, 1548, 1790, 17806, 7447, 1723],
    ["ADEMICON ADM CONS S.A.", 84911098, 202408, 3, 14.60279, 62, 1, 0, 2834, 2798, 11176, 41456, 366, 46624, 786, 5222, 28164, 2231, 3283],
    ["ADEMICON ADM CONS S.A.", 84911098, 202408, 4, 0.00000, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
]

columns = [
    "Nome_da_Administradora", "CNPJ_da_Administradora", "Data_base", "Código_do_segmento",
    "Taxa_de_administração", "Quantidade_de_grupos_ativos", "Quantidade_de_grupos_constituídos_no_mês",
    "Quantidade_de_grupos_encerrados_no_mês", "Quantidade_de_cotas_comercializadas_no_mês",
    "Quantidade_de_cotas_excluídas_a_comercializar", "Quantidade_acumulada_de_cotas_ativas_contempladas",
    "Quantidade_de_cotas_ativas_não_contempladas", "Quantidade_de_cotas_ativas_contempladas_no_mês",
    "Quantidade_de_cotas_ativas_em_dia", "Quantidade_de_cotas_ativas_contempladas_inadimplentes",
    "Quantidade_de_cotas_ativas_não_contempladas_inadimplentes", "Quantidade_de_cotas_excluídas",
    "Quantidade_de_cotas_ativas_quitadas", "Quantidade_de_cotas_ativas_com_crédito_pendente_de_utilização"
]

df = pd.DataFrame(data, columns=columns)

# Exibindo o DataFrame
st.write("DataFrame criado com as linhas fornecidas:")
st.dataframe(df)

# Informações sobre as colunas
st.write("Tipos de dados das colunas:")
st.write(df.dtypes)

# Estatísticas básicas
st.write("Estatísticas básicas:")
st.write(df.describe())

# Verificando a coluna específica
st.write("Valores da coluna 'Quantidade_de_cotas_ativas_contempladas':")
st.write(df['Quantidade_acumulada_de_cotas_ativas_contempladas'])

# Tentando fazer os cálculos
try:
    df['taxa_adimplencia'] = df['Quantidade_de_cotas_ativas_em_dia'] / (df['Quantidade_acumulada_de_cotas_ativas_contempladas'] + df['Quantidade_de_cotas_ativas_não_contempladas'])
    df['taxa_contemplacao'] = df['Quantidade_acumulada_de_cotas_ativas_contempladas'] / (df['Quantidade_acumulada_de_cotas_ativas_contempladas'] + df['Quantidade_de_cotas_ativas_não_contempladas'])
    df['eficiencia_comercializacao'] = df['Quantidade_de_cotas_comercializadas_no_mês'] / df['Quantidade_de_cotas_excluídas_a_comercializar']
    
    st.write("Cálculos realizados com sucesso!")
    st.write(df[['taxa_adimplencia', 'taxa_contemplacao', 'eficiencia_comercializacao']])
except Exception as e:
    st.error(f"Erro ao realizar os cálculos: {str(e)}")
