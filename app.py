import streamlit as st
import sqlite3
import pandas as pd


def carregar_dados_paginados(tabela, offset, limite, semestre=None, produto=None):
    """Executa query SQL dinâmica para buscar dados filtrados e paginados."""
    conn = sqlite3.connect("data/database.sqlite")

    query = f"SELECT * FROM {tabela}"
    filtros = []

    if tabela in ["turmas", "alunos_turma"]:
        if semestre:
            filtros.append(f"SEMESTRE = '{semestre}'")
        if produto:
            filtros.append(f"PRODUTO = '{produto}'")

    if filtros:
        query += " WHERE " + " AND ".join(filtros)

    query += f" LIMIT {limite} OFFSET {offset}"

    df = pd.read_sql(query, conn)
    conn.close()
    return df


def carregar_clusters_turmas(semestre=None, produto=None):
    """
    Busca a quantidade de alunos por turma e agrupa em clusters.
    Inclui WHERE para SEMESTRE e PRODUTO, unindo alunos_turma + turmas.
    """
    conn = sqlite3.connect("data/database.sqlite")

    query = """
        SELECT t.NUM_SEQ_TURMA,
               COUNT(a.COD_MATRICULA) as QTD_ALUNOS
        FROM alunos_turma a
        JOIN turmas t ON a.NUM_SEQ_TURMA = t.NUM_SEQ_TURMA
    """

    filtros = []
    if semestre:
        filtros.append(f"t.SEMESTRE = '{semestre}'")
    if produto:
        filtros.append(f"t.PRODUTO = '{produto}'")

    if filtros:
        query += " WHERE " + " AND ".join(filtros)

    query += " GROUP BY t.NUM_SEQ_TURMA"

    df = pd.read_sql(query, conn)
    conn.close()

    df["CLUSTER"] = df["QTD_ALUNOS"].apply(
        lambda x: (
            "> 100 alunos"
            if x > 100
            else "> 50 alunos" if x > 50 else "> 20 alunos" if x > 20 else "≤ 20 alunos"
        )
    )

    return df


def carregar_presencialidade(semestre=None, produto=None):
    """
    Analisa os dias presenciais das turmas, verificando TEMPOS_SEG, TEMPOS_TER, etc.
    Agora com possibilidade de filtrar por SEMESTRE e PRODUTO.
    """
    conn = sqlite3.connect("data/database.sqlite")

    query = """
        SELECT t.NUM_SEQ_TURMA,
               t.TEMPOS_SEG, t.TEMPOS_TER, t.TEMPOS_QUA,
               t.TEMPOS_QUI, t.TEMPOS_SEX, t.TEMPOS_SAB, t.TEMPOS_DOM,
               t.SEMESTRE, t.PRODUTO
        FROM turmas t
    """

    filtros = []
    if semestre:
        filtros.append(f"t.SEMESTRE = '{semestre}'")
    if produto:
        filtros.append(f"t.PRODUTO = '{produto}'")

    if filtros:
        query += " WHERE " + " AND ".join(filtros)

    df = pd.read_sql(query, conn)
    conn.close()

    cols_tempos = [
        "TEMPOS_SEG",
        "TEMPOS_TER",
        "TEMPOS_QUA",
        "TEMPOS_QUI",
        "TEMPOS_SEX",
        "TEMPOS_SAB",
        "TEMPOS_DOM",
    ]

    for col in cols_tempos:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    df["QTD_DIAS_PRESENCIAIS"] = df[cols_tempos].gt(0).sum(axis=1)

    return df


def obter_valores_filtro(coluna):
    """Busca valores distintos de uma coluna para o filtro."""
    conn = sqlite3.connect("data/database.sqlite")
    query = f"SELECT DISTINCT {coluna} FROM turmas"
    valores = pd.read_sql(query, conn)[coluna].dropna().unique().tolist()
    conn.close()
    return ["Todos"] + sorted(valores)


st.title("Análises de Turmas e Alunos Yduqs")

tab_tabela, tab_analise = st.tabs(["Tabelas", "Análises"])

with st.sidebar:
    st.header("Filtros")

    valores_semestre = obter_valores_filtro("SEMESTRE")
    filtro_semestre = st.selectbox("Filtrar por SEMESTRE:", valores_semestre)

    valores_produto = obter_valores_filtro("PRODUTO")
    filtro_produto = st.selectbox("Filtrar por PRODUTO:", valores_produto)

    filtro_semestre = None if filtro_semestre == "Todos" else filtro_semestre
    filtro_produto = None if filtro_produto == "Todos" else filtro_produto


def exibir_dataframe(tabela, titulo, page_size=100):
    """Exibe DataFrame paginado dinamicamente do SQLite com filtros (somente para turmas e alunos_turma)."""
    st.subheader(titulo)

    conn = sqlite3.connect("data/database.sqlite")
    query_contagem = f"SELECT COUNT(*) as total FROM {tabela}"

    filtros = []
    if tabela in ["turmas", "alunos_turma"]:
        if filtro_semestre:
            filtros.append(f"SEMESTRE = '{filtro_semestre}'")
        if filtro_produto:
            filtros.append(f"PRODUTO = '{filtro_produto}'")

    if filtros:
        query_contagem += " WHERE " + " AND ".join(filtros)

    total_rows = pd.read_sql(query_contagem, conn)["total"][0]
    conn.close()

    total_pages = max(
        1, total_rows // page_size + (1 if total_rows % page_size > 0 else 0)
    )
    page_number = st.number_input(
        f"Página de {titulo} (1 - {total_pages})",
        min_value=1,
        max_value=total_pages,
        step=1,
    )

    offset = (page_number - 1) * page_size

    df_pagina = carregar_dados_paginados(
        tabela, offset, page_size, filtro_semestre, filtro_produto
    )

    st.write(f"Mostrando {len(df_pagina)} registros de {total_rows} disponíveis")
    st.dataframe(df_pagina.style.hide(axis="index"))


with tab_tabela:
    exibir_dataframe("turmas", "Tabela de Turmas")
    exibir_dataframe("alunos_turma", "Tabela de Alunos x Turma")
    exibir_dataframe("unidades", "Tabela de Unidades")


with tab_analise:
    st.header("Clusters de Turmas por Quantidade de Alunos")

    df_clusters = carregar_clusters_turmas(filtro_semestre, filtro_produto)
    cluster_counts = df_clusters["CLUSTER"].value_counts().reset_index()
    cluster_counts.columns = ["Cluster", "Número de Turmas"]

    st.subheader("Tabela de Clusters")
    st.dataframe(cluster_counts)

    st.subheader("Distribuição das Turmas por Quantidade de Alunos")
    st.bar_chart(cluster_counts.set_index("Cluster"))

    st.header("Presencialidade por Turma")

    df_pres = carregar_presencialidade(filtro_semestre, filtro_produto)

    st.subheader("Tabela de Presencialidade (Turma)")
    st.dataframe(df_pres)

    pres_counts = df_pres["QTD_DIAS_PRESENCIAIS"].value_counts().reset_index()
    pres_counts.columns = ["Dias Presenciais", "Número de Turmas"]

    st.subheader("Distribuição de Turmas por Quantidade de Dias Presenciais")
    st.bar_chart(pres_counts.set_index("Dias Presenciais"))
