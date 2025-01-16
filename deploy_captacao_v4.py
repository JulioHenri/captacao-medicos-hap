import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.sql import text
import streamlit as st

# Configuração da conexão com SQL Server usando Windows Authentication
HOST = "10.224.8.249"  # IP ou nome do servidor
DATABASE = "BASE_CAPTACAO_backup1"

# Função para conectar e carregar dados do SQL Server
@st.cache_data
def carregar_dados():
    engine = create_engine(
    "mssql+pyodbc://@spaulo-G8YMM44/BASE_CAPTACAO_backup1?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server"
    )

    
    # Query para tabela principal
    query_medicos = """
    SELECT NOME, CRM, UF, ESPECIALIDADES, TEM_TELEFONE, TEM_DADOS_REDES, TEM_RQE,
           INSTAGRAM, FACEBOOK, LINKEDIN, TWITTER, SITE
    FROM dbo.TB_BASE_CAPTACAO_MEDICA
    """
    df_medicos = pd.read_sql(query_medicos, engine)
    
    # Query para tabela de enriquecimento
    query_enriquecimento = """
    SELECT 
           NOME,
           FIX_1_DDD, FIX_1_NUMERO, FIX_2_DDD, FIX_2_NUMERO, FIX_3_DDD, FIX_3_NUMERO, FIX_4_DDD, FIX_4_NUMERO,
           CEL_1_DDD, CEL_1_NUMERO, CEL_2_DDD, CEL_2_NUMERO, CEL_3_DDD, CEL_3_NUMERO, CEL_4_DDD, CEL_4_NUMERO,
           EMAIL_1, EMAIL_2, EMAIL_3
    FROM dbo.RETORNO_ENRIQUECIMENTO
    """
    df_enriquecimento = pd.read_sql(query_enriquecimento, engine)

    # Combinar as tabelas usando a coluna NOME
    df_combinado = pd.merge(df_medicos, df_enriquecimento, on="NOME", how="left")

    # Substituir valores NULL por "-"
    df_combinado = df_combinado.fillna("-")

    # Agrupar os CRMs por nome do médico para consolidar múltiplos CRMs
    df_combinado = df_combinado.groupby("NOME").agg({
        "CRM": lambda x: ", ".join(x.dropna().unique()),
        "UF": "first",
        "ESPECIALIDADES": "first",
        "TEM_TELEFONE": "first",
        "TEM_DADOS_REDES": "first",
        "TEM_RQE": "first",
        "INSTAGRAM": "first",
        "FACEBOOK": "first",
        "LINKEDIN": "first",
        "TWITTER": "first",
        "SITE": "first",
        "FIX_1_DDD": "first",
        "FIX_1_NUMERO": "first",
        "FIX_2_DDD": "first",
        "FIX_2_NUMERO": "first",
        "FIX_3_DDD": "first",
        "FIX_3_NUMERO": "first",
        "FIX_4_DDD": "first",
        "FIX_4_NUMERO": "first",
        "CEL_1_DDD": "first",
        "CEL_1_NUMERO": "first",
        "CEL_2_DDD": "first",
        "CEL_2_NUMERO": "first",
        "CEL_3_DDD": "first",
        "CEL_3_NUMERO": "first",
        "CEL_4_DDD": "first",
        "CEL_4_NUMERO": "first",
        "EMAIL_1": "first",
        "EMAIL_2": "first",
        "EMAIL_3": "first"
    }).reset_index()

    return df_combinado

# Função para inserir informações adicionais no banco
def inserir_informacoes(nome, informacao):
    try:
        engine = create_engine(f"mssql+pyodbc://@{HOST}/{DATABASE}?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server")
        query = text("INSERT INTO dbo.INFORMACOES_ADICIONAIS (NOME, INFORMACAO) VALUES (:nome, :informacao)")
        with engine.connect() as conn:
            conn.execute(query, {"nome": nome, "informacao": informacao})
        st.success(f"Informação adicional para o médico '{nome}' salva com sucesso!")
    except Exception as e:
        st.error(f"Erro ao salvar informação: {str(e)}")


# Função de Login
def fazer_login():
    st.title("Login - Sistema de Captação de Médicos")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    
    if st.button("Entrar"):
        if usuario == "timecaptacao" and senha == "senha123":
            st.session_state["logado"] = True
            st.success("Login realizado com sucesso!")
        else:
            st.error("Usuário ou senha incorretos. Tente novamente.")

