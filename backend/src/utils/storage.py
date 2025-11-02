import pandas as pd

def mover_para_pendentes(df, linha_id, caminho="data/pendentes.xlsx"):
    linha = df.loc[df.index == linha_id]
    df = df.drop(index=linha_id)

    try:
        pendentes = pd.read_excel(caminho)
        pendentes = pd.concat([pendentes, linha])
    except FileNotFoundError:
        pendentes = linha

    pendentes.to_excel(caminho, index=False)
    return df
