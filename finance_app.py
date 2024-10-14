import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from decimal import Decimal, ROUND_HALF_UP

# Configuração da página
st.set_page_config(page_title="Constructa MVP", layout="wide")

# Funções auxiliares
def format_currency(value):
    if isinstance(value, str):
        value = parse_currency(value)
    return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

def parse_currency(value):
    if isinstance(value, (int, float, Decimal)):
        return Decimal(str(value))
    return Decimal(value.replace('R$', '').replace('.', '').replace(',', '.').strip())

def calcular_parcela(valor_credito, prazo_meses, taxa_admin_anual, indice_correcao_anual):
    valor_credito = Decimal(str(valor_credito))
    prazo_meses = Decimal(str(prazo_meses))
    taxa_admin_mensal = Decimal(str(taxa_admin_anual)) / Decimal('12') / Decimal('100')
    indice_correcao_mensal = (Decimal('1') + Decimal(str(indice_correcao_anual))/Decimal('100'))**(Decimal('1')/Decimal('12')) - Decimal('1')
    fator = (indice_correcao_mensal * (1 + indice_correcao_mensal)**prazo_meses) / ((1 + indice_correcao_mensal)**prazo_meses - 1)
    parcela = valor_credito * fator
    parcela += valor_credito * taxa_admin_mensal
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
    return [receitas[i] - despesas[i] for i in range(prazo)]

def gerar_perfil(valor_total, prazo, perfil):
    valor_total = Decimal(str(valor_total))
    prazo = Decimal(str(prazo))
    if perfil == 'Linear':
        return [valor_total / prazo] * int(prazo)
    elif perfil == 'Front-loaded':
        meio = int(prazo) // 2
        return [valor_total * Decimal('0.6') / Decimal(str(meio))] * meio + \
               [valor_total * Decimal('0.4') / (prazo - Decimal(str(meio)))] * (int(prazo) - meio)
    else:  # Back-loaded
        meio = int(prazo) // 2
        return [valor_total * Decimal('0.4') / Decimal(str(meio))] * meio + \
               [valor_total * Decimal('0.6') / (prazo - Decimal(str(meio)))] * (int(prazo) - meio)

def calcular_vpl(fluxo_caixa, taxa_desconto):
    taxa_desconto = Decimal(str(taxa_desconto)) / Decimal('100')
    return sum(Decimal(str(valor)) / (1 + taxa_desconto) ** Decimal(str(i)) for i, valor in enumerate(fluxo_caixa))

# Interface do usuário
st.title("Constructa MVP - Simulador de Consórcio e Fluxo de Caixa")

# Criação de abas
tab1, tab2, tab3 = st.tabs(["Dados do Consórcio", "Dados do Empreendimento", "Simulação de Cenários"])

with tab1:
    st.header("Dados do Consórcio")
    
    col1, col2 = st.columns(2)
    with col1:
        valor_credito = st.text_input("Valor do Crédito", value="R$ 10.000.000,00", 
                                      help="Valor total do crédito do consórcio")
        prazo_meses = st.number_input("Prazo (meses)", min_value=12, max_value=240, value=60, step=12, 
                                      help="Duração total do consórcio em meses")
    with col2:
        taxa_admin_anual = st.number_input("Taxa de Administração Anual (%)", min_value=0.0, value=1.20, step=0.01, 
                                           help="Taxa anual cobrada pela administradora do consórcio")
        indice_correcao_anual = st.number_input("Índice de Correção Anual (%)", min_value=0.0, value=5.0, step=0.1, 
                                                help="Taxa anual de correção do valor da carta de crédito")

    valor_lance = st.text_input("Valor do Lance", value="R$ 2.000.000,00", 
                                help="Valor do lance oferecido para contemplação")

with tab2:
    st.header("Dados do Empreendimento")
    
    col1, col2 = st.columns(2)
    with col1:
        vgv = st.text_input("Valor Geral de Vendas (VGV)", value="R$ 10.000.000,00", 
                            help="Valor total esperado de vendas do empreendimento")
        prazo_empreendimento = st.number_input("Prazo do Empreendimento (meses)", min_value=1, value=24, step=1, 
                                               help="Duração total do empreendimento em meses")
    with col2:
        orcamento = st.text_input("Orçamento", value="R$ 8.000.000,00", 
                                  help="Custo total estimado do empreendimento")
        taxa_desconto_vpl = st.number_input("Taxa de Desconto para VPL (%)", min_value=0.0, value=10.0, step=0.1, 
                                            help="Taxa utilizada para calcular o Valor Presente Líquido")

    col3, col4 = st.columns(2)
    with col3:
        perfil_vendas = st.selectbox("Perfil de Vendas", ['Linear', 'Front-loaded', 'Back-loaded'], 
                                     help="Padrão de distribuição das vendas ao longo do tempo")
    with col4:
        perfil_despesas = st.selectbox("Perfil de Despesas", ['Linear', 'Front-loaded', 'Back-loaded'], 
                                       help="Padrão de distribuição das despesas ao longo do tempo")

