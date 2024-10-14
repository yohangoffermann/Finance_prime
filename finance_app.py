import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

def parse_moeda(valor_str):
    try:
        return float(valor_str.replace('R$', '').replace('.', '').replace(',', '.').strip())
    except ValueError:
        return 0.0

def input_moeda(label, value=0.0, key=None):
    valor_str = st.sidebar.text_input(label, value=formatar_moeda(value), key=key)
    return parse_moeda(valor_str)

def calcular_parcela_consorcio(valor_credito, prazo_total, taxa_admin, percentual_lance, mes, indice_correcao):
    valor_lance = valor_credito * (percentual_lance / 100)
    credito_efetivo = valor_credito - valor_lance
    anos_passados = mes // 12
    valor_corrigido = credito_efetivo * (1 + indice_correcao/100) ** anos_passados
    fundo_comum = valor_corrigido / (prazo_total - mes)
    taxa_admin_valor = valor_credito * (taxa_admin / 100 / 12)  # Taxa de admin sobre o valor total
    return fundo_comum + taxa_admin_valor

def simular_fluxo_caixa(valor_total, prazo_projeto, prazo_consorcio, taxa_admin, percentual_lance, indice_correcao, receitas, despesas, dropdowns):
    lance = valor_total * (percentual_lance / 100)
    fluxo_caixa = [-lance]
    saldo_devedor = valor_total - lance

    for mes in range(1, max(prazo_projeto, prazo_consorcio) + 1):
        parcela = calcular_parcela_consorcio(valor_total, prazo_consorcio, taxa_admin, percentual_lance, mes-1, indice_correcao) if mes <= prazo_consorcio else 0
        receita = receitas[mes-1] if mes <= prazo_projeto else 0
        despesa = despesas[mes-1] if mes <= prazo_projeto else 0
        
        fluxo = receita - despesa - parcela
        
        for drop_mes, drop_valor in dropdowns:
            if mes == drop_mes:
                fluxo += drop_valor
                saldo_devedor -= drop_valor

        fluxo_caixa.append(fluxo)

    return fluxo_caixa

def calcular_economia(valor_total, taxa_tradicional, prazo_projeto, fluxo_caixa_constructa):
    taxa_mensal = (1 + taxa_tradicional/100)**(1/12) - 1
    parcela_tradicional = valor_total * (taxa_mensal * (1 + taxa_mensal)**prazo_projeto) / ((1 + taxa_mensal)**prazo_projeto - 1)
    fluxo_tradicional = [-parcela_tradicional] * prazo_projeto
    
    vpls = []
    for fluxo in [fluxo_caixa_constructa, fluxo_tradicional]:
        vpl = np.npv(taxa_mensal, fluxo)
        vpls.append(vpl)
    
    return vpls[1] - vpls[0]  # Economia é a diferença entre os VPLs

def plot_fluxos(fluxo_caixa, excedente, dropdowns):
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    ax1.plot(range(len(fluxo_caixa)), fluxo_caixa, marker='o', color='b', label='Fluxo de Caixa')
    ax1.set_xlabel("Mês")
    ax1.set_ylabel("Fluxo de Caixa (R$)", color='b')
    ax1.tick_params(axis='y', labelcolor='b')

    ax2 = ax1.twinx()
    ax2.plot(range(len(excedente)), excedente, color='r', label='Excedente Acumulado')
    ax2.set_ylabel("Excedente Acumulado (R$)", color='r')
    ax2.tick_params(axis='y', labelcolor='r')

    for mes, valor in dropdowns:
        ax1.axvline(x=mes, color='g', linestyle='--', alpha=0.5)
        ax1.text(mes, ax1.get_ylim()[1], f'Dropdown R${valor:,.0f}', rotation=90, verticalalignment='top')

    fig.tight_layout()
    return fig

