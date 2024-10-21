import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Configuração da página
st.set_page_config(
    page_title="Análise de Fluxo de Caixa",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS personalizado
st.markdown("""
<style>
    .reportview-container {
        background: #f0f2f6
    }
    .sidebar .sidebar-content {
        background: #ffffff
    }
    .Widget>label {
        color: #262730;
        font-family: sans-serif;
    }
    .stButton>button {
        color: #ffffff;
        background-color: #F63366;
        border-radius: 5px;
    }
    .stTextInput>div>div>input {
        color: #262730;
    }
</style>
""", unsafe_allow_html=True)

def calcular_fluxo_auto_financiado(vgv, custo_construcao, prazo_meses, 
                                   percentual_inicio, percentual_meio, percentual_fim,
                                   percentual_lancamento, percentual_baloes, percentual_parcelas,
                                   prazo_parcelas):
    fluxo = pd.DataFrame(index=range(prazo_meses), columns=['Mês', 'Receitas', 'Custos', 'Saldo Mensal', 'Saldo Acumulado'])
    
    # Distribuição dos custos
    custos = np.zeros(prazo_meses)
    tercio_obra = prazo_meses // 3
    custos[:tercio_obra] = custo_construcao * percentual_inicio / 100 / tercio_obra
    custos[tercio_obra:2*tercio_obra] = custo_construcao * percentual_meio / 100 / tercio_obra
    custos[2*tercio_obra:] = custo_construcao * percentual_fim / 100 / (prazo_meses - 2*tercio_obra)
    fluxo['Custos'] = custos
    
    # Inicializar receitas
    fluxo['Receitas'] = 0
    
    # Lançamento
    fluxo.loc[0, 'Receitas'] += vgv * percentual_lancamento / 100
    
    # Balões
    valor_baloes = vgv * percentual_baloes / 100
    num_baloes = 3
    for i in range(1, num_baloes + 1):
        mes_balao = i * prazo_meses // (num_baloes + 1)
        fluxo.loc[mes_balao, 'Receitas'] += valor_baloes / num_baloes
    
    # Parcelas
    valor_parcelas = vgv * percentual_parcelas / 100
    parcela_mensal = valor_parcelas / min(prazo_parcelas, prazo_meses)
    fluxo.loc[:min(prazo_parcelas, prazo_meses)-1, 'Receitas'] += parcela_mensal
    
    # Cálculo do saldo mensal e acumulado
    fluxo['Saldo Mensal'] = fluxo['Receitas'] - fluxo['Custos']
    fluxo['Saldo Acumulado'] = fluxo['Saldo Mensal'].cumsum()
    
    fluxo['Mês'] = range(1, prazo_meses + 1)
    
    return fluxo
                                       
def mostrar_grafico(fluxo):
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=fluxo['Mês'], 
        y=fluxo['Receitas'], 
        name='Receitas', 
        marker_color='green'
    ))
    
    fig.add_trace(go.Bar(
        x=fluxo['Mês'], 
        y=-fluxo['Custos'], 
        name='Custos', 
        marker_color='red'
    ))
    
    fig.add_trace(go.Scatter(
        x=fluxo['Mês'], 
        y=fluxo['Saldo Acumulado'], 
        name='Saldo Acumulado', 
        mode='lines+markers', 
        line=dict(color='blue', width=3),
        yaxis='y2'
    ))
    
    fig.update_layout(
        title='Fluxo de Caixa ao Longo do Tempo',
        xaxis_title='Mês',
        yaxis_title='Valores (milhões R$)',
        yaxis2=dict(
            title='Saldo Acumulado (milhões R$)',
            overlaying='y',
            side='right'
        ),
        barmode='relative',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=50, r=50, t=80, b=50),
        height=600
    )

    fig.add_shape(
        type="line",
        x0=fluxo['Mês'].min(),
        y0=0,
        x1=fluxo['Mês'].max(),
        y1=0,
        line=dict(color="black", width=1, dash="dash"),
    )

    st.plotly_chart(fig, use_container_width=True)
    
