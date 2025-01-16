import pandas as pd
from sqlalchemy import create_engine
import streamlit as st

# Configuração da conexão com SQL Server usando Windows Authentication
HOST = "10.224.8.249"  # IP ou nome do servidor
DATABASE = "BASE_CAPTACAO_backup1"

# Função para conectar e carregar dados do SQL Server
@st.cache_data
def carregar_dados():
    engine = create_engine(f"mssql+pyodbc://@{HOST}/{DATABASE}?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server")
    
    # Query para carregar dados da tabela principal
    query_medicos = """
    SELECT NOME, CRM, UF, ESPECIALIDADES, TEM_TELEFONE, TEM_DADOS_REDES, TEM_RQE,
           INSTAGRAM, FACEBOOK, LINKEDIN, TWITTER, SITE
    FROM dbo.TB_BASE_CAPTACAO_MEDICA
    """
    df_medicos = pd.read_sql(query_medicos, engine)
    
    # Query para carregar dados adicionais (telefones e emails)
    query_enriquecimento = """
    SELECT CRM, 
           FIX_1_DDD, FIX_1_NUMERO, FIX_2_DDD, FIX_2_NUMERO, FIX_3_DDD, FIX_3_NUMERO, FIX_4_DDD, FIX_4_NUMERO,
           CEL_1_DDD, CEL_1_NUMERO, CEL_2_DDD, CEL_2_NUMERO, CEL_3_DDD, CEL_3_NUMERO, CEL_4_DDD, CEL_4_NUMERO,
           EMAIL_1, EMAIL_2, EMAIL_3
    FROM dbo.RETORNO_ENRIQUECIMENTO
    """
    df_enriquecimento = pd.read_sql(query_enriquecimento, engine)
    
    # Combinar dados das duas tabelas
    return pd.merge(df_medicos, df_enriquecimento, on="CRM", how="left")

# Inserir informações adicionais no banco
def inserir_informacoes(crm, informacao):
    engine = create_engine(f"mssql+pyodbc://@{HOST}/{DATABASE}?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server")
    with engine.connect() as conn:
        conn.execute(f"INSERT INTO dbo.INFORMACOES_ADICIONAIS (CRM, INFORMACAO) VALUES ('{crm}', '{informacao}')")
    st.success("Informação adicional salva com sucesso!")

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

    # Aplicar filtros
    resultado = df.copy()
    if nome_filtro:
        resultado = resultado[resultado["NOME"].str.contains(nome_filtro, case=False, na=False)]
    if crm_filtro:
        resultado = resultado[resultado["CRM"].str.contains(crm_filtro, case=False, na=False)]

    # Exibir resultados em formato de cards
    st.subheader("Resultados da Busca")
    st.write(f"Total de registros encontrados: {len(resultado)}")

    if len(resultado) == 0:
        st.info("Nenhum registro encontrado. Ajuste os filtros e tente novamente.")
    else:
        for _, row in resultado.iterrows():
            with st.expander(f"🔍 {row['NOME']} ({row['CRM']})"):
                st.markdown(f"""
                **UF:** {row['UF']}  
                **Especialidade:** {row['ESPECIALIDADES']}  
                **Possui Telefone:** {row['TEM_TELEFONE']}  
                **Possui Dados de Redes:** {row['TEM_DADOS_REDES']}  
                **Possui RQE:** {row['TEM_RQE']}  
                **Redes Sociais:** {row['INSTAGRAM']} / {row['FACEBOOK']} / {row['LINKEDIN']} / {row['TWITTER']} / {row['SITE']}  
                """)

                st.write("### Telefones")
                for i in range(1, 5):
                    if pd.notna(row[f"FIX_{i}_DDD"]) and pd.notna(row[f"FIX_{i}_NUMERO"]):
                        st.write(f"📞 Fixo: ({row[f'FIX_{i}_DDD']}) {row[f'FIX_{i}_NUMERO']}")
                    if pd.notna(row[f"CEL_{i}_DDD"]) and pd.notna(row[f"CEL_{i}_NUMERO"]):
                        st.write(f"📱 Celular: ({row[f'CEL_{i}_DDD']}) {row[f'CEL_{i}_NUMERO']}")
                
                st.write("### Emails")
                for i in range(1, 4):
                    if pd.notna(row[f"EMAIL_{i}"]):
                        st.write(f"✉️ {row[f'EMAIL_{i}']}")

                st.write("### Inserir Informações Adicionais")
                informacao = st.text_area("Insira a nova informação:")
                if st.button("Salvar Informação", key=f"save_{row['CRM']}"):
                    inserir_informacoes(row["CRM"], informacao)

# Gerenciamento de Sessão
if "logado" not in st.session_state:
    st.session_state["logado"] = False

# Verificar login e exibir a tela correta
if not st.session_state["logado"]:
    fazer_login()
else:
    tela_filtros()
