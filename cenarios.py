import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

def calculate_auto_financiado(vgv, custo_construcao, prazo_meses, entrada_percentual):
    fluxo = pd.DataFrame(index=range(prazo_meses), columns=['Receitas', 'Custos', 'Saldo'])
    fluxo.loc[0, 'Receitas'] = vgv * entrada_percentual
    fluxo['Receitas'].iloc[1:] = (vgv * (1 - entrada_percentual)) / (prazo_meses - 1)
    fluxo['Custos'] = custo_construcao / prazo_meses
    fluxo['Saldo'] = fluxo['Receitas'] - fluxo['Custos']
    fluxo['Saldo Acumulado'] = fluxo['Saldo'].cumsum()
    return fluxo

def calculate_financiamento(vgv, custo_construcao, prazo_meses, entrada_percentual, taxa_juros, percentual_financiado):
    fluxo = pd.DataFrame(index=range(prazo_meses), columns=['Receitas', 'Custos', 'Financiamento', 'Saldo'])
    
    fluxo.loc[0, 'Receitas'] = vgv * entrada_percentual
    receita_mensal = (vgv * (1 - entrada_percentual)) / (prazo_meses - 1)
    fluxo['Receitas'].iloc[1:] = receita_mensal
    
    custo_mensal = custo_construcao / prazo_meses
    fluxo['Custos'] = custo_mensal
    
    valor_financiado = custo_construcao * percentual_financiado
    fluxo.loc[0, 'Financiamento'] = valor_financiado
    
    taxa_mensal = (1 + taxa_juros) ** (1/12) - 1
    parcela = valor_financiado * (taxa_mensal * (1 + taxa_mensal) ** prazo_meses) / ((1 + taxa_mensal) ** prazo_meses - 1)
    
    saldo_devedor = valor_financiado
    for mes in range(prazo_meses):
        juros = saldo_devedor * taxa_mensal
        amortizacao = parcela - juros
        fluxo.loc[mes, 'Custos'] += parcela
        saldo_devedor -= amortizacao
    
    fluxo['Saldo'] = fluxo['Receitas'] - fluxo['Custos'] + fluxo['Financiamento']
    fluxo['Saldo Acumulado'] = fluxo['Saldo'].cumsum()
    return fluxo

def calculate_constructa(vgv, custo_construcao, prazo_meses, entrada_percentual, lance_percentual, agio_percentual, taxa_selic, taxa_admin_consorcio):
    fluxo = pd.DataFrame(index=range(prazo_meses), columns=['Receitas', 'Custos', 'Crédito Consórcio', 'Saldo'])
    lance = custo_construcao * lance_percentual
    credito_consorcio = custo_construcao - lance
    
    fluxo.loc[0, 'Receitas'] = vgv * entrada_percentual * (1 + agio_percentual)
    fluxo.loc[0, 'Crédito Consórcio'] = credito_consorcio
    fluxo.loc[0, 'Custos'] = lance
    
    custo_mensal_construcao = custo_construcao / prazo_meses
    fluxo['Custos'] = custo_mensal_construcao
    
    amortizacao_mensal = credito_consorcio / prazo_meses
    taxa_admin_mensal = (taxa_admin_consorcio / 100 / 12) * credito_consorcio
    parcela_consorcio = amortizacao_mensal + taxa_admin_mensal
    
    fluxo['Custos'] += parcela_consorcio
    
    receita_mensal = (vgv * (1 - entrada_percentual) * (1 + agio_percentual)) / (prazo_meses - 1)
    fluxo['Receitas'].iloc[1:] = receita_mensal
    
    rendimento_selic = lance * ((1 + taxa_selic)**(prazo_meses/12) - 1)
    fluxo.loc[prazo_meses-1, 'Receitas'] += rendimento_selic
    
    fluxo['Saldo'] = fluxo['Receitas'] - fluxo['Custos'] + fluxo['Crédito Consórcio']
    fluxo['Saldo Acumulado'] = fluxo['Saldo'].cumsum()
    return fluxo

st.title('Comparativo de Cenários de Incorporação Imobiliária')

vgv = st.sidebar.number_input('VGV (milhões R$)', value=35.0, step=0.1)
custo_construcao_percentual = st.sidebar.slider('Custo de Construção (% do VGV)', 50, 90, 70)
prazo_meses = st.sidebar.number_input('Prazo de Construção (meses)', value=48, step=1)
entrada_percentual = st.sidebar.slider('Entrada (%)', 10, 50, 30) / 100
taxa_selic = st.sidebar.number_input('Taxa Selic (% a.a.)', value=11.0, step=0.1) / 100
taxa_juros = st.sidebar.number_input('Taxa de Juros Financiamento (% a.a.)', value=12.0, step=0.1) / 100
percentual_financiado = st.sidebar.slider('Percentual Financiado', 20, 80, 40) / 100
lance_percentual = st.sidebar.slider('Lance do Consórcio (%)', 20, 40, 25) / 100
agio_percentual = st.sidebar.slider('Ágio do Consórcio (%)', 10, 50, 20) / 100
taxa_admin_consorcio = st.sidebar.slider('Taxa de Administração do Consórcio (% a.a.)', 0.5, 5.0, 1.0, step=0.1)