def main():
    st.title("Análise de Fluxo de Caixa - Modelo Auto Financiado")

    # Barra lateral para inputs
    st.sidebar.header("Parâmetros do Projeto")
    
    vgv = st.sidebar.number_input('VGV (Valor Geral de Vendas) em milhões R$', value=35.0, step=0.1)
    custo_construcao_percentual = st.sidebar.slider('Custo de Construção (% do VGV)', 50, 90, 70)
    prazo_meses = st.sidebar.number_input('Prazo de Construção (meses)', value=48, step=1)

    # Usar colunas para organizar os inputs
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Distribuição dos Custos")
        percentual_inicio = st.slider('% Custos no Início da Obra', 0, 100, 30)
        percentual_meio = st.slider('% Custos no Meio da Obra', 0, 100, 40)
        percentual_fim = st.slider('% Custos no Fim da Obra', 0, 100, 30)
        
        if percentual_inicio + percentual_meio + percentual_fim != 100:
            st.warning("A soma dos percentuais de custos deve ser 100%")
            return

    with col2:
        st.subheader("Distribuição das Vendas")
        percentual_lancamento = st.slider('% Vendas no Lançamento', 0, 100, 20)
        percentual_baloes = st.slider('% Vendas em Balões', 0, 100, 30)
        percentual_parcelas = st.slider('% Vendas em Parcelas', 0, 100, 50)
        
        if percentual_lancamento + percentual_baloes + percentual_parcelas != 100:
            st.warning("A soma dos percentuais de vendas deve ser 100%")
            return
        
        prazo_parcelas = st.slider('Prazo das Parcelas (meses)', 1, 120, 48)

    # Cálculos
    custo_construcao = vgv * custo_construcao_percentual / 100
    fluxo_auto = calcular_fluxo_auto_financiado(vgv, custo_construcao, prazo_meses, 
                                                percentual_inicio, percentual_meio, percentual_fim,
                                                percentual_lancamento, percentual_baloes, percentual_parcelas,
                                                prazo_parcelas)

    # Exibição dos resultados
    st.subheader('Fluxo de Caixa Mensal')
    st.dataframe(fluxo_auto)

    mostrar_grafico(fluxo_auto)

    # Cálculo das métricas
    lucro_total = fluxo_auto['Saldo Mensal'].sum()
    margem = (lucro_total / vgv) * 100
    exposicao_maxima = -fluxo_auto['Saldo Acumulado'].min()
    
    saldo_acumulado_positivo = fluxo_auto[fluxo_auto['Saldo Acumulado'] > 0]
    if not saldo_acumulado_positivo.empty:
        mes_payback = saldo_acumulado_positivo.index[0] + 1
        valor_payback = saldo_acumulado_positivo['Saldo Acumulado'].iloc[0]
    else:
        mes_payback = "Não atingido"
        valor_payback = None

    # Exibição das métricas
    st.subheader('Métricas do Projeto')
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("VGV", f"R$ {vgv:.2f} milhões")
        st.metric("Custo de Construção", f"R$ {custo_construcao:.2f} milhões")
    with col2:
        st.metric("Lucro Total", f"R$ {lucro_total:.2f} milhões")
        st.metric("Margem", f"{margem:.2f}%")
    with col3:
        st.metric("Exposição Máxima de Caixa", f"R$ {exposicao_maxima:.2f} milhões")
        if isinstance(mes_payback, int):
            st.metric("Mês de Payback", f"{mes_payback} (R$ {valor_payback:.2f} milhões)")
        else:
            st.metric("Mês de Payback", mes_payback)

    # Análise
    st.subheader('Análise')
    st.write(f"""
    No modelo auto financiado:
    1. O incorporador recebe R$ {vgv * percentual_lancamento / 100:.2f} milhões no lançamento.
    2. R$ {vgv * percentual_baloes / 100:.2f} milhões são recebidos em 3 balões ao longo do projeto.
    3. R$ {vgv * percentual_parcelas / 100:.2f} milhões são recebidos em {prazo_parcelas} parcelas mensais.
    4. Os custos de construção são distribuídos da seguinte forma:
       - {percentual_inicio}% no início da obra
       - {percentual_meio}% no meio da obra
       - {percentual_fim}% no final da obra
    5. A exposição máxima de caixa é de R$ {exposicao_maxima:.2f} milhões, o que representa o momento de maior necessidade de capital no projeto.
    6. O projeto atinge o ponto de equilíbrio (payback) no mês {mes_payback}{f', com um saldo positivo de R$ {valor_payback:.2f} milhões' if isinstance(mes_payback, int) else ''}.
    7. A margem final do projeto é de {margem:.2f}%.
    """)

if __name__ == "__main__":
    main()
