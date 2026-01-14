import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import date

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sistema de Agendamento", layout="centered")

# --- CONEXÃO COM O GOOGLE SHEETS (HÍBRIDA) ---
def conectar_google_sheets():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # Lógica Inteligente:
    # 1. Tenta pegar os segredos da Nuvem (Streamlit Cloud)
    if "gcp_service_account" in st.secrets:
        creds_dict = st.secrets["gcp_service_account"]
        credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    
    # 2. Se não achar na nuvem, tenta pegar o arquivo local (No seu PC)
    else:
        credentials = Credentials.from_service_account_file("credentials.json", scopes=scopes)
    
    gc = gspread.authorize(credentials)
    sheet = gc.open("sistema_cadastros").sheet1
    return sheet

try:
    sheet = conectar_google_sheets()
except Exception as e:
    st.error(f"Erro ao conectar. Verifique se:\n1. O arquivo 'credentials.json' está na pasta.\n2. O e-mail do robô foi adicionado como Editor na planilha.\n3. O nome da planilha é exatamente 'sistema_cadastros'.\n\nErro detalhado: {e}")
    st.stop()

st.title("🏥 Agendamento e Triagem")

# Abas para separar Cadastro de Visualização
aba_cadastro, aba_busca = st.tabs(["📝 Novo Agendamento", "🔍 Consultar Agenda"])

# --- ABA DE CADASTRO ---
with aba_cadastro:
    with st.form(key='form_agendamento', clear_on_submit=True):
        nome = st.text_input("Nome do Paciente")
        
        col1, col2 = st.columns(2)
        data_atendimento = col1.date_input("Data do Atendimento", value=date.today(), format="DD/MM/YYYY")
        data_formatada = data_atendimento.strftime("%d/%m/%Y")
        
        profissional = col2.selectbox("Profissional", ["Enfermeira", "Médico", "Psicólogo", "Dentista", "Outro"])
        
        telefone = st.text_input("Telefone")
        observacao = st.text_area("Observação / Motivo")
        
        submit_button = st.form_submit_button(label='Salvar Agendamento')
        
        if submit_button:
            if nome:
                dados = [nome, data_formatada, profissional, observacao, telefone]
                with st.spinner('Salvando no Google Sheets...'):
                    sheet.append_row(dados)
                st.success(f"✅ {nome} agendado com sucesso!")
            else:
                st.warning("⚠️ O nome do paciente é obrigatório.")

# --- ABA DE BUSCA ---
with aba_busca:
    st.header("Agenda")
    
    if st.button("🔄 Atualizar Lista"):
        dados_sheet = sheet.get_all_records()
        
        if dados_sheet:
            df = pd.DataFrame(dados_sheet)
            filtro = st.text_input("Filtrar por nome ou profissional:")
            if filtro:
                df = df[df.astype(str).apply(lambda x: x.str.contains(filtro, case=False)).any(axis=1)]
            st.dataframe(df, use_container_width=True)
        else:

            st.info("A planilha está vazia.")