with tab3:
    st.header("Simulação de Cenários")
    
    if st.button("Calcular e Simular"):
        try:
            # Processamento dos dados do consórcio
            valor_credito_dec = parse_currency(valor_credito)
            valor_lance_dec = parse_currency(valor_lance)
            parcela = calcular_parcela(valor_credito_dec, prazo_meses, taxa_admin_anual, indice_correcao_anual)
            credito_novo = valor_credito_dec - valor_lance_dec
            relacao_parcela_credito = (parcela / credito_novo) * Decimal('100')

            # Processamento dos dados do empreendimento
            vgv_dec = parse_currency(vgv)
            orcamento_dec = parse_currency(orcamento)
            fluxo_caixa = calcular_fluxo_caixa(vgv_dec, orcamento_dec, prazo_empreendimento, perfil_vendas, perfil_despesas)
            vpl = calcular_vpl(fluxo_caixa, taxa_desconto_vpl)

            # Exibição dos resultados
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Parcela Mensal", format_currency(parcela))
            with col2:
                st.metric("Relação Parcela/Crédito Novo", f"{relacao_parcela_credito:.2f}%")
            with col3:
                st.metric("VPL do Fluxo de Caixa", format_currency(vpl))

            # Gráficos
            fig_saldo = go.Figure()
            meses = list(range(1, prazo_meses + 1))
            saldos = [calcular_saldo_devedor(valor_credito_dec, parcela, taxa_admin_anual, indice_correcao_anual, m) for m in meses]
            fig_saldo.add_trace(go.Scatter(x=meses, y=saldos, mode='lines', name='Saldo Devedor'))
            fig_saldo.update_layout(title="Evolução do Saldo Devedor", xaxis_title="Meses", yaxis_title="Saldo (R$)")
            st.plotly_chart(fig_saldo)

            fig_fluxo = go.Figure()
            fig_fluxo.add_trace(go.Bar(x=list(range(1, prazo_empreendimento + 1)), y=fluxo_caixa, name='Fluxo de Caixa'))
            fig_fluxo.update_layout(title="Fluxo de Caixa do Empreendimento", xaxis_title="Meses", yaxis_title="Valor (R$)")
            st.plotly_chart(fig_fluxo)

            # Tabela de fluxo de caixa
            df_fluxo = pd.DataFrame({
                'Mês': range(1, prazo_empreendimento + 1),
                'Fluxo de Caixa': [format_currency(fc) for fc in fluxo_caixa]
            })
            st.write("Detalhamento do Fluxo de Caixa:")
            st.dataframe(df_fluxo)

        except Exception as e:
            st.error(f"Ocorreu um erro nos cálculos: {str(e)}")

    # Simulação de Dropdown
    st.subheader("Simulação de Dropdown")
    
    if 'dropdowns' not in st.session_state:
        st.session_state.dropdowns = []

    col1, col2, col3 = st.columns(3)
    with col1:
        valor_dropdown = st.text_input("Valor do Dropdown", value="R$ 500.000,00", key="valor_dropdown")
    with col2:
        agio = st.number_input("Ágio (%)", min_value=0.0, value=5.0, step=0.1, key="agio")
    with col3:
        mes_dropdown = st.number_input("Mês do Dropdown", min_value=1, value=12, step=1, key="mes_dropdown")

    if st.button("Adicionar Dropdown"):
        st.session_state.dropdowns.append({
            "valor": parse_currency(valor_dropdown),
            "agio": agio,
            "mes": mes_dropdown
        })

    if st.session_state.dropdowns:
        st.write("Dropdowns Adicionados:")
        for i, dropdown in enumerate(st.session_state.dropdowns):
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            with col1:
                st.write(f"Dropdown {i+1}: {format_currency(dropdown['valor'])}")
            with col2:
                st.write(f"Ágio: {dropdown['agio']}%")
            with col3:
                st.write(f"Mês: {dropdown['mes']}")
            with col4:
                if st.button(f"Remover {i+1}"):
                    st.session_state.dropdowns.pop(i)
                    st.experimental_rerun()

    if st.button("Recalcular com Dropdowns"):
        try:
            saldo_atual = valor_credito_dec
            nova_parcela = parcela
            for dropdown in sorted(st.session_state.dropdowns, key=lambda x: x['mes']):
                saldo_atual = calcular_saldo_devedor(saldo_atual, nova_parcela, taxa_admin_anual, indice_correcao_anual, dropdown['mes'])
                valor_efetivo = dropdown['valor'] * (1 + Decimal(str(dropdown['agio'])) / Decimal('100'))
                saldo_atual = max(saldo_atual - valor_efetivo, Decimal('0'))
                prazo_restante = prazo_meses - dropdown['mes']
                nova_parcela = calcular_parcela(saldo_atual, prazo_restante, taxa_admin_anual, indice_correcao_anual)
            
            st.metric("Nova Parcela após Dropdowns", format_currency(nova_parcela))
            st.metric("Saldo Final", format_currency(saldo_atual))
        except Exception as e:
            st.error(f"Ocorreu um erro no recálculo com dropdowns: {str(e)}")

st.sidebar.info("Constructa MVP - Versão 1.1.0")
