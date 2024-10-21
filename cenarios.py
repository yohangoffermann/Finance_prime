# Funções Compartilhadas

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

def mostrar_metricas(fluxo, vgv, custo_construcao, is_financiado=False):
    if is_financiado:
        receita_total = fluxo['Receitas'].sum()
        custo_total = fluxo['Custos'].sum()
        lucro_total = receita_total - custo_total
    else:
        lucro_total = fluxo['Saldo Mensal'].sum()
    
    margem = (lucro_total / vgv) * 100
    exposicao_maxima = -fluxo['Saldo Acumulado'].min()
    mes_payback = fluxo[fluxo['Saldo Acumulado'] > 0].index[0] + 1 if any(fluxo['Saldo Acumulado'] > 0) else "Não atingido"

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

def mostrar_grafico(fluxo):
    st.subheader('Gráfico de Fluxo de Caixa')
    fig = go.Figure()
    fig.add_trace(go.Bar(x=fluxo['Mês'], y=fluxo['Receitas'], name='Receitas', marker_color='green'))
    fig.add_trace(go.Bar(x=fluxo['Mês'], y=-fluxo['Custos'], name='Custos', marker_color='red'))
    if 'Financiamento' in fluxo.columns:
        fig.add_trace(go.Bar(x=fluxo['Mês'], y=fluxo['Financiamento'], name='Financiamento', marker_color='orange'))
    fig.add_trace(go.Scatter(x=fluxo['Mês'], y=fluxo['Saldo Acumulado'], name='Saldo Acumulado', mode='lines', line=dict(color='blue', width=2)))

    fig.update_layout(
        title='Fluxo de Caixa ao Longo do Tempo',
        xaxis_title='Mês',
        yaxis_title='Valor (milhões R$)',
        barmode='relative'
    )

    st.plotly_chart(fig)

# Aba Auto Financiado

def calcular_fluxo_auto_financiado(vgv, custo_construcao, prazo_meses, entrada_percentual):
    fluxo = pd.DataFrame(index=range(prazo_meses), columns=['Mês', 'Receitas', 'Custos', 'Saldo Mensal', 'Saldo Acumulado'])
    
    fluxo.loc[0, 'Receitas'] = vgv * entrada_percentual
    receita_mensal = (vgv * (1 - entrada_percentual)) / (prazo_meses - 1)
    fluxo['Receitas'].iloc[1:] = receita_mensal
    
    fluxo['Custos'] = custo_construcao / prazo_meses
    
    fluxo['Saldo Mensal'] = fluxo['Receitas'] - fluxo['Custos']
    fluxo['Saldo Acumulado'] = fluxo['Saldo Mensal'].cumsum()
    
    fluxo['Mês'] = range(1, prazo_meses + 1)
    
    return fluxo

def aba_auto_financiado():
    st.header("Modelo Auto Financiado")
    
    vgv = st.number_input('VGV (Valor Geral de Vendas) em milhões R$', value=35.0, step=0.1, key='vgv_auto')
    custo_construcao_percentual = st.slider('Custo de Construção (% do VGV)', 50, 90, 70, key='custo_auto')
    prazo_meses = st.number_input('Prazo de Construção (meses)', value=48, step=1, key='prazo_auto')
    entrada_percentual = st.slider('Entrada (%)', 10, 50, 30, key='entrada_auto') / 100

    custo_construcao = vgv * custo_construcao_percentual / 100
    fluxo_auto = calcular_fluxo_auto_financiado(vgv, custo_construcao, prazo_meses, entrada_percentual)

    st.subheader('Fluxo de Caixa Mensal')
    st.dataframe(fluxo_auto)

    mostrar_grafico(fluxo_auto)
    mostrar_metricas(fluxo_auto, vgv, custo_construcao)

    receita_mensal = (vgv * (1 - entrada_percentual)) / (prazo_meses - 1)
    st.subheader('Análise')
    st.write(f"""
    No modelo auto financiado:
    1. O incorporador recebe R$ {vgv * entrada_percentual:.2f} milhões de entrada.
    2. O restante (R$ {vgv * (1-entrada_percentual):.2f} milhões) é recebido em {prazo_meses-1} parcelas mensais de R$ {receita_mensal:.2f} milhões.
    3. Os custos de construção são distribuídos igualmente ao longo de {prazo_meses} meses, sendo R$ {custo_construcao / prazo_meses:.2f} milhões por mês.
    4. A exposição máxima de caixa é de R$ {-fluxo_auto['Saldo Acumulado'].min():.2f} milhões, ocorrendo no início do projeto.
    5. O projeto atinge o ponto de equilíbrio (payback) no mês {fluxo_auto[fluxo_auto['Saldo Acumulado'] > 0].index[0] + 1 if any(fluxo_auto['Saldo Acumulado'] > 0) else "Não atingido"}.
    6. Não há custos financeiros adicionais (como juros de financiamento), o que contribui para uma margem mais alta de {(fluxo_auto['Saldo Mensal'].sum() / vgv) * 100:.2f}%.
    """)

