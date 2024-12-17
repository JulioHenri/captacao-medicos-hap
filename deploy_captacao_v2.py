import pandas as pd
from sqlalchemy import create_engine
import streamlit as st

# Configuração da conexão com SQL Server usando Windows Authentication
HOST = "10.224.8.249"  # IP ou nome do servidor
DATABASE = "BASE_CAPTACAO_backup1"

# Função para conectar e carregar dados do SQL Server
@st.cache_data
def carregar_dados():
    # Conexão com SQL Server via trusted_connection
    engine = create_engine(f"mssql+pyodbc://@{HOST}/{DATABASE}?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server")
    
    # Query consolidando informações da tabela principal
    query = """
    SELECT *
    FROM dbo.TB_BASE_CAPTACAO_MEDICA
    """
    df = pd.read_sql(query, engine)
    return df

# Função de Login
def fazer_login():
    st.title("Login - Sistema de Captação de Médicos")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    
    if st.button("Entrar"):
        if usuario == "timecaptacao" and senha == "senha123":
            # Definir sessão logada
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
    with st.expander("Área de Atuação"):
        area_filtro = st.selectbox("Selecione a área de atuação:", [""] + list(df["ESPECIALIDADES"].dropna().unique()))
    with st.expander("Município"):
        municipio_filtro = st.text_input("Digite a cidade:")
    with st.expander("CRM"):
        crm_filtro = st.text_input("Digite o CRM:")
    with st.expander("UF"):
        uf_filtro = st.selectbox("Selecione a UF:", [""] + list(df["UF"].dropna().unique()))
    with st.expander("Tempo de Carreira"):
        tempo_filtro = st.selectbox("Selecione o tempo de carreira:", [""] + list(df["FX_TEMPO_DE_CARREIRA"].dropna().unique()))
    with st.expander("Telemedicina"):
        telemedicina_filtro = st.selectbox("Atua com telemedicina?", ["", "Sim", "Não"])

    # Aplicar filtros
    resultado = df.copy()
    if nome_filtro:
        resultado = resultado[resultado["NOME"].str.contains(nome_filtro, case=False, na=False)]
    if area_filtro:
        resultado = resultado[resultado["ESPECIALIDADES"] == area_filtro]
    if municipio_filtro:
        resultado = resultado[resultado["CIDADE"].str.contains(municipio_filtro, case=False, na=False)]
    if crm_filtro:
        resultado = resultado[resultado["CRM"].str.contains(crm_filtro, case=False, na=False)]
    if uf_filtro:
        resultado = resultado[resultado["UF"] == uf_filtro]
    if tempo_filtro:
        resultado = resultado[resultado["FX_TEMPO_DE_CARREIRA"] == tempo_filtro]
    if telemedicina_filtro:
        resultado = resultado[resultado["ATUA_COM_TELEMEDICINA"] == telemedicina_filtro]

    # Exibir resultados limitados com scroll
    st.subheader("Resultados da Busca")
    st.write(f"Total de registros encontrados: {len(resultado)}")

    # Limitar a exibição a 100 registros e permitir scroll vertical
    st.markdown(
        resultado.head(100).to_html(index=False, classes="table table-striped", escape=False),
        unsafe_allow_html=True
    )
    st.caption("Exibindo até 100 registros. Use os filtros para refinar os resultados.")

# Gerenciamento de Sessão
if "logado" not in st.session_state:
    st.session_state["logado"] = False

# Verificar login e exibir a tela correta
if not st.session_state["logado"]:
    fazer_login()
else:
    tela_filtros()
