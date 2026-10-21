import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Concessionária - Dashboard de Vendas", page_icon="🚗", layout="wide")

# ----------------------------------------------------------------------------
# Dados
# ----------------------------------------------------------------------------
CATALOGO = {
    "Fiat Mobi 1.0": {"categoria": "Hatch", "preco": 72900.00, "estoque": 6},
    "VW Polo 1.0 TSI": {"categoria": "Hatch", "preco": 109900.00, "estoque": 5},
    "Chevrolet Onix Plus": {"categoria": "Sedã", "preco": 99900.00, "estoque": 4},
    "Toyota Corolla XEi": {"categoria": "Sedã", "preco": 169900.00, "estoque": 3},
    "Hyundai Creta Comfort": {"categoria": "SUV", "preco": 139900.00, "estoque": 4},
    "Jeep Compass Sport": {"categoria": "SUV", "preco": 164900.00, "estoque": 3},
    "Fiat Strada Freedom": {"categoria": "Picape", "preco": 125900.00, "estoque": 5},
    "Toyota Hilux SR": {"categoria": "Picape", "preco": 259900.00, "estoque": 2},
}
CORES = ["Branco", "Prata", "Preto", "Cinza", "Vermelho", "Azul"]
TAXA_MENSAL = 0.0149  # juros do financiamento (1,49% a.m.)
ENTRADA_MINIMA = 0.20  # 20% do valor total


def brl(valor: float) -> str:
    """Formata número no padrão brasileiro: R$ 1.234,56"""
    return "R$ " + f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ----------------------------------------------------------------------------
# Estado da sessão
# ----------------------------------------------------------------------------
if "carrinho" not in st.session_state:
    st.session_state.carrinho = []
if "estoque" not in st.session_state:
    st.session_state.estoque = {nome: d["estoque"] for nome, d in CATALOGO.items()}
if "vendas" not in st.session_state:
    st.session_state.vendas = []
if "mensagem" not in st.session_state:
    st.session_state.mensagem = None


def qtd_no_carrinho(modelo: str) -> int:
    return sum(i["Qtd"] for i in st.session_state.carrinho if i["Modelo"] == modelo)


# ----------------------------------------------------------------------------
# Cabeçalho
# ----------------------------------------------------------------------------
st.title("🚗 Dashboard de Vendas - Concessionária")

if st.session_state.mensagem:
    st.success(st.session_state.mensagem)
    st.session_state.mensagem = None

# Indicadores gerais
total_vendido = sum(v["Total"] for v in st.session_state.vendas)
carros_vendidos = sum(v["Qtd"] for v in st.session_state.vendas)
m1, m2, m3 = st.columns(3)
m1.metric("FATURAMENTO", brl(total_vendido))
m2.metric("CARROS VENDIDOS", carros_vendidos)
m3.metric("ESTOQUE TOTAL", sum(st.session_state.estoque.values()))

st.markdown("---")

col1, col2 = st.columns([1, 1], gap="large")

# ----------------------------------------------------------------------------
# Coluna 1 - Seleção de veículos e carrinho
# ----------------------------------------------------------------------------
with col1:
    st.subheader("Seleção de Veículos")

    with st.form("form_veiculo", clear_on_submit=False):
        modelo = st.selectbox("Escolha o Modelo", list(CATALOGO.keys()))
        cor = st.selectbox("Cor", CORES)
        preco_unit = CATALOGO[modelo]["preco"]
        disponivel = st.session_state.estoque[modelo] - qtd_no_carrinho(modelo)
        st.caption(
            f"Categoria: **{CATALOGO[modelo]['categoria']}** | "
            f"Preço: **{brl(preco_unit)}** | Estoque disponível: **{disponivel}**"
        )
        quantidade = st.number_input("Quantidade", min_value=1, value=1, step=1)
        btn_adicionar = st.form_submit_button("Adicionar ao Carrinho", use_container_width=True)

        if btn_adicionar:
            if quantidade > disponivel:
                st.error(f"Estoque insuficiente! Disponível: **{disponivel}** unidade(s).")
            else:
                st.session_state.carrinho.append({
                    "Modelo": modelo,
                    "Cor": cor,
                    "Preço Unit. (R$)": preco_unit,
                    "Qtd": quantidade,
                    "Subtotal (R$)": preco_unit * quantidade,
                })
                st.success(f"**{modelo}** ({cor}) adicionado com sucesso!")

    st.subheader("Carrinho")
    if st.session_state.carrinho:
        df_carrinho = pd.DataFrame(st.session_state.carrinho)
        st.dataframe(
            df_carrinho,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Preço Unit. (R$)": st.column_config.NumberColumn("Preço Unit.", format="R$ %.2f"),
                "Subtotal (R$)": st.column_config.NumberColumn("Subtotal", format="R$ %.2f"),
            },
        )
        if st.button("Limpar Carrinho", use_container_width=True):
            st.session_state.carrinho = []
            st.rerun()
    else:
        st.info("O carrinho está vazio. Adicione um veículo acima.")

