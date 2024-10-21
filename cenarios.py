import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def main():
    st.title("Fluxo de Caixa Simplificado - Empreendimento Imobiliário com Constructa")

    params = get_user_inputs()
    fluxo_caixa = calcular_fluxo_caixa(params)
    display_results(fluxo_caixa, params)

    # Opção para usar a ferramenta Constructa
    if st.checkbox("Aplicar Ferramenta Constructa"):
        fluxo_otimizado = ferramenta_constructa(fluxo_caixa, params)
        
        st.subheader("Análise Comparativa")
        st.write(f"VPL Original: R$ {fluxo_caixa['Saldo'].iloc[-1]:.2f} milhões")
        st.write(f"VPL Otimizado: R$ {fluxo_otimizado['Saldo Otimizado'].iloc[-1]:.2f} milhões")
        st.write(f"Melhoria no VPL: R$ {(fluxo_otimizado['Saldo Otimizado'].iloc[-1] - fluxo_caixa['Saldo'].iloc[-1]):.2f} milhões")

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

    params['prazo_parcelas'] = st.sidebar.number_input("Prazo das Parcelas (meses)", value=120, min_value=params['prazo_meses'], step=1)

    return params

def calcular_fluxo_caixa(params):
    meses_obra = params['prazo_meses']
    meses_total = max(meses_obra, params['prazo_parcelas'])
    vgv = params['vgv']
    custo_obra = vgv * (params['custo_obra_percentual'] / 100)

    fluxo = pd.DataFrame(0, index=range(meses_total), columns=['Receitas', 'Custos Obra', 'Saldo'])
    
    # Entrada
    fluxo.loc[0, 'Receitas'] = vgv * (params['entrada_percentual'] / 100)
    
    # Balões
    for i, balao in enumerate(params['baloes']):
        mes_balao = int((i + 1) * meses_obra / (len(params['baloes']) + 1))
        fluxo.loc[mes_balao, 'Receitas'] += vgv * (balao / 100)
    
    # Parcelas
    valor_parcela = (vgv * (params['parcelas_percentual'] / 100)) / params['prazo_parcelas']
    for mes in range(params['prazo_parcelas']):
        fluxo.loc[mes, 'Receitas'] += valor_parcela
    
    # Custos da Obra (distribuição linear simplificada)
    fluxo.loc[:meses_obra-1, 'Custos Obra'] = custo_obra / meses_obra
    
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

    # Análise adicional
    st.subheader("Análise Adicional")
    receita_total = fluxo_caixa['Receitas'].sum()
    custo_total = fluxo_caixa['Custos Obra'].sum()
    margem = (receita_total - custo_total) / receita_total * 100

    st.write(f"Receita Total: R$ {receita_total:.2f} milhões")
    st.write(f"Custo Total da Obra: R$ {custo_total:.2f} milhões")
    st.write(f"Margem do Projeto: {margem:.2f}%")

    valor_parcela = (params['vgv'] * (params['parcelas_percentual'] / 100)) / params['prazo_parcelas']
    st.write(f"Valor da Parcela Mensal: R$ {valor_parcela*1e6:.2f}")

    if max_exposicao < 0:
        st.write(f"Necessidade de Capital de Giro: R$ {abs(max_exposicao):.2f} milhões")
        st.write("Considere estratégias para reduzir a exposição máxima de caixa, como negociar melhores condições de pagamento com fornecedores ou buscar financiamento para cobrir o período de exposição negativa.")
    else:
        st.write("O projeto não apresenta necessidade de capital de giro adicional.")

    if meses_negativos > 0:
        st.write(f"O projeto apresenta {meses_negativos} meses com fluxo de caixa negativo. Considere estratégias para melhorar o fluxo de caixa nesses períodos.")
    else:
        st.write("O projeto mantém fluxo de caixa positivo durante toda sua duração.")

    st.write(f"Prazo total do fluxo de caixa: {len(fluxo_caixa)} meses")
    st.write(f"Prazo de construção: {params['prazo_meses']} meses")
    st.write(f"Prazo das parcelas: {params['prazo_parcelas']} meses")

def calcular_parcela_consorcio(valor_consorcio, prazo_meses, taxa_administracao_percentual):
    valor_credito_mensal = valor_consorcio / prazo_meses
    taxa_administracao = (valor_consorcio * taxa_administracao_percentual / 100) / prazo_meses
    
    return valor_credito_mensal + taxa_administracao

