import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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
    
    # Distribuição das receitas
    fluxo.loc[0, 'Receitas'] = vgv * percentual_lancamento / 100  # Lançamento
    
    # Balões
    num_baloes = 3  # Podemos ajustar isso se necessário
    for i in range(1, num_baloes + 1):
        mes_balao = i * prazo_meses // (num_baloes + 1)
        fluxo.loc[mes_balao, 'Receitas'] += vgv * (percentual_baloes / 100) / num_baloes
    
    # Parcelas
    valor_parcelas = vgv * percentual_parcelas / 100
    parcela_mensal = valor_parcelas / prazo_parcelas
    fluxo['Receitas'] += parcela_mensal
    
    fluxo['Saldo Mensal'] = fluxo['Receitas'] - fluxo['Custos']
    fluxo['Saldo Acumulado'] = fluxo['Saldo Mensal'].cumsum()
    
    fluxo['Mês'] = range(1, prazo_meses + 1)
    
    return fluxo

def calcular_fluxo_financiado(vgv, custo_construcao, prazo_meses, 
                              percentual_inicio, percentual_meio, percentual_fim,
                              percentual_lancamento, percentual_baloes, percentual_parcelas,
                              prazo_parcelas, percentual_financiado, taxa_juros_anual):
    fluxo = pd.DataFrame(index=range(prazo_meses), columns=['Mês', 'Receitas', 'Custos', 'Financiamento', 'Juros', 'Saldo Mensal', 'Saldo Acumulado'])
    
    # Distribuição dos custos
    custos = np.zeros(prazo_meses)
    tercio_obra = prazo_meses // 3
    custos[:tercio_obra] = custo_construcao * percentual_inicio / 100 / tercio_obra
    custos[tercio_obra:2*tercio_obra] = custo_construcao * percentual_meio / 100 / tercio_obra
    custos[2*tercio_obra:] = custo_construcao * percentual_fim / 100 / (prazo_meses - 2*tercio_obra)
    fluxo['Custos'] = custos
    
    # Distribuição das receitas
    fluxo.loc[0, 'Receitas'] = vgv * percentual_lancamento / 100  # Lançamento
    
    # Balões
    num_baloes = 3  # Podemos ajustar isso se necessário
    for i in range(1, num_baloes + 1):
        mes_balao = i * prazo_meses // (num_baloes + 1)
        fluxo.loc[mes_balao, 'Receitas'] += vgv * (percentual_baloes / 100) / num_baloes
    
    # Parcelas
    valor_parcelas = vgv * percentual_parcelas / 100
    parcela_mensal = valor_parcelas / prazo_parcelas
    fluxo['Receitas'] += parcela_mensal
    
    # Financiamento
    valor_financiado = custo_construcao * percentual_financiado / 100
    financiamento_mensal = valor_financiado / prazo_meses
    fluxo['Financiamento'] = financiamento_mensal
    
    # Cálculo dos juros
    taxa_juros_mensal = (1 + taxa_juros_anual) ** (1/12) - 1
    saldo_devedor = 0
    for mes in range(prazo_meses):
        saldo_devedor += financiamento_mensal
        juros = saldo_devedor * taxa_juros_mensal
        fluxo.loc[mes, 'Juros'] = juros
        fluxo.loc[mes, 'Custos'] += juros
    
    fluxo['Saldo Mensal'] = fluxo['Receitas'] + fluxo['Financiamento'] - fluxo['Custos']
    fluxo['Saldo Acumulado'] = fluxo['Saldo Mensal'].cumsum()
    
    fluxo['Mês'] = range(1, prazo_meses + 1)
    
    return fluxo

