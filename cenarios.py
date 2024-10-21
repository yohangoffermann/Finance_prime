import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

def calculate_auto_financiado(vgv, custo_construcao, prazo_meses, entrada_percentual):
    fluxo = pd.DataFrame(index=range(prazo_meses), columns=['Receitas', 'Custos', 'Saldo'])
    fluxo['Custos'] = custo_construcao / prazo_meses
    fluxo.loc[0, 'Receitas'] = vgv * entrada_percentual
    fluxo['Receitas'].iloc[1:] = (vgv * (1 - entrada_percentual)) / (prazo_meses - 1)
    fluxo['Saldo'] = fluxo['Receitas'].cumsum() - fluxo['Custos'].cumsum()
    return fluxo

def calculate_financiamento(vgv, custo_construcao, prazo_meses, entrada_percentual, taxa_juros, percentual_financiado):
    fluxo = calculate_auto_financiado(vgv, custo_construcao, prazo_meses, entrada_percentual)
    valor_financiado = custo_construcao * percentual_financiado
    juros_totais = valor_financiado * ((1 + taxa_juros)**(prazo_meses/12) - 1)
    fluxo.loc[0, 'Saldo'] += valor_financiado
    fluxo.loc[prazo_meses-1, 'Custos'] += valor_financiado + juros_totais
    fluxo['Saldo'] = fluxo['Receitas'].cumsum() - fluxo['Custos'].cumsum()
    return fluxo

def calculate_constructa(vgv, custo_construcao, prazo_meses, entrada_percentual, lance_percentual, agio_percentual, taxa_selic):
    fluxo = pd.DataFrame(index=range(prazo_meses), columns=['Receitas', 'Custos', 'Saldo'])
    lance = custo_construcao * lance_percentual
    fluxo.loc[0, 'Receitas'] = custo_construcao + (vgv * entrada_percentual * (1 + agio_percentual))
    fluxo.loc[0, 'Custos'] = lance
    fluxo['Custos'].iloc[1:] = (custo_construcao - lance) / (prazo_meses - 1)
    fluxo['Receitas'].iloc[1:] = (vgv * (1 - entrada_percentual) * (1 + agio_percentual)) / (prazo_meses - 1)
    rendimento_selic = lance * ((1 + taxa_selic)**(prazo_meses/12) - 1)
    fluxo.loc[prazo_meses-1, 'Receitas'] += rendimento_selic
    fluxo['Saldo'] = fluxo['Receitas'].cumsum() - fluxo['Custos'].cumsum()
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

custo_construcao = vgv * custo_construcao_percentual / 100

fluxo_auto = calculate_auto_financiado(vgv, custo_construcao, prazo_meses, entrada_percentual)
fluxo_financiamento = calculate_financiamento(vgv, custo_construcao, prazo_meses, entrada_percentual, taxa_juros, percentual_financiado)
fluxo_constructa = calculate_constructa(vgv, custo_construcao, prazo_meses, entrada_percentual, lance_percentual, agio_percentual, taxa_selic)

fig = go.Figure()
fig.add_trace(go.Scatter(x=fluxo_auto.index, y=fluxo_auto['Saldo'], mode='lines', name='Auto Financiado'))
fig.add_trace(go.Scatter(x=fluxo_financiamento.index, y=fluxo_financiamento['Saldo'], mode='lines', name='Financiamento Tradicional'))
fig.add_trace(go.Scatter(x=fluxo_constructa.index, y=fluxo_constructa['Saldo'], mode='lines', name='Constructa'))
fig.update_layout(title='Comparativo de Fluxo de Caixa', xaxis_title='Meses', yaxis_title='Saldo (R$ milhões)')

st.plotly_chart(fig)

results = pd.DataFrame({
    'Cenário': ['Auto Financiado', 'Financiamento Tradicional', 'Constructa'],
    'Lucro Final (milhões R$)': [fluxo_auto['Saldo'].iloc[-1], fluxo_financiamento['Saldo'].iloc[-1], fluxo_constructa['Saldo'].iloc[-1]],
    'Exposição Máxima (milhões R$)': [-fluxo_auto['Saldo'].min(), -fluxo_financiamento['Saldo'].min(), -fluxo_constructa['Saldo'].min()],
    'TIR (%)': [np.irr(fluxo_auto['Saldo']) * 12 * 100, np.irr(fluxo_financiamento['Saldo']) * 12 * 100, np.irr(fluxo_constructa['Saldo']) * 12 * 100]
})

st.write(results)
