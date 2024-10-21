import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def main():
    st.title("Fluxo de Caixa Detalhado do Empreendimento Imobiliário")

    params = get_user_inputs()
    fluxo_caixa = calcular_fluxo_caixa(params)
    metricas = calcular_metricas(fluxo_caixa, params)
    display_results(fluxo_caixa, metricas, params)

def get_user_inputs():
    st.sidebar.header("Parâmetros do Projeto")
    params = {
        'vgv': st.sidebar.number_input("VGV (milhões R$)", value=35.0, step=0.1),
        'custo_construcao_percentual': st.sidebar.slider("Custo de Construção (% do VGV)", 50, 90, 70),
        'prazo_meses': st.sidebar.number_input("Prazo de Construção (meses)", value=48, step=1),
        'entrada_percentual': st.sidebar.slider("Entrada (%)", 0, 50, 20),
        'num_baloes': st.sidebar.number_input("Número de Balões", 1, 5, 3, step=1),
        'taxa_juros_aplicacao': st.sidebar.number_input("Taxa de Juros para Aplicação (% a.a.)", value=5.0, step=0.1),
        'taxa_juros_financiamento': st.sidebar.number_input("Taxa de Juros para Financiamento (% a.a.)", value=12.0, step=0.1),
        'percentual_vendas_pre_lancamento': st.sidebar.slider("Vendas no Pré-Lançamento (%)", 0, 100, 30),
        'velocidade_vendas': st.sidebar.slider("Velocidade de Vendas (unidades/mês)", 1, 10, 3),
        'despesas_marketing_percentual': st.sidebar.slider("Despesas de Marketing (% do VGV)", 0, 10, 3),
        'despesas_administrativas_percentual': st.sidebar.slider("Despesas Administrativas (% do VGV)", 0, 10, 2),
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
    custo_construcao = vgv * (params['custo_construcao_percentual'] / 100)
    unidades_totais = int(vgv / 0.5)  # Assumindo preço médio de 500 mil por unidade

    fluxo = pd.DataFrame(0, index=range(meses), columns=['Receitas', 'Custos Construção', 'Despesas Marketing', 
                                                         'Despesas Administrativas', 'Juros', 'Saldo'])
    
    # Vendas no pré-lançamento
    unidades_vendidas_pre = int(unidades_totais * params['percentual_vendas_pre_lancamento'] / 100)
    fluxo.loc[0, 'Receitas'] += unidades_vendidas_pre * 0.5 * (params['entrada_percentual'] / 100)
    
    # Vendas durante a construção
    unidades_restantes = unidades_totais - unidades_vendidas_pre
    meses_venda = min(meses, int(unidades_restantes / params['velocidade_vendas']))
    
    for mes in range(meses_venda):
        unidades_vendidas = min(params['velocidade_vendas'], unidades_restantes)
        receita_mes = unidades_vendidas * 0.5
        fluxo.loc[mes, 'Receitas'] += receita_mes * (params['entrada_percentual'] / 100)
        
        # Balões
        for i, balao in enumerate(params['baloes']):
            mes_balao = int((i + 1) * meses / (len(params['baloes']) + 1))
            fluxo.loc[mes_balao, 'Receitas'] += receita_mes * (balao / 100)
        
        # Parcelas
        valor_parcela = (receita_mes * (params['parcelas_percentual'] / 100)) / meses
        for m in range(mes, meses):
            fluxo.loc[m, 'Receitas'] += valor_parcela
        
        unidades_restantes -= unidades_vendidas
    
    # Custos e Despesas
    fluxo['Custos Construção'] = calcular_curva_s(custo_construcao, meses)
    fluxo['Despesas Marketing'] = vgv * (params['despesas_marketing_percentual'] / 100) / meses
    fluxo['Despesas Administrativas'] = vgv * (params['despesas_administrativas_percentual'] / 100) / meses
    
    # Cálculo do Saldo e Juros
    saldo_acumulado = 0
    for mes in range(meses):
        receitas = fluxo.loc[mes, 'Receitas']
        custos = fluxo.loc[mes, 'Custos Construção'] + fluxo.loc[mes, 'Despesas Marketing'] + fluxo.loc[mes, 'Despesas Administrativas']
        saldo_mes = receitas - custos
        saldo_acumulado += saldo_mes
        
        if saldo_acumulado > 0:
            juros = saldo_acumulado * (params['taxa_juros_aplicacao'] / 100 / 12)
            fluxo.loc[mes, 'Juros'] = juros
            saldo_acumulado += juros
        else:
            juros = saldo_acumulado * (params['taxa_juros_financiamento'] / 100 / 12)
            fluxo.loc[mes, 'Juros'] = juros
            saldo_acumulado += juros
        
        fluxo.loc[mes, 'Saldo'] = saldo_acumulado
    
    return fluxo

def calcular_curva_s(total, meses):
    x = np.linspace(0, 1, meses)
    y = (1 / (1 + np.exp(-10*(x-0.5)))) * total
    return np.diff(y, prepend=0)

def calcular_vpl(taxa, fluxos):
    return sum(fluxo / (1 + taxa) ** i for i, fluxo in enumerate(fluxos))

def calcular_tir(fluxos):
    try:
        return np.irr(fluxos)
    except:
        return None

def calcular_metricas(fluxo_caixa, params):
    fluxos = fluxo_caixa['Saldo'].values
    taxa_mensal = params['taxa_juros_aplicacao'] / 100 / 12
    
    vpl = calcular_vpl(taxa_mensal, fluxos)
    tir = calcular_tir(fluxos)
    payback = np.where(fluxo_caixa['Saldo'] > 0)[0][0] if any(fluxo_caixa['Saldo'] > 0) else None
    max_exposicao = fluxo_caixa['Saldo'].min()
    
    return {
        'VPL': vpl,
        'TIR Mensal': tir,
        'TIR Anual': (1 + tir)**12 - 1 if tir is not None else None,
        'Payback (meses)': payback,
        'Máxima Exposição de Caixa': max_exposicao
    }

def display_results(fluxo_caixa, metricas, params):
    st.subheader("Fluxo de Caixa do Projeto")
    st.dataframe(fluxo_caixa)
    
    st.subheader("Gráfico do Fluxo de Caixa")
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(fluxo_caixa.index, fluxo_caixa['Saldo'], label='Saldo Acumulado')
    ax.bar(fluxo_caixa.index, fluxo_caixa['Receitas'], alpha=0.3, label='Receitas')
    ax.bar(fluxo_caixa.index, -fluxo_caixa['Custos Construção'], alpha=0.3, label='Custos Construção')
    ax.set_xlabel('Meses')
    ax.set_ylabel('Valor (R$ milhões)')
    ax.legend()
    st.pyplot(fig)
    
    st.subheader("Métricas Financeiras")
    for metrica, valor in metricas.items():
        st.write(f"{metrica}: {valor:.2f}" if isinstance(valor, float) else f"{metrica}: {valor}")
    
    st.subheader("Insights de Gestão de Fluxo de Caixa")
    eficiencia_caixa = (fluxo_caixa['Saldo'] >= 0).mean() * 100
    st.write(f"Eficiência de Caixa: {eficiencia_caixa:.2f}% dos meses com saldo positivo")
    
    meses_negativos = (fluxo_caixa['Saldo'] < 0).sum()
    st.write(f"Meses com Caixa Negativo: {meses_negativos}")
    
    juros_totais = fluxo_caixa['Juros'].sum()
    st.write(f"Total de Juros: R$ {juros_totais:.2f} milhões")
    
    if juros_totais < 0:
        st.write("Oportunidade: Considere estratégias para reduzir períodos de caixa negativo e minimizar custos de financiamento.")
    else:
        st.write("Oportunidade: Explore opções para maximizar o rendimento do caixa positivo.")
    
    velocidade_vendas_real = params['velocidade_vendas']
    velocidade_vendas_ideal = (params['vgv'] / 0.5) / params['prazo_meses']
    if velocidade_vendas_real < velocidade_vendas_ideal:
        st.write(f"Alerta: A velocidade de vendas atual ({velocidade_vendas_real:.2f} unidades/mês) está abaixo do ideal ({velocidade_vendas_ideal:.2f} unidades/mês) para o prazo do projeto.")
    
    st.write("Recomendações:")
    st.write("1. Monitore de perto a curva de vendas e ajuste as estratégias de marketing conforme necessário.")
    st.write("2. Considere negociar com fornecedores para alinhar os pagamentos com o fluxo de receitas.")
    st.write("3. Avalie a possibilidade de adiantar recebíveis em períodos de caixa negativo.")
    st.write("4. Mantenha uma reserva de contingência para lidar com flutuações imprevistas no fluxo de caixa.")

if __name__ == "__main__":
    main()