# Aba Auto Financiado

def calcular_fluxo_auto_financiado(vgv, custo_construcao, prazo_meses, entrada_percentual):
    fluxo = pd.DataFrame(index=range(prazo_meses), columns=['Mês', 'Receitas', 'Custos', 'Saldo Mensal', 'Saldo Acumulado'])
    
    fluxo.loc[0, 'Receitas'] = vgv * entrada_percentual
    receita_mensal = (vgv * (1 - entrada_percentual)) / (prazo_meses - 1)
    fluxo['Receitas'].iloc[1:] = receita_mensal
    
    fluxo['Custos'] = custo_construcao / prazo_meses
    
    fluxo['Saldo Mensal'] = fluxo['Receitas'] - fluxo['Custos']
    fluxo['Saldo Acumulado'] = fluxo['Saldo Mensal'].cumsum()
    
    fluxo['Mês'] = range(1, prazo_meses + 1)
    
    return fluxo

def aba_auto_financiado():
    st.header("Modelo Auto Financiado")
    
    vgv = st.number_input('VGV (Valor Geral de Vendas) em milhões R$', value=35.0, step=0.1, key='vgv_auto')
    custo_construcao_percentual = st.slider('Custo de Construção (% do VGV)', 50, 90, 70, key='custo_auto')
    prazo_meses = st.number_input('Prazo de Construção (meses)', value=48, step=1, key='prazo_auto')
    entrada_percentual = st.slider('Entrada (%)', 10, 50, 30, key='entrada_auto') / 100

    custo_construcao = vgv * custo_construcao_percentual / 100
    fluxo_auto = calcular_fluxo_auto_financiado(vgv, custo_construcao, prazo_meses, entrada_percentual)

    st.subheader('Fluxo de Caixa Mensal')
    st.dataframe(fluxo_auto)

    mostrar_grafico(fluxo_auto)
    mostrar_metricas(fluxo_auto, vgv, custo_construcao)

    receita_mensal = (vgv * (1 - entrada_percentual)) / (prazo_meses - 1)
    st.subheader('Análise')
    st.write(f"""
    No modelo auto financiado:
    1. O incorporador recebe R$ {vgv * entrada_percentual:.2f} milhões de entrada.
    2. O restante (R$ {vgv * (1-entrada_percentual):.2f} milhões) é recebido em {prazo_meses-1} parcelas mensais de R$ {receita_mensal:.2f} milhões.
    3. Os custos de construção são distribuídos igualmente ao longo de {prazo_meses} meses, sendo R$ {custo_construcao / prazo_meses:.2f} milhões por mês.
    4. A exposição máxima de caixa é de R$ {-fluxo_auto['Saldo Acumulado'].min():.2f} milhões, ocorrendo no início do projeto.
    5. O projeto atinge o ponto de equilíbrio (payback) no mês {fluxo_auto[fluxo_auto['Saldo Acumulado'] > 0].index[0] + 1 if any(fluxo_auto['Saldo Acumulado'] > 0) else "Não atingido"}.
    6. Não há custos financeiros adicionais (como juros de financiamento), o que contribui para uma margem mais alta de {(fluxo_auto['Saldo Mensal'].sum() / vgv) * 100:.2f}%.
    """)
    # Aba Financiamento Tradicional

