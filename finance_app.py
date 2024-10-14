import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Tente importar numpy, mas use uma alternativa se falhar
try:
    import numpy as np
except ImportError:
    print("NumPy não pôde ser importado. Usando alternativas.")
    class np:
        @staticmethod
        def arange(*args, **kwargs):
            return range(*args)

# Funções de cálculo
def calcular_relacao_parcela_credito(valor_cota, taxa_admin_anual, prazo_meses):
    taxa_admin_mensal = taxa_admin_anual / 12 / 100
    parcela = (valor_cota / prazo_meses) + (valor_cota * taxa_admin_mensal)
    relacao = (parcela / valor_cota) * 100
    return relacao

def calcular_economia(valor_total, taxa_tradicional_anual, taxa_constructa_anual, prazo_meses):
    taxa_tradicional_mensal = (1 + taxa_tradicional_anual/100)**(1/12) - 1
    taxa_constructa_mensal = (1 + taxa_constructa_anual/100)**(1/12) - 1
    
    custo_tradicional = valor_total * ((1 + taxa_tradicional_mensal)**prazo_meses - 1) / taxa_tradicional_mensal
    custo_constructa = valor_total * ((1 + taxa_constructa_mensal)**prazo_meses - 1) / taxa_constructa_mensal
    
    economia = custo_tradicional - custo_constructa
    return economia

def calcular_fluxo_caixa(valor_total, prazo_meses, percentual_lance, taxa_admin_anual):
    lance = valor_total * (percentual_lance / 100)
    credito_novo = valor_total - lance
    taxa_admin_mensal = taxa_admin_anual / 12 / 100
    parcela = (credito_novo / prazo_meses) + (valor_total * taxa_admin_mensal)
    
    fluxo_caixa = [-lance]  # Mês 0: pagamento do lance
    for _ in range(prazo_meses):
        fluxo_caixa.append(-parcela)
    
    return fluxo_caixa

def simular_dropdown(valor_total, prazo_meses, percentual_lance, taxa_admin_anual, mes_dropdown, percentual_dropdown):
    fluxo_inicial = calcular_fluxo_caixa(valor_total, prazo_meses, percentual_lance, taxa_admin_anual)
    
    valor_dropdown = valor_total * (percentual_dropdown / 100)
    parcela_apos_dropdown = ((valor_total - valor_dropdown) / prazo_meses) + (valor_total * taxa_admin_anual / 12 / 100)
    
    for i in range(mes_dropdown, prazo_meses):
        fluxo_inicial[i] = -parcela_apos_dropdown
    
    fluxo_inicial[mes_dropdown] += valor_dropdown  # Receita do dropdown
    
    return fluxo_inicial

def main():
    st.set_page_config(page_title="Constructa - Simulador de Crédito Otimizado", layout="wide")
    st.title("Constructa - Simulador de Crédito Otimizado")

    # Entradas do usuário
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Dados do Projeto")
        valor_projeto = st.number_input("Valor total do projeto (R$)", min_value=0.0, value=1000000.0, help="Insira o valor total do projeto")
        prazo = st.number_input("Prazo do projeto (meses)", min_value=1, max_value=240, value=60, help="Insira o prazo do projeto em meses")
        valor_terreno = st.number_input("Valor do terreno (R$, opcional)", min_value=0.0, value=0.0, help="Insira o valor do terreno, se aplicável")

    with col2:
        st.subheader("Dados do Consórcio")
        valor_cota = st.number_input("Valor da cota (R$)", min_value=0.0, value=valor_projeto, help="Insira o valor da cota do consórcio")
        num_cotas = st.number_input("Número de cotas", min_value=1, value=1, help="Insira o número de cotas do consórcio")
        taxa_admin_anual = st.number_input("Taxa de administração anual (%)", min_value=0.0, max_value=100.0, value=10.0, help="Insira a taxa de administração anual do consórcio")
        percentual_lance = st.number_input("Percentual de lance (%)", min_value=0.0, max_value=100.0, value=20.0, help="Insira o percentual de lance do consórcio")

    st.subheader("Simulação de Dropdown")
    mes_dropdown = st.number_input("Mês do dropdown", min_value=1, max_value=prazo, value=12, help="Insira o mês em que ocorrerá o dropdown")
    percentual_dropdown = st.number_input("Percentual do dropdown (%)", min_value=0.0, max_value=100.0, value=30.0, help="Insira o percentual do dropdown")

    if st.button("Calcular"):
        # Cálculos
        relacao_parcela_credito = calcular_relacao_parcela_credito(valor_cota, taxa_admin_anual, prazo)
        economia_estimada = calcular_economia(valor_projeto, 12.0, taxa_admin_anual, prazo)  # 12% a.a. para financiamento tradicional
        fluxo_caixa_sem_dropdown = calcular_fluxo_caixa(valor_projeto, prazo, percentual_lance, taxa_admin_anual)
        fluxo_caixa_com_dropdown = simular_dropdown(valor_projeto, prazo, percentual_lance, taxa_admin_anual, mes_dropdown, percentual_dropdown)

        # Exibição dos resultados
        st.subheader("Resultados")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"Relação parcela/crédito novo: {relacao_parcela_credito:.2f}%")
            st.write(f"Economia estimada: R$ {economia_estimada:,.2f}")
        
        with col2:
            st.write(f"Valor do lance: R$ {valor_projeto * (percentual_lance / 100):,.2f}")
            st.write(f"Crédito novo: R$ {valor_projeto * (1 - percentual_lance / 100):,.2f}")

        # Fluxo de caixa
        st.subheader("Fluxo de Caixa")
        df_fluxo = pd.DataFrame({
            'Mês': range(prazo + 1),
            'Sem Dropdown': fluxo_caixa_sem_dropdown,
            'Com Dropdown': fluxo_caixa_com_dropdown
        })
        st.dataframe(df_fluxo)

        # Gráficos
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12))

        # Gráfico de barras comparando custos
        custo_tradicional = valor_projeto + economia_estimada
        custos = [custo_tradicional, valor_projeto]
        labels = ['Financiamento Tradicional', 'Constructa']
        ax1.bar(labels, custos)
        ax1.set_ylabel('Custo Total (R$)')
        ax1.set_title('Comparação de Custos')
        for i, v in enumerate(custos):
            ax1.text(i, v, f'R$ {v:,.2f}', ha='center', va='bottom')

        # Gráfico de linha mostrando evolução do fluxo de caixa
        ax2.plot(df_fluxo['Mês'], df_fluxo['Sem Dropdown'], label='Sem Dropdown')
        ax2.plot(df_fluxo['Mês'], df_fluxo['Com Dropdown'], label='Com Dropdown')
        ax2.set_xlabel('Mês')
        ax2.set_ylabel('Fluxo de Caixa (R$)')
        ax2.set_title('Evolução do Fluxo de Caixa')
        ax2.legend()

        st.pyplot(fig)

if __name__ == "__main__":
    main()