# Tela de Filtros e Resultados
def tela_filtros():
    st.title("Sistema de Captação de Médicos")
    st.write("Utilize os filtros abaixo para buscar médicos com as características desejadas:")

    # Carregar dados do SQL Server
    df = carregar_dados()

    # Filtros interativos
    with st.expander("Nome do Médico"):
        nome_filtro = st.text_input("Digite o nome do médico:")
    with st.expander("CRM"):
        crm_filtro = st.text_input("Digite o CRM:")
    with st.expander("UF"):
        uf_filtro = st.selectbox("Selecione a UF:", [""] + list(df["UF"].unique()))
    with st.expander("Especialidade"):
        especialidade_filtro = st.selectbox("Selecione a Especialidade:", [""] + list(df["ESPECIALIDADES"].unique()))
    with st.expander("Possui Telefone"):
        telefone_filtro = st.radio("O médico possui telefone?", ["", "SIM", "NÃO"])
    with st.expander("Possui Dados de Redes Sociais"):
        redes_filtro = st.radio("O médico possui dados de redes sociais?", ["", "SIM", "NÃO"])
    with st.expander("Possui RQE"):
        rqe_filtro = st.radio("O médico possui RQE?", ["", "SIM", "NÃO"])

    # Aplicar filtros
    resultado = df.copy()
    if nome_filtro:
        resultado = resultado[resultado["NOME"].str.contains(nome_filtro, case=False)]
    if crm_filtro:
        resultado = resultado[resultado["CRM"].str.contains(crm_filtro, case=False)]
    if uf_filtro:
        resultado = resultado[resultado["UF"] == uf_filtro]
    if especialidade_filtro:
        resultado = resultado[resultado["ESPECIALIDADES"] == especialidade_filtro]
    if telefone_filtro:
        resultado = resultado[resultado["TEM_TELEFONE"] == telefone_filtro]
    if redes_filtro:
        resultado = resultado[resultado["TEM_DADOS_REDES"] == redes_filtro]
    if rqe_filtro:
        resultado = resultado[resultado["TEM_RQE"] == rqe_filtro]

    # Número total de registros antes de limitar a 50
    total_registros = len(resultado)

    # Limitar a exibição a 50 resultados
    resultado = resultado.head(50)

    # Exibir resultados em formato de cards
    st.subheader("Resultados da Busca")
    st.write(f"Total de registros encontrados: {total_registros} (mostrando até 50 registros)")

    if total_registros == 0:
        st.info("Nenhum registro encontrado. Ajuste os filtros e tente novamente.")
    else:
        for i, row in resultado.iterrows():
            with st.expander(f"🔍 {row['NOME']}"):
                st.markdown(f"""
                **CRMs:** {row['CRM']}  
                **UF:** {row['UF']}  
                **Especialidade:** {row['ESPECIALIDADES']}  
                **Redes Sociais:** {row['INSTAGRAM']} / {row['FACEBOOK']} / {row['LINKEDIN']} / {row['TWITTER']} / {row['SITE']}  
                """)

                st.write("### Telefones")
                for j in range(1, 5):
                    if row[f"FIX_{j}_DDD"] != "-" and row[f"FIX_{j}_NUMERO"] != "-":
                        st.write(f"📞 Fixo: ({row[f'FIX_{j}_DDD']}) {row[f'FIX_{j}_NUMERO']}")
                    if row[f"CEL_{j}_DDD"] != "-" and row[f"CEL_{j}_NUMERO"] != "-":
                        st.write(f"📱 Celular: ({row[f'CEL_{j}_DDD']}) {row[f'CEL_{j}_NUMERO']}")

                st.write("### Emails")
                for k in range(1, 4):
                    if row[f"EMAIL_{k}"] != "-":
                        st.write(f"✉️ {row[f'EMAIL_{k}']}")

                informacao = st.text_area("Insira a nova informação:", key=f"informacao_{row['NOME']}_{i}")
                if st.button("Salvar Informação", key=f"save_{row['NOME']}_{i}"):
                    inserir_informacoes(row["NOME"], informacao)

# Gerenciamento de Sessão
if "logado" not in st.session_state:
    st.session_state["logado"] = False

# Verificar login e exibir a tela correta
if not st.session_state["logado"]:
    fazer_login()
else:
    tela_filtros()