def main():
    st.set_page_config(page_title="Constructa - Simulador de Crédito Otimizado", layout="wide")
    st.title("Constructa - Simulador de Crédito Otimizado")

    st.sidebar.header("Parâmetros do Projeto")
    valor_total = input_moeda("Valor Total do Projeto (R$)", value=1000000.0, key="valor_total")
    prazo_projeto = st.sidebar.slider("Prazo do Projeto (meses)", min_value=12, max_value=240, value=60)
    prazo_consorcio = st.sidebar.slider("Prazo do Consórcio (meses)", min_value=12, max_value=240, value=60)
    percentual_lance = st.sidebar.slider("Percentual de Lance (%)", min_value=0.0, max_value=50.0, value=20.0, step=0.1)
    taxa_admin = st.sidebar.slider("Taxa de Administração Anual (%)", min_value=0.1, max_value=20.0, value=1.2, step=0.1)
    indice_correcao = st.sidebar.slider("Índice de Correção Anual (%)", min_value=0.0, max_value=15.0, value=5.0, step=0.1)
    taxa_tradicional = st.sidebar.slider("Taxa de Juros Tradicional (% a.a.)", min_value=1.0, max_value=20.0, value=12.0, step=0.1)

    st.sidebar.header("Perfil de Receitas do Projeto")
    perfil_receita = st.sidebar.selectbox("Escolha o perfil de receitas", ["Constante", "Crescente", "Concentrado no Fim", "Personalizado"])
    if perfil_receita == "Constante":
        receita_mensal = st.sidebar.number_input("Receita Mensal Estimada (R$)", min_value=0.0, value=50000.0, step=1000.0)
        receitas = [receita_mensal] * prazo_projeto
    elif perfil_receita == "Crescente":
        receita_inicial = st.sidebar.number_input("Receita Inicial Mensal (R$)", min_value=0.0, value=30000.0, step=1000.0)
        receita_final = st.sidebar.number_input("Receita Final Mensal (R$)", min_value=receita_inicial, value=70000.0, step=1000.0)
        receitas = np.linspace(receita_inicial, receita_final, prazo_projeto).tolist()
    elif perfil_receita == "Concentrado no Fim":
        receita_total = st.sidebar.number_input("Receita Total do Projeto (R$)", min_value=0.0, value=valor_total*1.3, step=100000.0)
        meses_finais = st.sidebar.slider("Meses de Concentração das Receitas", min_value=1, max_value=prazo_projeto//2, value=prazo_projeto//4)
        receitas = [0] * (prazo_projeto - meses_finais) + [receita_total / meses_finais] * meses_finais
    else:  # Personalizado
        st.sidebar.write("Insira as receitas para cada trimestre do projeto:")
        receitas_trimestrais = []
        for i in range(prazo_projeto // 3 + (1 if prazo_projeto % 3 else 0)):
            receita = st.sidebar.number_input(f"Receita Trimestral {i+1} (R$)", min_value=0.0, value=150000.0, step=10000.0, key=f"receita_trim_{i}")
            receitas_trimestrais.append(receita)
        receitas = []
        for r in receitas_trimestrais:
            receitas.extend([r/3] * 3)
        receitas = receitas[:prazo_projeto]

    st.sidebar.header("Perfil de Despesas do Projeto")
    perfil_despesa = st.sidebar.selectbox("Escolha o perfil de despesas", ["Constante", "Variável por Fase", "Personalizado"])
    if perfil_despesa == "Constante":
        despesa_mensal = st.sidebar.number_input("Despesa Mensal Estimada (R$)", min_value=0.0, value=30000.0, step=1000.0)
        despesas = [despesa_mensal] * prazo_projeto
    elif perfil_despesa == "Variável por Fase":
        st.sidebar.write("Insira as despesas para cada fase do projeto:")
        despesa_inicial = st.sidebar.number_input("Despesa Mensal Inicial (R$)", min_value=0.0, value=20000.0, step=1000.0)
        despesa_construcao = st.sidebar.number_input("Despesa Mensal Durante Construção (R$)", min_value=0.0, value=50000.0, step=1000.0)
        despesa_final = st.sidebar.number_input("Despesa Mensal Final (R$)", min_value=0.0, value=10000.0, step=1000.0)
        meses_construcao = st.sidebar.slider("Meses de Construção", min_value=1, max_value=prazo_projeto-2, value=prazo_projeto-6)
        despesas = [despesa_inicial] * 3 + [despesa_construcao] * meses_construcao + [despesa_final] * (prazo_projeto - meses_construcao - 3)
    else:  # Personalizado
        st.sidebar.write("Insira as despesas para cada trimestre do projeto:")
        despesas_trimestrais = []
        for i in range(prazo_projeto // 3 + (1 if prazo_projeto % 3 else 0)):
            despesa = st.sidebar.number_input(f"Despesa Trimestral {i+1} (R$)", min_value=0.0, value=100000.0, step=10000.0, key=f"despesa_trim_{i}")
            despesas_trimestrais.append(despesa)
        despesas = []
        for d in despesas_trimestrais:
            despesas.extend([d/3] * 3)
        despesas = despesas[:prazo_projeto]

    st.sidebar.header("Simulação de Dropdowns")
    num_dropdowns = st.sidebar.number_input("Número de Dropdowns", min_value=0, max_value=5, value=1)
    dropdowns = []
    for i in range(num_dropdowns):
        col1, col2 = st.sidebar.columns(2)
        mes = col1.number_input(f"Mês do Dropdown {i+1}", min_value=1, max_value=prazo_projeto, value=min(24*(i+1), prazo_projeto), key=f"mes_{i}")
        valor = col2.number_input(f"Valor do Dropdown {i+1} (R$)", min_value=0.0, value=100000.0, step=10000.0, key=f"valor_{i}")
        dropdowns.append((mes, valor))

    if st.sidebar.button("Calcular"):
        if percentual_lance >= 100:
            st.error("O percentual de lance não pode ser 100% ou maior.")
            return

        fluxo_caixa = simular_fluxo_caixa(valor_total, prazo_projeto, prazo_consorcio, taxa_admin, percentual_lance, indice_correcao, receitas, despesas, dropdowns)
        excedente = np.cumsum(fluxo_caixa)
        economia = calcular_economia(valor_total, taxa_tradicional, prazo_projeto, fluxo_caixa)

        parcela_inicial = calcular_parcela_consorcio(valor_total, prazo_consorcio, taxa_admin, percentual_lance, 0, indice_correcao)
        valor_lance = valor_total * (percentual_lance / 100)
        credito_efetivo = valor_total - valor_lance

        col1, col2 = st.columns(2)
        
        with col1:
            st.header("Resultados")
            st.write(f"Parcela Inicial: {formatar_moeda(parcela_inicial)}")
            st.write(f"Economia Total Estimada: {formatar_moeda(economia)}")
            st.write(f"Valor do Lance: {formatar_moeda(valor_lance)}")
            st.write(f"Crédito Efetivo: {formatar_moeda(credito_efetivo)}")
            st.write(f"Relação Parcela/Crédito Novo: {(parcela_inicial / credito_efetivo) * 100:.2f}%")

        with col2:
            st.header("Fluxo de Caixa e Excedente")
            fig = plot_fluxos(fluxo_caixa, excedente, dropdowns)
            st.pyplot(fig)

        st.header("Detalhamento do Fluxo de Caixa e Excedente")
        df = pd.DataFrame({
            'Mês': range(1, len(fluxo_caixa) + 1),
            'Receitas': receitas + [0] * (len(fluxo_caixa) - len(receitas)),
            'Despesas': despesas + [0] * (len(fluxo_caixa) - len(despesas)),
            'Fluxo de Caixa': [formatar_moeda(valor) for valor in fluxo_caixa],
            'Excedente Acumulado': [formatar_moeda(valor) for valor in excedente]
        })
        st.dataframe(df)

        if parcela_inicial > (valor_total * 0.03):
            st.warning("Atenção: O valor da parcela calculada é relativamente alto em relação ao valor total do projeto. Considere ajustar os parâmetros.")

    st.sidebar.info("Constructa - Versão Piloto")
    st.warning("Atenção: O valor da parcela calculada é relativamente alto em relação ao valor total do projeto. Considere ajustar os parâmetros.")

    st.sidebar.info("Constructa - Versão Piloto")
    st.sidebar.warning("Este é um modelo simplificado para fins de demonstração. Consulte um profissional financeiro para decisões reais.")

if __name__ == "__main__":
    main()