def mostrar_grafico(fluxo):
    st.subheader('Gráfico de Fluxo de Caixa')
    
    # Criar subplots: um para barras empilhadas, outro para linha
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.02, row_heights=[0.7, 0.3])
    
    # Adicionar barras para Receitas
    fig.add_trace(
        go.Bar(x=fluxo['Mês'], y=fluxo['Receitas'], name='Receitas', marker_color='green'),
        row=1, col=1
    )
    
    # Adicionar barras para Custos (valores negativos)
    fig.add_trace(
        go.Bar(x=fluxo['Mês'], y=-fluxo['Custos'], name='Custos', marker_color='red'),
        row=1, col=1
    )
    
    # Adicionar barras para Financiamento, se existir
    if 'Financiamento' in fluxo.columns:
        fig.add_trace(
            go.Bar(x=fluxo['Mês'], y=fluxo['Financiamento'], name='Financiamento', marker_color='orange'),
            row=1, col=1
        )
    
    # Adicionar linha para Saldo Acumulado no subplot inferior
    fig.add_trace(
        go.Scatter(x=fluxo['Mês'], y=fluxo['Saldo Acumulado'], name='Saldo Acumulado', mode='lines', line=dict(color='blue', width=2)),
        row=2, col=1
    )
    
    # Atualizar layout
    fig.update_layout(
        title='Fluxo de Caixa ao Longo do Tempo',
        barmode='relative',
        height=700,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    fig.update_xaxes(title_text="Mês", row=2, col=1)
    fig.update_yaxes(title_text="Valores (milhões R$)", row=1, col=1)
    fig.update_yaxes(title_text="Saldo Acumulado (milhões R$)", row=2, col=1)

    # Adicionar linha horizontal em y=0 no gráfico de Saldo Acumulado
    fig.add_shape(
        type="line",
        x0=fluxo['Mês'].min(),
        y0=0,
        x1=fluxo['Mês'].max(),
        y1=0,
        line=dict(color="black", width=1, dash="dash"),
        row=2, col=1
    )

    # Exibir o gráfico
    st.plotly_chart(fig, use_container_width=True)

def aba_auto_financiado():
    st.header("Modelo Auto Financiado")
    
    col1, col2 = st.columns(2)
    
    with col1:
        vgv = st.number_input('VGV (Valor Geral de Vendas) em milhões R$', value=35.0, step=0.1, key='vgv_auto')
        custo_construcao_percentual = st.slider('Custo de Construção (% do VGV)', 50, 90, 70, key='custo_auto')
        prazo_meses = st.number_input('Prazo de Construção (meses)', value=48, step=1, key='prazo_auto')

    with col2:
        st.subheader("Distribuição dos Custos")
        percentual_inicio = st.slider('% Custos no Início da Obra', 0, 100, 30, key='custo_inicio')
        percentual_meio = st.slider('% Custos no Meio da Obra', 0, 100, 40, key='custo_meio')
        percentual_fim = st.slider('% Custos no Fim da Obra', 0, 100, 30, key='custo_fim')
        
        if percentual_inicio + percentual_meio + percentual_fim != 100:
            st.warning("A soma dos percentuais de custos deve ser 100%")
            return

    st.subheader("Distribuição das Vendas")
    percentual_lancamento = st.slider('% Vendas no Lançamento', 0, 100, 20, key='vendas_lancamento')
    percentual_baloes = st.slider('% Vendas em Balões', 0, 100, 30, key='vendas_baloes')
    percentual_parcelas = st.slider('% Vendas em Parcelas', 0, 100, 50, key='vendas_parcelas')
    
    if percentual_lancamento + percentual_baloes + percentual_parcelas != 100:
        st.warning("A soma dos percentuais de vendas deve ser 100%")
        return
    
    prazo_parcelas = st.slider('Prazo das Parcelas (meses)', 1, 120, 48, key='prazo_parcelas')

    custo_construcao = vgv * custo_construcao_percentual / 100
    fluxo_auto = calcular_fluxo_auto_financiado(vgv, custo_construcao, prazo_meses, 
                                                percentual_inicio, percentual_meio, percentual_fim,
                                                percentual_lancamento, percentual_baloes, percentual_parcelas,
                                                prazo_parcelas)

    st.subheader('Fluxo de Caixa Mensal')
    st.dataframe(fluxo_auto)

    mostrar_grafico(fluxo_auto)

    lucro_total = fluxo_auto['Saldo Mensal'].sum()
    margem = (lucro_total / vgv) * 100
    exposicao_maxima = -fluxo_auto['Saldo Acumulado'].min()
    mes_payback = fluxo_auto[fluxo_auto['Saldo Acumulado'] > 0].index[0] + 1 if any(fluxo_auto['Saldo Acumulado'] > 0) else "Não atingido"

    st.subheader('Métricas do Projeto')
    col1, col2 = st.columns(2)
    with col1:
        st.metric("VGV", f"R$ {vgv:.2f} milhões")
        st.metric("Custo de Construção", f"R$ {custo_construcao:.2f} milhões")
        st.metric("Lucro Total", f"R$ {lucro_total:.2f} milhões")
    with col2:
        st.metric("Margem", f"{margem:.2f}%")
        st.metric("Exposição Máxima de Caixa", f"R$ {exposicao_maxima:.2f} milhões")
        st.metric("Mês de Payback", mes_payback)

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
    5. A exposição máxima de caixa é de R$ {exposicao_maxima:.2f} milhões.
    6. O projeto atinge o ponto de equilíbrio (payback) no mês {mes_payback}.
    7. A margem final do projeto é de {margem:.2f}%.
    """)

def aba_financiamento_tradicional():
    st.header("Modelo com Financiamento")
    
    col1, col2 = st.columns(2)
    
    with col1:
        vgv = st.number_input('VGV (Valor Geral de Vendas) em milhões R$', value=35.0, step=0.1, key='vgv_fin')
        custo_construcao_percentual = st.slider('Custo de Construção (% do VGV)', 50, 90, 70, key='custo_fin')
        prazo_meses = st.number_input('Prazo de Construção (meses)', value=48, step=1, key='prazo_fin')

    with col2:
        st.subheader("Distribuição dos Custos")
        percentual_inicio = st.slider('% Custos no Início da Obra', 0, 100, 30, key='custo_inicio_fin')
        percentual_meio = st.slider('% Custos no Meio da Obra', 0, 100, 40, key='custo_meio_fin')
        percentual_fim = st.slider('% Custos no Fim da Obra', 0, 100, 30, key='custo_fim_fin')
        
        if percentual_inicio + percentual_meio + percentual_fim != 100:
            st.warning("A soma dos percentuais de custos deve ser 100%")
            return

    st.subheader("Distribuição das Vendas")
    percentual_lancamento = st.slider('% Vendas no Lançamento', 0, 100, 20, key='vendas_lancamento_fin')
    percentual_baloes = st.slider('% Vendas em Balões', 0, 100, 30, key='vendas_baloes_fin')
    percentual_parcelas = st.slider('% Vendas em Parcelas', 0, 100, 50, key='vendas_parcelas_fin')
    
    if percentual_lancamento + percentual_baloes + percentual_parcelas != 100:
        st.warning("A soma dos percentuais de vendas deve ser 100%")
        return
    
    prazo_parcelas = st.slider('Prazo das Parcelas (meses)', 1, 120, 48, key='prazo_parcelas_fin')

    st.subheader("Financiamento")
    percentual_financiado = st.slider('% do Orçamento Financiado', 0, 100, 50, key='percentual_financiado')
    taxa_juros_anual = st.slider('Taxa de Juros Anual (%)', 0.0, 20.0, 12.0, step=0.1) / 100

    custo_construcao = vgv * custo_construcao_percentual / 100
    fluxo_financiado = calcular_fluxo_financiado(vgv, custo_construcao, prazo_meses, 
                                                 percentual_inicio, percentual_meio, percentual_fim,
                                                 percentual_lancamento, percentual_baloes, percentual_parcelas,
                                                 prazo_parcelas, percentual_financiado, taxa_juros_anual)

    st.subheader('Fluxo de Caixa Mensal')
    st.dataframe(fluxo_financiado)

    mostrar_grafico(fluxo_financiado)

    lucro_total = fluxo_financiado['Receitas'].sum() - fluxo_financiado['Custos'].sum()
    margem = (lucro_total / vgv) * 100
    exposicao_maxima = -fluxo_financiado['Saldo Acumulado'].min()
    mes_payback = fluxo_financiado[fluxo_financiado['Saldo Acumulado'] > 0].index[0] + 1 if any(fluxo_financiado['Saldo Acumulado'] > 0) else "Não atingido"

    st.subheader('Métricas do Projeto')
    col1, col2 = st.columns(2)
    with col1:
        st.metric("VGV", f"R$ {vgv:.2f} milhões")
        st.metric("Custo de Construção", f"R$ {custo_construcao:.2f} milhões")
        st.metric("Lucro Total", f"R$ {lucro_total:.2f} milhões")
    with col2:
        st.metric("Margem", f"{margem:.2f}%")
        st.metric("Exposição Máxima de Caixa", f"R$ {exposicao_maxima:.2f} milhões")
        st.metric("Mês de Payback", mes_payback)

    valor_financiado = custo_construcao * percentual_financiado / 100
    juros_totais = fluxo_financiado['Juros'].sum()

    st.subheader('Análise')
    st.write(f"""
    No modelo com financiamento:
    1. O incorporador recebe R$ {vgv * percentual_lancamento / 100:.2f} milhões no lançamento.
    2. R$ {vgv * percentual_baloes / 100:.2f} milhões são recebidos em 3 balões ao longo do projeto.
    3. R$ {vgv * percentual_parcelas / 100:.2f} milhões são recebidos em {prazo_parcelas} parcelas mensais.
    4. Os custos de construção são distribuídos da seguinte forma:
       - {percentual_inicio}% no início da obra
       - {percentual_meio}% no meio da obra
       - {percentual_fim}% no final da obra
    5. O projeto utiliza um financiamento de R$ {valor_financiado:.2f} milhões ({percentual_financiado}% do custo de construção).
    6. O custo total de juros do financiamento é de R$ {juros_totais:.2f} milhões.
    7. A exposição máxima de caixa é de R$ {exposicao_maxima:.2f} milhões.
    8. O projeto atinge o ponto de equilíbrio (payback) no mês {mes_payback}.
    9. A margem final do projeto é de {margem:.2f}%.
    """)

def main():
    st.title('Análise de Fluxo de Caixa - Modelos de Incorporação')

    tab1, tab2 = st.tabs(["Auto Financiado", "Financiamento"])

    with tab1:
        aba_auto_financiado()

    with tab2:
        aba_financiamento_tradicional()

if __name__ == "__main__":
    main()
