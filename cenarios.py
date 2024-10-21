import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def main():
    st.title("Fluxo de Caixa Simplificado - Empreendimento Imobiliário")

    params = get_user_inputs()
    fluxo_caixa = calcular_fluxo_caixa(params)
    display_results(fluxo_caixa, params)

def get_user_inputs():
    st.sidebar.header("Parâmetros do Projeto")
    params = {
        'vgv': st.sidebar.number_input("VGV (milhões R$)", value=35.0, step=0.1),
        'custo_obra_percentual': st.sidebar.slider("Custo da Obra (% do VGV)", 50, 90, 70),
        'prazo_meses': st.sidebar.number_input("Prazo de Construção (meses)", value=48, step=1),
        'entrada_percentual': st.sidebar.slider("Entrada (%)", 0, 50, 20),
        'num_baloes': st.sidebar.number_input("Número de Balões", 1, 5, 3, step=1),
    }
    
    baloes = []
    total_baloes = 0
    for i in range(params['num_baloes']):
        balao = st.sidebar.slider(f"Balão {i+1} (%)", 0, 50-total_baloes, 10)
        baloes.append(balao)
        total_baloes += balao
    params['baloes'] = baloes

    params['parcelas_percentual'] = 100 - params['entrada_percentual'] - sum(baloes)
    st.sidebar.write(f"Parcelas Mensais: {params['parcelas_percentual']}%")

    return params

def calcular_fluxo_caixa(params):
    meses = params['prazo_meses']
    vgv = params['vgv']
    custo_obra = vgv * (params['custo_obra_percentual'] / 100)

    fluxo = pd.DataFrame(index=range(meses), columns=['Receitas', 'Custos Obra', 'Saldo'])
    
    # Receitas
    fluxo.loc[0, 'Receitas'] = vgv * (params['entrada_percentual'] / 100)
    
    # Balões
    for i, balao in enumerate(params['baloes']):
        mes_balao = int((i + 1) * meses / (len(params['baloes']) + 1))
        fluxo.loc[mes_balao, 'Receitas'] += vgv * (balao / 100)
    
    # Parcelas
    valor_parcela = (vgv * (params['parcelas_percentual'] / 100)) / meses
    fluxo['Receitas'] = fluxo['Receitas'].fillna(valor_parcela)
    
    # Custos da Obra (distribuição linear simplificada)
    fluxo['Custos Obra'] = custo_obra / meses
    
    # Saldo
    fluxo['Saldo'] = fluxo['Receitas'].cumsum() - fluxo['Custos Obra'].cumsum()
    
    return fluxo

def display_results(fluxo_caixa, params):
    st.subheader("Fluxo de Caixa do Projeto")
    st.dataframe(fluxo_caixa)
    
    st.subheader("Gráfico do Fluxo de Caixa")
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(fluxo_caixa.index, fluxo_caixa['Saldo'], label='Saldo Acumulado')
    ax.bar(fluxo_caixa.index, fluxo_caixa['Receitas'], alpha=0.3, label='Receitas')
    ax.bar(fluxo_caixa.index, -fluxo_caixa['Custos Obra'], alpha=0.3, label='Custos Obra')
    ax.set_xlabel('Meses')
    ax.set_ylabel('Valor (R$ milhões)')
    ax.legend()
    st.pyplot(fig)
    
    st.subheader("Métricas do Projeto")
    vpl = fluxo_caixa['Saldo'].iloc[-1]
    max_exposicao = fluxo_caixa['Saldo'].min()
    meses_negativos = (fluxo_caixa['Saldo'] < 0).sum()
    
    st.write(f"VPL do Projeto: R$ {vpl:.2f} milhões")
    st.write(f"Máxima Exposição de Caixa: R$ {max_exposicao:.2f} milhões")
    st.write(f"Meses com Caixa Negativo: {meses_negativos}")
    
    eficiencia_caixa = (fluxo_caixa['Saldo'] >= 0).mean() * 100
    st.write(f"Eficiência de Caixa: {eficiencia_caixa:.2f}% dos meses com saldo positivo")

if __name__ == "__main__":
    main()
