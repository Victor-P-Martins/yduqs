import pandas as pd
import sqlite3

conn = sqlite3.connect("data/database.sqlite")

df_alunos_turma = pd.read_sql("SELECT * FROM alunos_turma", conn)
df_turmas = pd.read_sql("SELECT * FROM turmas", conn)
df_unidades = pd.read_sql("SELECT * FROM unidades", conn)

df_turmas["NOM_FANTASIA"].unique()
conn.close()


def carregar_dados_paginados(tabela, offset, limite):
    """Busca apenas os dados necessários da tabela no SQLite."""
    query = f"SELECT * FROM {tabela} LIMIT {limite} OFFSET {offset}"
    return pd.read_sql(query, conn)
