import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from decimal import Decimal, ROUND_HALF_UP

# Configuração da página
st.set_page_config(page_title="Constructa MVP", layout="wide")

# Funções de cálculo
def calcular_parcela(valor_credito, prazo_meses, taxa_admin_anual, indice_correcao_anual):
    valor_credito = Decimal(str(valor_credito))
    prazo_meses = Decimal(str(prazo_meses))
    taxa_admin_mensal = Decimal(str(taxa_admin_anual)) / Decimal('12') / Decimal('100')
    indice_correcao_mensal = (Decimal('1') + Decimal(str(indice_correcao_anual))/Decimal('100'))**(Decimal('1')/Decimal('12')) - Decimal('1')
    fator = (Decimal('1') + indice_correcao_mensal) / (Decimal('1') - (Decimal('1') + indice_correcao_mensal)**(-prazo_meses))
    parcela = valor_credito * (fator + taxa_admin_mensal)
    return parcela.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def calcular_saldo_devedor(valor_credito, parcela, taxa_admin_anual, indice_correcao_anual, meses_pagos):
    valor_credito = Decimal(str(valor_credito))
    parcela = Decimal(str(parcela))
    taxa_admin_mensal = Decimal(str(taxa_admin_anual)) / Decimal('12') / Decimal('100')
    indice_correcao_mensal = (Decimal('1') + Decimal(str(indice_correcao_anual))/Decimal('100'))**(Decimal('1')/Decimal('12')) - Decimal('1')
    saldo = valor_credito * (Decimal('1') + indice_correcao_mensal)**Decimal(str(meses_pagos))
    for _ in range(meses_pagos):
        saldo -= parcela - (saldo * taxa_admin_mensal)
    return max(saldo, Decimal('0')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def calcular_fluxo_caixa(vgv, orcamento, prazo, perfil_vendas, perfil_despesas):
    receitas = gerar_perfil(vgv, prazo, perfil_vendas)
    despesas = gerar_perfil(orcamento, prazo, perfil_despesas)
    fluxo_caixa = [receitas[i] - despesas[i] for i in range(prazo)]
    return fluxo_caixa

def gerar_perfil(valor_total, prazo, perfil):
    valor_total = Decimal(str(valor_total))
    prazo = Decimal(str(prazo))
    if perfil == 'Linear':
        return [valor_total / prazo] * int(prazo)
    elif perfil == 'Front-loaded':
        meio = int(prazo) // 2
        return [valor_total * Decimal('0.6') / Decimal(str(meio))] * meio + \
               [valor_total * Decimal('0.4') / (prazo - Decimal(str(meio)))] * (int(prazo) - meio)
    elif perfil == 'Back-loaded':
        meio = int(prazo) // 2
        return [valor_total * Decimal('0.4') / Decimal(str(meio))] * meio + \
               [valor_total * Decimal('0.6') / (prazo - Decimal(str(meio)))] * (int(prazo) - meio)

def aplicar_dropdown(saldo_devedor, valor_dropdown, agio):
    saldo_devedor = Decimal(str(saldo_devedor))
    valor_dropdown = Decimal(str(valor_dropdown))
    agio = Decimal(str(agio))
    valor_efetivo = valor_dropdown * (Decimal('1') + agio/Decimal('100'))
    novo_saldo = max(saldo_devedor - valor_efetivo, Decimal('0'))
    return novo_saldo.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

# Interface do usuário
st.title("Constructa MVP")

# Módulo 1: Crédito Otimizado
st.header("Módulo 1: Crédito Otimizado")
valor_credito = st.number_input("Valor do Crédito", min_value=0.0, value=100000.0, step=1000.0)
prazo_meses = st.number_input("Prazo (meses)", min_value=1, value=60, step=1)
taxa_admin_anual = st.number_input("Taxa de Administração Anual (%)", min_value=0.0, value=10.0, step=0.1)
indice_correcao_anual = st.number_input("Índice de Correção Anual (%)", min_value=0.0, value=5.0, step=0.1)
valor_lance = st.number_input("Valor do Lance", min_value=0.0, value=0.0, step=1000.0)

if st.button("Calcular Parcela"):
    parcela = calcular_parcela(valor_credito, prazo_meses, taxa_admin_anual, indice_correcao_anual)
    st.write(f"Parcela Mensal: R$ {parcela:.2f}")
    
    credito_novo = Decimal(str(valor_credito)) - Decimal(str(valor_lance))
    relacao_parcela_credito = (parcela / credito_novo) * Decimal('100')
    st.write(f"Relação Parcela/Crédito Novo: {relacao_parcela_credito:.2f}%")

# Módulo 2: Dados do Empreendimento
st.header("Módulo 2: Dados do Empreendimento")
vgv = st.number_input("VGV (Valor Geral de Vendas)", min_value=0.0, value=1000000.0, step=10000.0)
orcamento = st.number_input("Orçamento", min_value=0.0, value=800000.0, step=10000.0)
prazo_empreendimento = st.number_input("Prazo do Empreendimento (meses)", min_value=1, value=24, step=1)
perfil_vendas = st.selectbox("Perfil de Vendas", ['Linear', 'Front-loaded', 'Back-loaded'])
perfil_despesas = st.selectbox("Perfil de Despesas", ['Linear', 'Front-loaded', 'Back-loaded'])

if st.button("Calcular Fluxo de Caixa"):
    fluxo_caixa = calcular_fluxo_caixa(vgv, orcamento, prazo_empreendimento, perfil_vendas, perfil_despesas)
    df_fluxo = pd.DataFrame({
        'Mês': range(1, prazo_empreendimento + 1),
        'Fluxo de Caixa': fluxo_caixa
    })
    st.line_chart(df_fluxo.set_index('Mês'))
    st.write(df_fluxo)

# Módulo 3: Dropdown
st.header("Módulo 3: Dropdown")
valor_dropdown = st.number_input("Valor do Dropdown", min_value=0.0, value=50000.0, step=1000.0)
agio = st.number_input("Ágio (%)", min_value=0.0, value=5.0, step=0.1)
mes_dropdown = st.number_input("Mês do Dropdown", min_value=1, value=12, step=1)

if st.button("Simular Dropdown"):
    saldo_original = calcular_saldo_devedor(valor_credito, parcela, taxa_admin_anual, indice_correcao_anual, mes_dropdown)
    novo_saldo = aplicar_dropdown(saldo_original, valor_dropdown, agio)
    st.write(f"Saldo Original: R$ {saldo_original:.2f}")
    st.write(f"Novo Saldo após Dropdown: R$ {novo_saldo:.2f}")
    
    prazo_restante = prazo_meses - mes_dropdown
    nova_parcela = calcular_parcela(novo_saldo, prazo_restante, taxa_admin_anual, indice_correcao_anual)
    st.write(f"Nova Parcela: R$ {nova_parcela:.2f}")
    
    economia_total = (Decimal(str(parcela)) * Decimal(str(prazo_meses))) - (nova_parcela * Decimal(str(prazo_restante)) + Decimal(str(valor_dropdown)))
    st.write(f"Economia Total: R$ {economia_total:.2f}")

# Visualizações
st.header("Visualizações")
if 'parcela' in locals() and 'nova_parcela' in locals():
    fig, ax = plt.subplots()
    meses = list(range(1, prazo_meses + 1))
    saldos_originais = [calcular_saldo_devedor(valor_credito, parcela, taxa_admin_anual, indice_correcao_anual, m) for m in meses]
    saldos_com_dropdown = saldos_originais[:mes_dropdown] + \
                          [calcular_saldo_devedor(novo_saldo, nova_parcela, taxa_admin_anual, indice_correcao_anual, m - mes_dropdown) 
                           for m in range(mes_dropdown, prazo_meses + 1)]
    
    ax.plot(meses, saldos_originais, label='Sem Dropdown')
    ax.plot(meses, saldos_com_dropdown, label='Com Dropdown')
    ax.set_xlabel('Meses')
    ax.set_ylabel('Saldo Devedor')
    ax.set_title('Amortização do Saldo Devedor')
    ax.legend()
    st.pyplot(fig)

st.sidebar.info("Constructa MVP - Versão 1.0.0")
