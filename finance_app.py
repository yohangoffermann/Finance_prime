import streamlit as st
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

def calcular_vpn(taxa, fluxos):
    return sum(fluxo / (1 + taxa) ** i for i, fluxo in enumerate(fluxos))

def calcular_economia(valor_total, taxa_tradicional, prazo_projeto, fluxo_caixa_constructa):
    taxa_mensal = (1 + taxa_tradicional/100)**(1/12) - 1
    parcela_tradicional = valor_total * (taxa_mensal * (1 + taxa_mensal)**prazo_projeto) / ((1 + taxa_mensal)**prazo_projeto - 1)
    fluxo_tradicional = [-parcela_tradicional] * prazo_projeto
    
    vpn_constructa = calcular_vpn(taxa_mensal, fluxo_caixa_constructa)
    vpn_tradicional = calcular_vpn(taxa_mensal, fluxo_tradicional)
    
    return vpn_tradicional - vpn_constructa  # Economia é a diferença entre os VPNs

def identificar_oportunidades_dropdown(fluxo_caixa, excedente, prazo_projeto, prazo_consorcio, valor_total, percentual_lance):
    oportunidades = []
    saldo_devedor = valor_total * (1 - percentual_lance / 100)
    agio = 0.25  # 25% de ágio

    for mes in range(prazo_projeto):
        if mes > 0 and excedente[mes] > excedente[mes-1] and excedente[mes] > 0:
            valor_disponivel = min(excedente[mes], saldo_devedor * 0.1)  # Limita o dropdown a 10% do saldo devedor
            if valor_disponivel > valor_total * 0.05:  # Só considera dropdowns significativos (> 5% do valor total)
                beneficio = valor_disponivel * agio
                oportunidades.append((mes, valor_disponivel, beneficio))
                saldo_devedor -= valor_disponivel

    return oportunidades

def plot_fluxos_com_oportunidades(fluxo_caixa, excedente, oportunidades):
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    ax1.plot(range(len(fluxo_caixa)), fluxo_caixa, marker='o', color='b', label='Fluxo de Caixa')
    ax1.set_xlabel("Mês")
    ax1.set_ylabel("Fluxo de Caixa (R$)", color='b')
    ax1.tick_params(axis='y', labelcolor='b')

    ax2 = ax1.twinx()
    ax2.plot(range(len(excedente)), excedente, color='r', label='Excedente Acumulado')
    ax2.set_ylabel("Excedente Acumulado (R$)", color='r')
    ax2.tick_params(axis='y', labelcolor='r')

    for mes, valor, _ in oportunidades:
        ax1.axvline(x=mes, color='g', linestyle='--', alpha=0.5)
        ax1.text(mes, ax1.get_ylim()[1], f'Dropdown R${valor:,.0f}', rotation=90, verticalalignment='top')

    fig.tight_layout()
    return fig

def linspace(start, stop, num):
    step = (stop - start) / (num - 1)
    return [start + i * step for i in range(num)]

