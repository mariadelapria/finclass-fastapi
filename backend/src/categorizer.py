import pandas as pd
import unidecode
import re

def categorizar(df, categorias_dict, tipo_movimentacao_dict=None):
    if tipo_movimentacao_dict is None:
        tipo_movimentacao_dict = {}

    if "Description" not in df.columns or "Amount" not in df.columns:
        raise ValueError("O DataFrame precisa conter 'Description' e 'Amount'.")

    prefixos_repetidos = [
        r"(?i)^compra\s+cartao\s+(deb|cred|mc|visa|elo)\s*",
        r"(?i)^pgto\s+cartao\s+(deb|cred|mc|visa|elo)\s*",
        r"(?i)^pagamento\s+de\s+contas\s+itau\s*",
        r"(?i)^lcto\s+inc\s+dupli\s+parcela\s*",
        r"(?i)^compra\s+credito\s*"
    ]

    def limpar_descricao(texto):
        texto = str(texto)
        for padrao in prefixos_repetidos:
            texto = re.sub(padrao, "", texto)
        texto = re.sub(r"\s{2,}", " ", texto).strip()
        return texto

    df["Description"] = df["Description"].fillna("").apply(limpar_descricao)

    df["texto_base"] = (
        df["Description"].fillna('') + " " +
        df.get("Receiver Name", pd.Series([""] * len(df))).fillna('') + " " +
        df.get("Operation Type", pd.Series([""] * len(df))).fillna('')
    ).apply(lambda x: unidecode.unidecode(str(x).lower()))

    df["Operation Type"] = df["Amount"].apply(lambda x: "Entrada" if x > 0 else "Saída")
    df["categoria"] = "Não Classificado"

    regras = []
    for categoria, subcats in categorias_dict.items():
        for subcat, detalhes in subcats.items():
            tipo_permitido = tipo_movimentacao_dict.get(subcat, "Ambos")
            for palavra in detalhes["palavras_chave"]:
                palavra = unidecode.unidecode(palavra.lower().strip())
                if categoria.lower() == "pix":
                    parte_regex = re.escape(palavra).replace(" ", r"[\s\-\:\_]*")
                    regex = parte_regex
                else:
                    regex = rf"\b{re.escape(palavra)}\b"
                regras.append((subcat, regex, tipo_permitido, len(palavra)))

    regras.sort(key=lambda x: x[3], reverse=True)

    for subcat, regex, tipo, _ in regras:
        mask = df["texto_base"].str.contains(regex, na=False, regex=True)
        if tipo == "Entrada":
            mask &= df["Operation Type"] == "Entrada"
        elif tipo == "Saída":
            mask &= df["Operation Type"] == "Saída"

        for i, row in df[mask & df["categoria"].eq("Não Classificado")].iterrows():
            descricao = row["Description"]
            ultimas_palavras = " ".join(descricao.split()[-3:])
            if re.search(regex, unidecode.unidecode(ultimas_palavras.lower())):
                df.at[i, "categoria"] = subcat

        df.loc[df["categoria"].eq("Não Classificado") & mask, "categoria"] = subcat

    df_entradas = df[df["Operation Type"] == "Entrada"].copy()
    df_saidas = df[df["Operation Type"] == "Saída"].copy()
    total_entradas = df_entradas["Amount"].sum()
    total_saidas = df_saidas["Amount"].sum()

    categorias_agrupadas = (
        df.groupby("categoria", dropna=False)[["Description", "Amount", "Operation Type"]]
        .apply(lambda x: x.reset_index(drop=True))
        .reset_index(level=0)
    )

    df_nao_classificado = df[df["categoria"] == "Não Classificado"].copy()

    return {
        "df": df,
        "agrupado": categorias_agrupadas,
        "nao_classificado": df_nao_classificado,
        "entradas": df_entradas,
        "saidas": df_saidas,
        "total_entradas": total_entradas,
        "total_saidas": total_saidas
    }