def simular_uso_consorcio(fluxo_caixa, oportunidades_agio, valor_consorcio, params):
    fluxo_otimizado = fluxo_caixa.copy()
    
    # Adicionar o crédito do consórcio como entrada de caixa no início
    fluxo_otimizado.loc[0, 'Receitas Consórcio'] = valor_consorcio
    
    prazo_consorcio = params['prazo_meses']
    taxa_administracao = params['taxa_administracao']
    
    valor_parcela_consorcio = calcular_parcela_consorcio(valor_consorcio, prazo_consorcio, taxa_administracao)
    
    fluxo_otimizado['Custos Consórcio'] = 0
    fluxo_otimizado['Vendas Consórcio'] = 0
    
    saldo_consorcio = valor_consorcio
    
    for mes in range(prazo_consorcio):
        # Adicionar o custo da parcela do consórcio
        fluxo_otimizado.loc[mes, 'Custos Consórcio'] = valor_parcela_consorcio
        
        # Verificar oportunidades de venda com ágio
        oportunidade = oportunidades_agio[oportunidades_agio['Mês'] == mes]
        if not oportunidade.empty and saldo_consorcio > 0:
            valor_venda = min(oportunidade['Valor Recebido'].values[0], saldo_consorcio)
            agio = valor_venda * (params['percentual_agio'] / 100)
            fluxo_otimizado.loc[mes, 'Vendas Consórcio'] = valor_venda + agio
            saldo_consorcio -= valor_venda
    
    # Calcular o novo saldo
    fluxo_otimizado['Saldo Otimizado'] = (
        fluxo_otimizado['Saldo'] + 
        fluxo_otimizado['Receitas Consórcio'].cumsum() - 
        fluxo_otimizado['Custos Consórcio'].cumsum() -
        fluxo_otimizado['Vendas Consórcio'].cumsum()
    )
    
    return fluxo_otimizado

def ferramenta_constructa(fluxo_caixa, params):
    st.subheader("Ferramenta Constructa")

    # Parâmetros específicos do Constructa
    percentual_consorcio = st.slider("Percentual do VGV para Consórcio", 50, 100, 70)
    percentual_agio = st.slider("Percentual de Ágio Esperado", 5, 30, 10)
    taxa_administracao = st.slider("Taxa de Administração Mensal (%)", 0.1, 1.0, 0.5, step=0.1)

    valor_consorcio = params['vgv'] * (percentual_consorcio / 100)
    
    # Adicionar estes parâmetros ao dicionário params
    params['taxa_administracao'] = taxa_administracao
    params['percentual_agio'] = percentual_agio
    
    # Identificar oportunidades de ágio
    oportunidades_agio = identificar_oportunidades_agio(fluxo_caixa, params, percentual_agio)

    # Simular uso do consórcio
    fluxo_otimizado = simular_uso_consorcio(fluxo_caixa, oportunidades_agio, valor_consorcio, params)

    # Exibir resultados
    st.write("Oportunidades de Ágio Identificadas:")
    st.table(oportunidades_agio)

    st.write("Fluxo de Caixa Otimizado com Constructa:")
    st.dataframe(fluxo_otimizado)

    # Comparar fluxos
    comparar_fluxos(fluxo_caixa, fluxo_otimizado)

    # Informações adicionais de debug
    st.write("Detalhes do Fluxo Otimizado:")
    st.write(f"Valor Total do Consórcio: R$ {valor_consorcio:.2f} milhões")
    st.write(f"Soma das Receitas Consórcio: R$ {fluxo_otimizado['Receitas Consórcio'].sum():.2f} milhões")
    st.write(f"Soma dos Custos Consórcio: R$ {fluxo_otimizado['Custos Consórcio'].sum():.2f} milhões")
    st.write(f"Soma das Vendas Consórcio: R$ {fluxo_otimizado['Vendas Consórcio'].sum():.2f} milhões")
    st.write(f"Diferença entre Saldo Original e Otimizado no último mês: R$ {(fluxo_otimizado['Saldo Otimizado'].iloc[-1] - fluxo_caixa['Saldo'].iloc[-1]):.2f} milhões")

    return fluxo_otimizado

def identificar_oportunidades_agio(fluxo_caixa, params, percentual_agio):
    oportunidades = []
    threshold = fluxo_caixa['Receitas'].mean() * 1.5

    for mes, row in fluxo_caixa.iterrows():
        if row['Receitas'] > threshold or mes == 0 or mes in [int((i+1)*params['prazo_meses']/(len(params['baloes'])+1)) for i in range(len(params['baloes']))]:
            oportunidades.append({
                'Mês': mes,
                'Valor Recebido': row['Receitas'],
                'Potencial de Ágio': row['Receitas'] * (percentual_agio / 100)
            })

    return pd.DataFrame(oportunidades)

def comparar_fluxos(fluxo_original, fluxo_