def gerar_perfil(perfil, valor_total, prazo):
    if perfil == "Uniforme":
        return [valor_total / prazo] * prazo
    elif perfil == "Crescente":
        return linspace(valor_total / (prazo * 1.5), valor_total * 1.5 / prazo, prazo)
    elif perfil == "Concentrado no Fim":
        return [valor_total / (prazo * 2)] * (prazo // 2) + [valor_total * 1.5 / (prazo // 2)] * (prazo - prazo // 2)
    elif perfil == "Concentrado no Início":
        return [valor_total * 1.5 / (prazo // 2)] * (prazo // 2) + [valor_total / (prazo * 2)] * (prazo - prazo // 2)
    elif perfil == "Decrescente":
        return linspace(valor_total * 1.5 / prazo, valor_total / (prazo * 1.5), prazo)

def cumsum(lst):
    total = 0
    result = []
    for value in lst:
        total += value
        result.append(total)
    return result

def main():
    st.set_page_config(page_title="Constructa - Simulador de Crédito Otimizado", layout="wide")
    st.title("Constructa - Simulador de Crédito Otimizado")

    cenario = st.sidebar.selectbox("Escolha um cenário base", ["Personalizado", "Conservador", "Moderado", "Otimista"])

    if cenario == "Conservador":
        default_values = {
            "valor_total": 5000000.0, "prazo_projeto": 48, "prazo_consorcio": 200,
            "percentual_lance": 15.0, "taxa_admin": 1.5, "indice_correcao": 6.0,
            "taxa_tradicional": 14.0, "perfil_receita": "Concentrado no Fim",
            "perfil_despesa": "Concentrado no Início"
        }
    elif cenario == "Moderado":
        default_values = {
            "valor_total": 10000000.0, "prazo_projeto": 54, "prazo_consorcio": 220,
            "percentual_lance": 20.0, "taxa_admin": 1.2, "indice_correcao": 5.0,
            "taxa_tradicional": 12.0, "perfil_receita": "Uniforme",
            "perfil_despesa": "Uniforme"
        }
    elif cenario == "Otimista":
        default_values = {
            "valor_total": 15000000.0, "prazo_projeto": 60, "prazo_consorcio": 240,
            "percentual_lance": 25.0, "taxa_admin": 1.0, "indice_correcao": 4.0,
            "taxa_tradicional": 10.0, "perfil_receita": "Crescente",
            "perfil_despesa": "Decrescente"
        }
    else:
        default_values = {
            "valor_total": 10000000.0, "prazo_projeto": 48, "prazo_consorcio": 220,
            "percentual_lance": 20.0, "taxa_admin": 1.2, "indice_correcao": 5.0,
            "taxa_tradicional": 12.0, "perfil_receita": "Uniforme",
            "perfil_despesa": "Uniforme"
        }

    st.sidebar.header("Parâmetros Essenciais")
    valor_total = input_moeda("Valor Total do Projeto (R$)", value=default_values["valor_total"], key="valor_total")
    prazo_projeto = st.sidebar.slider("Prazo do Projeto (meses)", min_value=36, max_value=60, value=default_values["prazo_projeto"])
    prazo_consorcio = st.sidebar.slider("Prazo do Consórcio (meses)", min_value=180, max_value=240, value=default_values["prazo_consorcio"])
    percentual_lance = st.sidebar.slider("Percentual de Lance (%)", min_value=0.0, max_value=50.0, value=float(default_values["percentual_lance"]), step=0.1)

    mostrar_avancado = st.sidebar.checkbox("Mostrar parâmetros avançados")

    if mostrar_avancado:
        st.sidebar.header("Parâmetros Avançados")
        taxa_admin = st.sidebar.slider("Taxa de Administração Anual (%)", min_value=0.1, max_value=20.0, value=float(default_values["taxa_admin"]), step=0.1)
        indice_correcao = st.sidebar.slider("Índice de Correção Anual (%)", min_value=0.0, max_value=15.0, value=float(default_values["indice_correcao"]), step=0.1)
        taxa_tradicional = st.sidebar.slider("Taxa de Juros Tradicional (% a.a.)", min_value=1.0, max_value=20.0, value=float(default_values["taxa_tradicional"]), step=0.1)
    else:
        taxa_admin = default_values["taxa_admin"]
        indice_correcao = default_values["indice_correcao"]
        taxa_tradicional = default_values["taxa_tradicional"]

    perfil_receita = st.sidebar.selectbox("Perfil de Receitas", ["Uniforme", "Crescente", "Concentrado no Fim"], index=["Uniforme", "Crescente", "Concentrado no Fim"].index(default_values["perfil_receita"]))
    perfil_despesa = st.sidebar.selectbox("Perfil de Despesas", ["Uniforme", "Concentrado no Início", "Decrescente"], index=["Uniforme", "Concentrado no Início", "Decrescente"].index(default_values["perfil_despesa"]))

    receitas = gerar_perfil(perfil_receita, valor_total * 1.3, prazo_projeto)
    despesas = gerar_perfil(perfil_despesa, valor_total * 0.8, prazo_projeto)

    if st.sidebar.button("Calcular"):
        if percentual_lance >= 100:
            st.error("O percentual de lance não pode ser 100% ou maior.")
            return

        fluxo_caixa = simular_fluxo_caixa(valor_total, prazo_projeto, prazo_consorcio, taxa_admin, percentual_lance, indice_correcao, receitas, despesas, [])
        excedente = cumsum(fluxo_caixa)
        economia = calcular_economia(valor_total, taxa_tradicional, prazo_projeto, fluxo_caixa)

        oportunidades_dropdown = identificar_oportunidades_dropdown(fluxo_caixa, excedente, prazo_projeto, prazo_consorcio, valor_total, percentual_lance)

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
            fig = plot_fluxos_com_oportunidades(fluxo_caixa, excedente, oportunidades_dropdown)
            st.pyplot(fig)

        st.header("Oportunidades de Dropdown")
        if oportunidades_dropdown:
            oportunidades_df = pd.DataFrame(oportunidades_dropdown, columns=["Mês", "Valor Sugerido", "Benefício Estimado"])
            oportunidades_df["Valor Sugerido"] = oportunidades_df["Valor Sugerido"].apply(formatar_moeda)
            oportunidades_df["Benefício Estimado"] = oportunidades_df["Benefício Estimado"].apply(formatar_moeda)
            st.table(oportunidades_df)
        else:
            st.write("Não foram identificadas oportunidades
