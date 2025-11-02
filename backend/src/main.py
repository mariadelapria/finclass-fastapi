from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import pandas as pd
import os
import traceback
from pathlib import Path

from src.categorizer import categorizar
from src.utils.storage import mover_para_pendentes
from src.categories import categorias_dict

app = FastAPI(title="API de Categorização Financeira")

# Caminho persistente do arquivo de dados
DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "data_temp.parquet"
DATA_PATH.parent.mkdir(exist_ok=True, parents=True)


def ler_arquivo(file: UploadFile) -> pd.DataFrame:
    if file.filename.endswith(".csv"):
        df = pd.read_csv(file.file)
    else:
        df = pd.read_excel(file.file)

    df.columns = df.columns.str.strip().str.title()
    rename_map = {
        "Descrição": "Description",
        "Descricao": "Description",
        "Histórico": "Description",
        "Valor": "Amount",
        "Valor (R$)": "Amount",
        "Crédito/Débito": "Operation Type",
        "Tipo": "Operation Type",
        "Nome Do Recebedor": "Receiver Name"
    }
    df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}, inplace=True)

    if "Description" not in df.columns or "Amount" not in df.columns:
        raise ValueError("O arquivo precisa conter as colunas 'Description' e 'Amount'.")

    return df


@app.post("/upload")
async def upload_arquivo(file: UploadFile = File(...)):
    try:
        df = ler_arquivo(file)
        resultado = categorizar(df, categorias_dict)
        df_global = resultado["df"].copy()

        df_global.reset_index(drop=True, inplace=True)
        if "categoria" not in df_global.columns:
            df_global["categoria"] = "Não Classificado"

      
        df_global.to_parquet(DATA_PATH, index=True)

        agrupado = resultado.get("agrupado", pd.DataFrame())
        if agrupado.empty:
            agrupado = df_global.copy()

        return {
            "status": "ok",
            "totais": {
                "entradas": float(resultado.get("total_entradas", 0)),
                "saidas": float(resultado.get("total_saidas", 0))
            },
            "nao_classificado": int(df_global["categoria"].eq("Não Classificado").sum()),
            "categorias": agrupado.to_dict(orient="records")
        }

    except Exception as e:
        traceback.print_exc()
        return JSONResponse(
            content={"erro": f"Falha ao processar arquivo ({type(e).__name__}): {str(e)}"},
            status_code=500
        )


@app.post("/reclassificar")
def reclassificar(linha: dict):
    try:
        if not DATA_PATH.exists():
            return JSONResponse(content={"erro": "Nenhum dado carregado."}, status_code=400)

        df_global = pd.read_parquet(DATA_PATH)

        linha_id = linha.get("id")
        nova_cat = linha.get("nova_categoria")

        if linha_id is None or nova_cat is None:
            return JSONResponse(content={"erro": "Campos obrigatórios ausentes."}, status_code=400)

        if "categoria" not in df_global.columns:
            return JSONResponse(content={"erro": "Coluna 'categoria' não encontrada."}, status_code=500)

        if linha_id < 0 or linha_id >= len(df_global):
            return JSONResponse(content={"erro": f"ID {linha_id} fora do intervalo."}, status_code=404)

        df_global.loc[linha_id, "categoria"] = nova_cat

        df_global.to_parquet(DATA_PATH, index=True)

        return {
            "mensagem": f"Linha {linha_id} reclassificada como '{nova_cat}'.",
            "linha_atualizada": df_global.loc[linha_id].to_dict()
        }

    except Exception as e:
        traceback.print_exc()
        return JSONResponse(
            content={"erro": f"Falha interna ({type(e).__name__}): {str(e)}"},
            status_code=500
        )


@app.get("/categorias")
def listar_categorias():
    if not DATA_PATH.exists():
        return {"erro": "Nenhum arquivo classificado ainda."}
    df = pd.read_parquet(DATA_PATH)
    return df.to_dict(orient="records")


@app.get("/")
def home():
    return JSONResponse(
        content={
            "mensagem": "API de Categorização Financeira está rodando.",
            "docs": "Acesse /docs para ver os endpoints disponíveis."
        }
    )
