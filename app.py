import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import date

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sistema de Agendamento", layout="wide")

# --- CONEXÃO COM O GOOGLE SHEETS ---
def conectar_google_sheets():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    if "gcp_service_account" in st.secrets:
        creds_dict = st.secrets["gcp_service_account"]
        credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    else:
        credentials = Credentials.from_service_account_file("credentials.json", scopes=scopes)
    
    gc = gspread.authorize(credentials)
    
    # --- MUDANÇA AQUI: USANDO O ID DA PLANILHA ---
    # Isso blinda o sistema. Ela pode mudar o nome do arquivo que não quebra.
    sheet_id = "1gF6fMQBK9NI8waQbvdMTnZZFrR__4tME6LBt7hTu0gw"
    sheet = gc.open_by_key(sheet_id).sheet1
    return sheet

try:
    sheet = conectar_google_sheets()
except Exception as e:
    st.error(f"Erro de conexão: {e}")
    st.stop()

st.title("🏥 Sistema de Agendamento & Triagem")

aba_cadastro, aba_agenda = st.tabs(["📝 Novo Agendamento", "📅 Consultar e Atualizar Status"])

# ---------------------------------------------------------
# ABA 1: CADASTRO
# ---------------------------------------------------------
with aba_cadastro:
    st.header("Adicionar Paciente")
    
    # LISTA DA EQUIPE (Edite os nomes aqui se quiser)
    lista_equipe = ["Maria", "Enfermeira Plantão", "Secretária", "Outro"]
    
    with st.form(key='form_agendamento'):
        # --- AQUI ESTÁ O CAMPO DA MARIA ---
        # Ele cria um menu para ela selecionar quem é.
        # Se quiser que ela DIGITE, troque 'st.selectbox' por 'st.text_input'
        responsavel = st.selectbox("Quem está agendando?", lista_equipe, key="input_responsavel")
        
        st.divider() 
        
        nome = st.text_input("Nome do Paciente", key="input_nome")
        
        col1, col2 = st.columns(2)
        data_atendimento = col1.date_input("Data do Atendimento", value=date.today(), format="DD/MM/YYYY", key="input_data")
        profissional = col2.selectbox("Profissional", ["Enfermeira", "Médico", "Psicólogo", "Dentista", "Outro"], key="input_profissional")
        
        col3, col4 = st.columns(2)
        telefone = col3.text_input("Telefone", key="input_telefone")
        
        observacao = st.text_area("Observação / Motivo", key="input_obs")
        
        # Função para limpar apenas os campos do paciente, mantendo a Maria selecionada
        def limpar_campos():
            st.session_state.input_nome = ""
            st.session_state.input_telefone = ""
            st.session_state.input_obs = ""

        submit_button = st.form_submit_button(label='Salvar Agendamento', on_click=limpar_campos)
        
        if submit_button:
            if nome:
                status_inicial = "Agendado"
                # Adicionando o responsável e o status na lista
                dados = [
                    nome, 
                    data_atendimento.strftime("%d/%m/%Y"), 
                    profissional, 
                    observacao, 
                    telefone, 
                    responsavel,
                    status_inicial
                ]
                
                with st.spinner('Salvando...'):
                    sheet.append_row(dados)
                
                st.success(f"✅ Agendado com sucesso por {responsavel}!")
            else:
                st.warning("⚠️ O nome do paciente é obrigatório.")

# ---------------------------------------------------------
# ABA 2: CONSULTA
# ---------------------------------------------------------
with aba_agenda:
    st.header("Gerenciamento do Dia")
    
    if st.button("🔄 Atualizar Tabela"):
        st.cache_data.clear()
    
    dados_sheet = sheet.get_all_records()
    
    if dados_sheet:
        df = pd.DataFrame(dados_sheet)
        
        # Configuração das colunas
        config_colunas = {
            "Status": st.column_config.SelectboxColumn(
                "Status",
                options=["Agendado", "Confirmado", "Realizado", "Faltou", "Cancelado"],
                required=True,
                width="medium"
            ),
            "Data": st.column_config.TextColumn("Data", width="small"),
            "Responsavel": st.column_config.TextColumn("Resp.", width="small")
        }

        st.info("💡 Edite o Status na tabela abaixo e clique em Salvar.")
        
        df_editado = st.data_editor(
            df, 
            column_config=config_colunas, 
            use_container_width=True,
            num_rows="fixed",
            hide_index=True
        )
        
        if st.button("💾 Salvar Alterações de Status"):
            with st.spinner("Atualizando planilha..."):
                valores_atualizados = [df_editado.columns.values.tolist()] + df_editado.values.tolist()
                sheet.update(range_name="A1", values=valores_atualizados)
            st.success("Planilha atualizada!")
            st.cache_data.clear() # Força recarregar os dados novos
            
    else:
        st.info("Ainda não há agendamentos cadastrados.")
