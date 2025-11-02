import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

API_UPLOAD_URL = "http://127.0.0.1:8000/upload"
API_RECLASSIFICAR_URL = "http://127.0.0.1:8000/reclassificar"
API_CATEGORIAS_URL = "http://127.0.0.1:8000/categorias"

st.set_page_config(page_title="Dashboard Financeiro", layout="wide")
st.title("Dashboard Financeiro – Classificação Automática")


@st.cache_data(show_spinner=True)
def carregar_extrato(caminho_arquivo):
    if not os.path.exists(caminho_arquivo):
        st.error(f"Arquivo não encontrado: {caminho_arquivo}")
        return None

    try:
        with open(caminho_arquivo, "rb") as f:
            files = {"file": (os.path.basename(caminho_arquivo), f, "application/octet-stream")}
            response = requests.post(API_UPLOAD_URL, files=files)

        if response.status_code != 200:
            try:
                erro_json = response.json()
                st.error(f"Erro: {erro_json.get('erro', 'Falha desconhecida.')}")
            except Exception:
                st.error("Erro desconhecido ao processar a resposta da API.")
            return None

        data = response.json()
        if not data or "categorias" not in data or not isinstance(data["categorias"], list):
            st.error("A API não retornou dados válidos.")
            return None

        df = pd.DataFrame(data["categorias"])
        if df.empty:
            st.warning("Nenhuma transação classificada foi retornada.")
            return None

        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

        if "valor" not in df.columns:
            if "amount" in df.columns:
                df.rename(columns={"amount": "valor"}, inplace=True)
            elif "Valor" in df.columns:
                df.rename(columns={"Valor": "valor"}, inplace=True)
            else:
                df["valor"] = 0

        df["valor"] = pd.to_numeric(df["valor"], errors="coerce").fillna(0)
        return df

    except Exception as e:
        st.error(f"Erro inesperado: {e}")
        return None


def atualizar_dataframe():
    try:
        response = requests.get(API_CATEGORIAS_URL)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                df_novo = pd.DataFrame(data)
                df_novo.columns = df_novo.columns.str.strip().str.lower().str.replace(" ", "_")

                if "valor" not in df_novo.columns:
                    if "amount" in df_novo.columns:
                        df_novo.rename(columns={"amount": "valor"}, inplace=True)
                    else:
                        df_novo["valor"] = 0
                df_novo["valor"] = pd.to_numeric(df_novo["valor"], errors="coerce").fillna(0)

                st.session_state["df"] = df_novo
                return df_novo
        st.warning("Não foi possível atualizar os dados do backend.")
        return st.session_state["df"]
    except Exception as e:
        st.error(f"Erro ao atualizar dados: {e}")
        return st.session_state["df"]

if "df" not in st.session_state:
    st.session_state["df"] = pd.DataFrame()

col1, col2 = st.columns(2)
with col1:
    if st.button("Carregar Extrato 1"):
        df_result = carregar_extrato(os.path.join(DATA_DIR, "extrato1.xlsx"))
        if df_result is not None:
            st.session_state["df"] = df_result
with col2:
    if st.button("Carregar Extrato 2"):
        df_result = carregar_extrato(os.path.join(DATA_DIR, "extrato2.xlsx"))
        if df_result is not None:
            st.session_state["df"] = df_result

df = st.session_state["df"]

if df is not None and hasattr(df, "empty") and not df.empty:
    st.success(f"{len(df)} transações carregadas com sucesso.")

    st.subheader("Consumo por Categoria")

    if "valor" not in df.columns:
        if "amount" in df.columns:
            df.rename(columns={"amount": "valor"}, inplace=True)
        else:
            df["valor"] = 0

    resumo = df.groupby("categoria", dropna=False)["valor"].sum().reset_index()

    fig = px.bar(
        resumo,
        x="categoria",
        y="valor",
        title="Distribuição de Gastos por Categoria",
        color="categoria",
        text_auto=".2s"
    )
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(resumo, use_container_width=True)

    st.markdown("---")
    st.subheader("Transações Classificadas")

    cat_filtro = st.selectbox(
        "Filtrar por Categoria:",
        options=["Todas"] + sorted(df["categoria"].dropna().unique().tolist())
    )

    df_filtrado = df.copy()
    if cat_filtro != "Todas":
        df_filtrado = df[df["categoria"] == cat_filtro]

    st.dataframe(df_filtrado, use_container_width=True, height=400)

    st.markdown("---")
    st.subheader("Reclassificar Transação")

    if not df.empty:
        linha_escolhida = st.selectbox(
            "Escolha a transação:",
            df.apply(lambda x: f"{x.name} — {x['description']} ({x['categoria']})", axis=1)
        )

        categorias_existentes = sorted(df["categoria"].dropna().unique().tolist())
        nova_categoria = st.selectbox("Nova categoria:", categorias_existentes)

        if st.button("Atualizar Categoria"):
            if linha_escolhida and nova_categoria:
                linha_id = int(linha_escolhida.split(" — ")[0])
                payload = {"id": linha_id, "nova_categoria": nova_categoria}

                try:
                    response = requests.post(API_RECLASSIFICAR_URL, json=payload)
                    if response.status_code == 200:
                        msg = response.json().get("mensagem", "Categoria atualizada.")
                        st.success(msg)

                        df_atualizado = atualizar_dataframe()
                        st.session_state["df"] = df_atualizado
                        st.rerun()
                    else:
                        st.error(f"Erro: {response.status_code} - {response.text}")
                except Exception as e:
                    st.error(f"Falha ao comunicar com a API: {e}")
            else:
                st.warning("Escolha uma nova categoria antes de confirmar.")

    st.download_button(
        "Baixar Resultado (CSV)",
        df_filtrado.to_csv(index=False).encode("utf-8"),
        "classificado.csv",
        "text/csv"
    )

else:
    st.info("Escolha um extrato para começar.")