custo_construcao = vgv * custo_construcao_percentual / 100

fluxo_auto = calculate_auto_financiado(vgv, custo_construcao, prazo_meses, entrada_percentual)
fluxo_financiamento = calculate_financiamento(vgv, custo_construcao, prazo_meses, entrada_percentual, taxa_juros, percentual_financiado)
fluxo_constructa = calculate_constructa(vgv, custo_construcao, prazo_meses, entrada_percentual, lance_percentual, agio_percentual, taxa_selic, taxa_admin_consorcio)

fig = go.Figure()
fig.add_trace(go.Scatter(x=fluxo_auto.index, y=fluxo_auto['Saldo Acumulado'], mode='lines', name='Auto Financiado'))
fig.add_trace(go.Scatter(x=fluxo_financiamento.index, y=fluxo_financiamento['Saldo Acumulado'], mode='lines', name='Financiamento Tradicional'))
fig.add_trace(go.Scatter(x=fluxo_constructa.index, y=fluxo_constructa['Saldo Acumulado'], mode='lines', name='Constructa'))
fig.update_layout(title='Comparativo de Fluxo de Caixa', xaxis_title='Meses', yaxis_title='Saldo Acumulado (R$ milhões)')

st.plotly_chart(fig)

results = pd.DataFrame({
    'Cenário': ['Auto Financiado', 'Financiamento Tradicional', 'Constructa'],
    'Receita Total (milhões R$)': [fluxo_auto['Receitas'].sum(), 
                                   fluxo_financiamento['Receitas'].sum(), 
                                   fluxo_constructa['Receitas'].sum()],
    'Custo Total (milhões R$)': [fluxo_auto['Custos'].sum(), 
                                 fluxo_financiamento['Custos'].sum(), 
                                 fluxo_constructa['Custos'].sum()],
    'Lucro Bruto (milhões R$)': [fluxo_auto['Saldo'].sum(), 
                                 fluxo_financiamento['Saldo'].sum() - fluxo_financiamento['Financiamento'].sum(), 
                                 fluxo_constructa['Saldo'].sum() - fluxo_constructa['Crédito Consórcio'].sum()],
    'Margem Bruta (%)': [(fluxo_auto['Saldo'].sum() / fluxo_auto['Receitas'].sum()) * 100,
                         ((fluxo_financiamento['Saldo'].sum() - fluxo_financiamento['Financiamento'].sum()) / fluxo_financiamento['Receitas'].sum()) * 100,
                         ((fluxo_constructa['Saldo'].sum() - fluxo_constructa['Crédito Consórcio'].sum()) / fluxo_constructa['Receitas'].sum()) * 100],
    'Exposição Máxima (milhões R$)': [-fluxo_auto['Saldo Acumulado'].min(), 
                                      -fluxo_financiamento['Saldo Acumulado'].min(), 
                                      -fluxo_constructa['Saldo Acumulado'].min()]
})

st.write(results)

fig_margin = go.Figure(data=[
    go.Bar(name='Margem Bruta (%)', x=results['Cenário'], y=results['Margem Bruta (%)'])
])
fig_margin.update_layout(title='Comparativo de Margem Bruta por Cenário')
st.plotly_chart(fig_margin)

st.subheader("Análise Comparativa")
melhor_margem = results.loc[results['Margem Bruta (%)'].idxmax(), 'Cenário']
menor_exposicao = results.loc[results['Exposição Máxima (milhões R$)'].idxmin(), 'Cenário']

st.write(f"O cenário com a melhor margem bruta é: {melhor_margem}")
st.write(f"O cenário com a menor exposição máxima de caixa é: {menor_exposicao}")

diferenca_margem = results['Margem Bruta (%)'].max() - results['Margem Bruta (%)'].min()
st.write(f"A diferença entre a maior e a menor margem bruta é de {diferenca_margem:.2f} pontos percentuais.")

st.write("Considerações:")
st.write("1. O modelo Auto Financiado geralmente oferece a maior margem bruta, mas pode requerer maior capital próprio.")
st.write("2. O Financiamento Tradicional pode reduzir a necessidade de capital próprio, mas os juros impactam a margem.")
st.write("3. O modelo Constructa equilibra a necessidade de capital com potencial de ganho através do ágio, considerando o custo do carrego do consórcio.")
st.write("4. A taxa de administração do consórcio e o percentual de lance impactam significativamente o desempenho do modelo Constructa.")