def calcular_fluxo_financiado(vgv, custo_construcao, prazo_meses, entrada_percentual, percentual_financiado, taxa_juros_anual):
    fluxo = pd.DataFrame(index=range(prazo_meses), columns=['Mês', 'Receitas', 'Custos', 'Financiamento', 'Juros', 'Saldo Mensal', 'Saldo Acumulado'])
    
    fluxo.loc[0, 'Receitas'] = vgv * entrada_percentual
    receita_mensal = (vgv * (1-entrada_percentual)) / (prazo_meses - 1)
    fluxo['Receitas'].iloc[1:] = receita_mensal
    
    fluxo['Custos'] = custo_construcao / prazo_meses
    
    valor_financiado = custo_construcao * percentual_financiado
    fluxo.loc[0, 'Financiamento'] = valor_financiado
    
    taxa_juros_mensal = (1 + taxa_juros_anual) ** (1/12) - 1
    parcela_financiamento = valor_financiado * (taxa_juros_mensal * (1 + taxa_juros_mensal) ** prazo_meses) / ((1 + taxa_juros_mensal) ** prazo_meses - 1)
    
    saldo_devedor = valor_financiado
    for mes in range(prazo_meses):
        juros = saldo_devedor * taxa_juros_mensal
        amortizacao = parcela_financiamento - juros
        fluxo.loc[mes, 'Juros'] = juros
        fluxo.loc[mes, 'Custos'] += parcela_financiamento
        saldo_devedor -= amortizacao
    
    fluxo['Saldo Mensal'] = fluxo['Receitas'] + fluxo['Financiamento'].fillna(0) - fluxo['Custos']
    fluxo['Saldo Acumulado'] = fluxo['Saldo Mensal'].cumsum()
    
    fluxo['Mês'] = range(1, prazo_meses + 1)
    
    return fluxo

def aba_financiamento_tradicional():
    st.header("Modelo com Financiamento Tradicional")
    
    vgv = st.number_input('VGV (Valor Geral de Vendas) em milhões R$', value=35.0, step=0.1, key='vgv_fin')
    custo_construcao_percentual = st.slider('Custo de Construção (% do VGV)', 50, 90, 70, key='custo_fin')
    prazo_meses = st.number_input('Prazo de Construção (meses)', value=48, step=1, key='prazo_fin')
    entrada_percentual = st.slider('Entrada (%)', 10, 50, 30, key='entrada_fin') / 100
    percentual_financiado = st.slider('Percentual Financiado (%)', 20, 80, 50) / 100
    taxa_juros_anual = st.slider('Taxa de Juros Anual (%)', 5.0, 20.0, 12.0) / 100

    custo_construcao = vgv * custo_construcao_percentual / 100
    fluxo_financiado = calcular_fluxo_financiado(vgv, custo_construcao, prazo_meses, entrada_percentual, percentual_financiado, taxa_juros_anual)

    st.subheader('Fluxo de Caixa Mensal')
    st.dataframe(fluxo_financiado)

    mostrar_grafico(fluxo_financiado)
    mostrar_metricas(fluxo_financiado, vgv, custo_construcao, is_financiado=True)

    valor_financiado = custo_construcao * percentual_financiado
    juros_totais = fluxo_financiado['Juros'].sum()
    receita_mensal = (vgv * (1-entrada_percentual)) / (prazo_meses - 1)
    
    st.subheader('Análise')
    st.write(f"""
    No modelo com financiamento tradicional:
    1. O incorporador recebe R$ {vgv * entrada_percentual:.2f} milhões de entrada dos compradores.
    2. Adicionalmente, recebe R$ {valor_financiado:.2f} milhões de financiamento bancário.
    3. O restante das vendas (R$ {vgv * (1-entrada_percentual):.2f} milhões) é recebido em {prazo_meses-1} parcelas mensais de R$ {receita_mensal:.2f} milhões.
    4. Os custos de construção são distribuídos ao longo de {prazo_meses} meses.
    5. Há um custo adicional de juros sobre o valor financiado, totalizando R$ {juros_totais:.2f} milhões ao longo do projeto.
    6. A exposição máxima de caixa é de R$ {-fluxo_financiado['Saldo Acumulado'].min():.2f} milhões.
    7. O projeto atinge o ponto de equilíbrio (payback) no mês {fluxo_financiado[fluxo_financiado['Saldo Acumulado'] > 0].index[0] + 1 if any(fluxo_financiado['Saldo Acumulado'] > 0) else "Não atingido"}.
    8. Este modelo reduz a necessidade de capital próprio inicial, mas impacta a margem final devido aos juros, resultando em uma margem de {((fluxo_financiado['Receitas'].sum() - fluxo_financiado['Custos'].sum()) / vgv) * 100:.2f}%.
    """)
    # Código Principal (main)

def main():
    st.title('Análise de Fluxo de Caixa - Modelos de Incorporação')

    tab1, tab2 = st.tabs(["Auto Financiado", "Financiamento Tradicional"])

    with tab1:
        aba_auto_financiado()

    with tab2:
        aba_financiamento_tradicional()

if __name__ == "__main__":
    main()
