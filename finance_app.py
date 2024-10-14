import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import locale

# Configurar a localização para formatação de números
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

def formatar_moeda(valor):
    return locale.currency(valor, grouping=True, symbol=None)

def parse_moeda(valor_str):
    try:
        return locale.atof(valor_str.replace('R$', '').strip())
    except ValueError:
        return 0.0

def input_moeda(label, value=0.0, key=None):
    valor_str = st.sidebar.text_input(label, value=formatar_moeda(value), key=key)
    return parse_moeda(valor_str)

def calcular_parcela_consorcio(valor_total, prazo, taxa_admin_anual, percentual_lance):
    valor_lance = valor_total * (percentual_lance / 100)
    credito_efetivo = valor_total - valor_lance
    taxa_admin_mensal = taxa_admin_anual / 12 / 100
    
    amortizacao = credito_efetivo / prazo
    custo_admin = valor_total * taxa_admin_mensal
    
    parcela = amortizacao + custo_admin
    return parcela

def calcular_economia(valor_total, taxa_tradicional_anual, taxa_admin_anual, prazo, percentual_lance):
    # Cálculo do custo total do financiamento tradicional
    taxa_tradicional_mensal = (1 + taxa_tradicional_anual/100)**(1/12) - 1
    parcela_tradicional = valor_total * (taxa_tradicional_mensal * (1 + taxa_tradicional_mensal)**prazo) / ((1 + taxa_tradicional_mensal)**prazo - 1)
    custo_total_tradicional = parcela_tradicional * prazo

    # Cálculo do custo total do Constructa
    parcela_constructa = calcular_parcela_consorcio(valor_total, prazo, taxa_admin_anual, percentual_lance)
    custo_total_constructa = (parcela_constructa * prazo) + (valor_total * (percentual_lance / 100))

    return custo_total_tradicional - custo_total_constructa

def simular_fluxo_caixa(valor_total, prazo, taxa_admin_anual, percentual_lance, mes_dropdown, percentual_dropdown):
    lance = valor_total * (percentual_lance / 100)
    parcela_inicial = calcular_parcela_consorcio(valor_total, prazo, taxa_admin_anual, percentual_lance)
    
    fluxo_caixa = [-lance] + [-parcela_inicial] * (mes_dropdown - 1)
    
    if mes_dropdown < prazo:
        valor_dropdown = valor_total * (percentual_dropdown / 100)
        credito_apos_dropdown = valor_total * (1 - percentual_dropdown / 100)
        parcela_apos_dropdown = calcular_parcela_consorcio(credito_apos_dropdown, prazo - mes_dropdown, taxa_admin_anual, 0)
        
        fluxo_caixa += [valor_dropdown - parcela_apos_dropdown]
        fluxo_caixa += [-parcela_apos_dropdown] * (prazo - mes_dropdown - 1)
    
    return fluxo_caixa

def plot_fluxo_caixa(fluxo_caixa):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(range(len(fluxo_caixa)), fluxo_caixa, marker='o')
    ax.set_title("Fluxo de Caixa do Projeto")
    ax.set_xlabel("Mês")
    ax.set_ylabel("Fluxo de Caixa (R$)")
    ax.grid(True)
    return fig

def main():
    st.set_page_config(page_title="Constructa - Simulador de Crédito Otimizado", layout="wide")
    st.title("Constructa - Simulador de Crédito Otimizado")

    # Inputs na sidebar
    st.sidebar.header("Parâmetros do Projeto")
    valor_total = input_moeda("Valor Total do Projeto (R$)", value=1000000.0, key="valor_total")
    prazo = st.sidebar.slider("Prazo do Projeto (meses)", min_value=12, max_value=240, value=60)
    percentual_lance = st.sidebar.slider("Percentual de Lance (%)", min_value=0.0, max_value=50.0, value=20.0, step=0.1)
    taxa_admin = st.sidebar.slider("Taxa de Administração Anual (%)", min_value=0.1, max_value=20.0, value=1.2, step=0.1)
    taxa_tradicional = st.sidebar.slider("Taxa de Juros Tradicional (% a.a.)", min_value=1.0, max_value=20.0, value=12.0, step=0.1)

    st.sidebar.header("Simulação de Dropdown")
    mes_dropdown = st.sidebar.slider("Mês do Dropdown", min_value=1, max_value=prazo, value=min(24, prazo))
    percentual_dropdown = st.sidebar.slider("Percentual do Dropdown (%)", min_value=0.0, max_value=50.0, value=30.0, step=0.1)

    if st.sidebar.button("Calcular"):
        # Verificações
        if percentual_lance >= 100:
            st.error("O percentual de lance não pode ser 100% ou maior.")
            return

        # Cálculos
        parcela = calcular_parcela_consorcio(valor_total, prazo, taxa_admin, percentual_lance)
        economia = calcular_economia(valor_total, taxa_tradicional, taxa_admin, prazo, percentual_lance)
        fluxo_caixa = simular_fluxo_caixa(valor_total, prazo, taxa_admin, percentual_lance, mes_dropdown, percentual_dropdown)

        # Cálculos adicionais
        valor_lance = valor_total * (percentual_lance / 100)
        credito_efetivo = valor_total - valor_lance

        # Exibição dos resultados
        col1, col2 = st.columns(2)
        
        with col1:
            st.header("Resultados")
            st.write(f"Parcela Inicial: {formatar_moeda(parcela)}")
            st.write(f"Economia Total Estimada: {formatar_moeda(economia)}")
            st.write(f"Valor do Lance: {formatar_moeda(valor_lance)}")
            st.write(f"Crédito Efetivo: {formatar_moeda(credito_efetivo)}")
            st.write(f"Relação Parcela/Crédito Novo: {(parcela / credito_efetivo) * 100:.2f}%")

        with col2:
            st.header("Fluxo de Caixa")
            fig = plot_fluxo_caixa(fluxo_caixa)
            st.pyplot(fig)

        st.header("Detalhamento do Fluxo de Caixa")
        df = pd.DataFrame({
            'Mês': range(len(fluxo_caixa)),
            'Fluxo de Caixa': fluxo_caixa
        })
        st.dataframe(df)

        # Aviso sobre parcela alta
        if parcela > (valor_total * 0.03):  # 3% do valor total como exemplo
            st.warning("Atenção: O valor da parcela calculada é relativamente alto em relação ao valor total do projeto. Considere ajustar os parâmetros.")

if __name__ == "__main__":
    main()
