import pandas as pd
import sqlite3

conn = sqlite3.connect("data/database.sqlite")


def carregar_dados():
    print("📥 Carregando os arquivos para o banco de dados SQLite...")

    df_alunos_turma = pd.read_csv(
        "data/AEA_TB_BD_ALUNO_TURMA_24_MODIFICADO.txt", sep=";", encoding="latin1"
    )
    df_turmas = pd.read_csv(
        "data/AEA_TB_BD_REL_TURMA_24_MODIFICADO.txt", sep=";", encoding="latin1"
    )
    df_unidades = pd.read_csv("data/AEA_TB_BD_UNIDADES.csv", sep=";", encoding="latin1")

    for df in [df_alunos_turma, df_turmas]:
        if "NOM_FANTASIA" in df.columns:
            df["SEMESTRE"] = (
                df["NOM_FANTASIA"]
                .astype(str)
                .apply(lambda x: x[:6] if isinstance(x, str) else "")
            )
            df["PRODUTO"] = (
                df["NOM_FANTASIA"]
                .astype(str)
                .apply(lambda x: x.split(" ", 1)[1] if " " in x else "")
            )

    df_alunos_turma.to_sql("alunos_turma", conn, if_exists="replace", index=False)
    df_turmas.to_sql("turmas", conn, if_exists="replace", index=False)
    df_unidades.to_sql("unidades", conn, if_exists="replace", index=False)


if __name__ == "__main__":
    carregar_dados()
