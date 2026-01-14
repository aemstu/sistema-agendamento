import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import date, time

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
    
    # ID DA PLANILHA (Blindado)
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
    
    with st.form(key='form_agendamento'):
        # Responsável (Fixo)
        responsavel = st.text_input("Quem está agendando?", key="input_responsavel")
        
        st.divider() 
        
        nome = st.text_input("Nome do Paciente", key="input_nome")
        
        # LINHA DE DATA E HORA
        col_data, col_hora = st.columns(2)
        data_atendimento = col_data.date_input("Data", value=date.today(), format="DD/MM/YYYY", key="input_data")
        hora_atendimento = col_hora.time_input("Horário", value=time(8, 0), key="input_hora") # Começa 08:00 por padrão
        
        # LINHA DE PROFISSIONAL E TELEFONE
        col_prof, col_tel = st.columns(2)
        # Lista atualizada
        lista_profissionais = ["Enfermeira", "Médico", "Fisioterapeuta", "Dentista", "Outro"]
        profissional = col_prof.selectbox("Profissional", lista_profissionais, key="input_profissional")
        telefone = col_tel.text_input("Telefone", key="input_telefone")
        
        observacao = st.text_area("Observação / Motivo", key="input_obs")
        
        # FUNÇÃO DE SALVAR MESTRA
        def salvar_formulario():
            v_nome = st.session_state.input_nome
            v_resp = st.session_state.input_responsavel
            v_data = st.session_state.input_data
            v_hora = st.session_state.input_hora
            v_prof = st.session_state.input_profissional
            v_obs = st.session_state.input_obs
            v_tel = st.session_state.input_telefone
            
            if v_nome:
                try:
                    status_inicial = "Agendado"
                    # Ordem das colunas: A, B, C, D, E, F, G, H (Horario)
                    # Mas no append_row você define a ordem dos dados:
                    dados = [
                        v_nome, 
                        v_data.strftime("%d/%m/%Y"), 
                        v_prof, 
                        v_obs, 
                        v_tel, 
                        v_resp,
                        status_inicial,
                        str(v_hora) # Salva o horário na Coluna H
                    ]
                    
                    sheet.append_row(dados)
                    
                    st.success(f"✅ Agendado com sucesso para {v_prof}! (Resp: {v_resp})")
                    
                    # Limpeza
                    st.session_state.input_nome = ""
                    st.session_state.input_telefone = ""
                    st.session_state.input_obs = ""
                    # Data e Hora não limpam para facilitar agendamentos em sequência no mesmo dia
                    
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
            else:
                st.warning("⚠️ O nome do paciente é obrigatório.")

        st.form_submit_button(label='Salvar Agendamento', on_click=salvar_formulario)

# ---------------------------------------------------------
# ABA 2: CONSULTA
# ---------------------------------------------------------
with aba_agenda:
    st.header("Gerenciamento do Dia")
    
    if st.button("🔄 Atualizar Tabela"):
        st.cache_data.clear()
    
    dados_sheet = sheet.get_all_records()
    
    if dados_sheet:
        df_original = pd.DataFrame(dados_sheet)
        
        termo_busca = st.text_input("🔍 Pesquisar Paciente ou Profissional", placeholder="Digite um nome...")
        
        if termo_busca:
            df_visualizacao = df_original[
                df_original.astype(str).apply(lambda x: x.str.contains(termo_busca, case=False)).any(axis=1)
            ]
        else:
            df_visualizacao = df_original

        # Configuração das colunas para visualização bonita
        config_colunas = {
            "Status": st.column_config.SelectboxColumn(
                "Status",
                options=["Agendado", "Confirmado", "Realizado", "Faltou", "Cancelado"],
                required=True,
                width="medium"
            ),
            "Data": st.column_config.TextColumn("Data", width="small"),
            "Horario": st.column_config.TextColumn("Hora", width="small"), # Nova coluna visual
            "Responsavel": st.column_config.TextColumn("Resp.", width="small")
        }

        st.info("💡 Edite o Status na tabela abaixo e clique em Salvar.")
        
        df_editado = st.data_editor(
            df_visualizacao, 
            column_config=config_colunas, 
            use_container_width=True,
            num_rows="fixed",
            hide_index=True
        )
        
        if st.button("💾 Salvar Alterações de Status"):
            with st.spinner("Atualizando planilha..."):
                df_original.update(df_editado)
                valores_atualizados = [df_original.columns.values.tolist()] + df_original.values.tolist()
                sheet.update(range_name="A1", values=valores_atualizados)
            
            st.success("Planilha atualizada com sucesso!")
            st.cache_data.clear()
            
    else:
        st.info("Ainda não há agendamentos cadastrados.")