# ----------------------------------------------------------------------------
# Coluna 2 - Pagamento e fechamento
# ----------------------------------------------------------------------------
with col2:
    st.subheader("Pagamento e Fechamento")

    total_compra = sum(i["Subtotal (R$)"] for i in st.session_state.carrinho)
    st.metric(label="TOTAL DA VENDA", value=brl(total_compra))
    st.markdown("---")

    forma = st.radio("Forma de Pagamento", ["À vista", "Financiado"], horizontal=True)
    pode_finalizar = False
    detalhe_pagamento = {}

    if total_compra == 0:
        st.warning("Adicione veículos ao carrinho antes de prosseguir com o pagamento.")

    elif forma == "À vista":
        valor_recebido = st.number_input(
            "Valor Recebido do Cliente (R$)",
            min_value=0.0, value=0.0, step=1000.0, format="%.2f",
        )
        if valor_recebido == 0:
            st.info("Aguardando o recebimento do pagamento...")
        elif valor_recebido < total_compra:
            st.error(f"**Valor insuficiente!** Faltam **{brl(total_compra - valor_recebido)}**.")
        else:
            troco = valor_recebido - total_compra
            st.success("**Pagamento Concluído!**")
            if troco > 0:
                st.metric("TROCO A DEVOLVER", brl(troco))
            pode_finalizar = True
            detalhe_pagamento = {"Forma": "À vista", "Pago": valor_recebido, "Detalhe": f"Troco {brl(troco)}"}

    else:  # Financiado
        entrada_min = total_compra * ENTRADA_MINIMA
        entrada = st.number_input(
            f"Entrada (mínimo {brl(entrada_min)})",
            min_value=0.0, value=0.0, step=1000.0, format="%.2f",
        )
        parcelas = st.selectbox("Parcelas", [12, 24, 36, 48, 60], index=2)

        if entrada == 0:
            st.info("Informe o valor da entrada para simular o financiamento.")
        elif entrada < entrada_min:
            st.error(f"**Entrada insuficiente!** A entrada mínima é de {brl(entrada_min)} (20%).")
        elif entrada >= total_compra:
            st.warning("A entrada cobre o valor total. Use a opção **À vista**.")
        else:
            financiado = total_compra - entrada
            parcela = financiado * TAXA_MENSAL / (1 - (1 + TAXA_MENSAL) ** -parcelas)
            total_pago = entrada + parcela * parcelas
            st.success("**Financiamento aprovado!**")
            c1, c2 = st.columns(2)
            c1.metric("VALOR FINANCIADO", brl(financiado))
            c2.metric(f"PARCELA ({parcelas}x)", brl(parcela))
            st.caption(f"Taxa: {TAXA_MENSAL * 100:.2f}% a.m. | Total a pagar: {brl(total_pago)}")
            pode_finalizar = True
            detalhe_pagamento = {
                "Forma": f"Financiado {parcelas}x",
                "Pago": entrada,
                "Detalhe": f"Parcela {brl(parcela)}",
            }

    if pode_finalizar:
        with st.expander("Ver Comprovante da Venda"):
            st.write(f"**Veículos:** {sum(i['Qtd'] for i in st.session_state.carrinho)}")
            for i in st.session_state.carrinho:
                st.write(f"- {i['Qtd']}x {i['Modelo']} ({i['Cor']}): {brl(i['Subtotal (R$)'])}")
            st.write(f"**Total:** {brl(total_compra)}")
            st.write(f"**Pagamento:** {detalhe_pagamento['Forma']}")
            st.write(f"**Valor pago/entrada:** {brl(detalhe_pagamento['Pago'])}")
            st.write(f"**{detalhe_pagamento['Detalhe']}**")

        if st.button("Finalizar Venda e Novo Cliente", type="primary", use_container_width=True):
            agora = datetime.now().strftime("%d/%m/%Y %H:%M")
            for i in st.session_state.carrinho:
                st.session_state.estoque[i["Modelo"]] -= i["Qtd"]
                st.session_state.vendas.append({
                    "Data": agora,
                    "Modelo": i["Modelo"],
                    "Categoria": CATALOGO[i["Modelo"]]["categoria"],
                    "Cor": i["Cor"],
                    "Qtd": i["Qtd"],
                    "Total": i["Subtotal (R$)"],
                    "Pagamento": detalhe_pagamento["Forma"],
                })
            st.session_state.carrinho = []
            st.session_state.mensagem = "Venda finalizada com sucesso!"
            st.rerun()

# ----------------------------------------------------------------------------
# Painel de vendas e estoque
# ----------------------------------------------------------------------------
st.markdown("---")
st.subheader("Painel de Vendas")

g1, g2 = st.columns(2, gap="large")

with g1:
    st.markdown("**Vendas por Categoria (R$)**")
    if st.session_state.vendas:
        df_vendas = pd.DataFrame(st.session_state.vendas)
        st.bar_chart(df_vendas.groupby("Categoria")["Total"].sum())
        with st.expander("Histórico de Vendas"):
            st.dataframe(
                df_vendas,
                use_container_width=True,
                hide_index=True,
                column_config={"Total": st.column_config.NumberColumn("Total", format="R$ %.2f")},
            )
    else:
        st.info("Nenhuma venda registrada ainda.")

with g2:
    st.markdown("**Estoque Atual**")
    df_estoque = pd.DataFrame([
        {"Modelo": n, "Categoria": d["categoria"], "Preço (R$)": d["preco"], "Estoque": st.session_state.estoque[n]}
        for n, d in CATALOGO.items()
    ])
    st.dataframe(
        df_estoque,
        use_container_width=True,
        hide_index=True,
        column_config={"Preço (R$)": st.column_config.NumberColumn("Preço", format="R$ %.2f")},
    )
