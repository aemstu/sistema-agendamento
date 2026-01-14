import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import date

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sistema de Agendamento", layout="wide") # Mudei para 'wide' para a tabela caber melhor

# --- CONEXÃO COM O GOOGLE SHEETS ---
def conectar_google_sheets():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # Tenta pegar segredos da nuvem ou arquivo local
    if "gcp_service_account" in st.secrets:
        creds_dict = st.secrets["gcp_service_account"]
        credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    else:
        credentials = Credentials.from_service_account_file("credentials.json", scopes=scopes)
    
    gc = gspread.authorize(credentials)
    # Abre a planilha pelo ID ou Nome (se usar ID é mais seguro, mas pelo nome funciona)
    sheet = gc.open("sistema_cadastros").sheet1
    return sheet

# Tenta conectar
try:
    sheet = conectar_google_sheets()
except Exception as e:
    st.error("Erro de conexão com o Google Sheets.")
    st.error(e)
    st.stop()

st.title("🏥 Sistema de Agendamento & Triagem")

# Abas do Sistema
aba_cadastro, aba_agenda = st.tabs(["📝 Novo Agendamento", "📅 Consultar e Atualizar Status"])

# ---------------------------------------------------------
# ABA 1: CADASTRO INTELIGENTE (STICKY)
# ---------------------------------------------------------
with aba_cadastro:
    st.header("Adicionar Paciente")
    
    # LISTA DE RESPONSÁVEIS (Edite aqui os nomes da equipe da Maria)
    lista_equipe = ["Maria", "Enfermeira 2", "Secretária", "Outro"]
    
    with st.form(key='form_agendamento'):
        # Campo 1: Responsável (Vem primeiro e NÃO SERÁ LIMPO)
        responsavel = st.selectbox("Quem está agendando?", lista_equipe, key="input_responsavel")
        
        st.divider() 
        
        # Campos do Paciente (Estes SERÃO limpos)
        nome = st.text_input("Nome do Paciente", key="input_nome")
        
        col1, col2 = st.columns(2)
        # Data padrão hoje
        data_atendimento = col1.date_input("Data do Atendimento", value=date.today(), format="DD/MM/YYYY", key="input_data")
        profissional = col2.selectbox("Profissional", ["Enfermeira", "Médico", "Psicólogo", "Dentista", "Outro"], key="input_profissional")
        
        col3, col4 = st.columns(2)
        telefone = col3.text_input("Telefone", key="input_telefone")
        
        # Observação
        observacao = st.text_area("Observação / Motivo", key="input_obs")
        
        # FUNÇÃO DE LIMPEZA CIRÚRGICA
        def limpar_campos():
            # Limpa tudo, MENOS o responsável e a data
            st.session_state.input_nome = ""
            st.session_state.input_telefone = ""
            st.session_state.input_obs = ""
            # Se quiser que a data volte para "hoje" sempre, descomente a linha abaixo:
            # st.session_state.input_data = date.today()

        # Botão de Envio
        submit_button = st.form_submit_button(label='Salvar Agendamento', on_click=limpar_campos)
        
        if submit_button:
            if nome:
                # Prepara os dados na ordem exata das colunas do Google Sheets
                # Coluna G (Status) entra automaticamente como "Agendado"
                status_inicial = "Agendado"
                
                dados = [
                    nome, 
                    data_atendimento.strftime("%d/%m/%Y"), 
                    profissional, 
                    observacao, 
                    telefone, 
                    responsavel,
                    status_inicial
                ]
                
                with st.spinner('Enviando para o Google Sheets...'):
                    sheet.append_row(dados)
                
                st.success(f"✅ Agendado com sucesso! (Resp: {responsavel})")
            else:
                st.warning("⚠️ O nome do paciente é obrigatório.")

# ---------------------------------------------------------
# ABA 2: CONSULTA E EDIÇÃO DE STATUS
# ---------------------------------------------------------
with aba_agenda:
    st.header("Gerenciamento do Dia")
    
    # Botão para recarregar os dados atuais
    if st.button("🔄 Atualizar Tabela"):
        st.cache_data.clear() # Limpa o cache para forçar pegar dados novos
    
    # Pega os dados
    dados_sheet = sheet.get_all_records()
    
    if dados_sheet:
        df = pd.DataFrame(dados_sheet)
        
        # Configuração da Tabela Editável
        # Aqui definimos que a coluna "Status" vai ser uma caixinha de seleção
        config_colunas = {
            "Status": st.column_config.SelectboxColumn(
                "Status do Paciente",
                options=["Agendado", "Confirmado", "Realizado", "Faltou", "Cancelado"],
                required=True,
                width="medium"
            ),
            "Observacao": st.column_config.TextColumn("Observação", width="large"),
            "Data": st.column_config.TextColumn("Data", width="small")
        }

        # Mostra a tabela editável
        st.info("💡 Dica: Altere o 'Status' diretamente na tabela abaixo e clique em 'Salvar Alterações'.")
        
        df_editado = st.data_editor(
            df, 
            column_config=config_colunas, 
            use_container_width=True,
            num_rows="fixed", # Não permite adicionar linhas por aqui, só editar
            hide_index=True
        )
        
        # Lógica de Salvar as Edições
        # Comparamos se houve mudança. Se clicar no botão, salvamos TUDO de volta.
        # É o método mais seguro para não corromper a planilha.
        if st.button("💾 Salvar Alterações de Status"):
            with st.spinner("Atualizando planilha..."):
                # Transforma o DataFrame editado de volta em lista
                # O gspread precisa de uma lista de listas
                valores_atualizados = [df_editado.columns.values.tolist()] + df_editado.values.tolist()
                
                # Atualiza a planilha inteira (método update é rápido)
                sheet.update(range_name="A1", values=valores_atualizados)
                
            st.success("Planilha atualizada com sucesso!")
            
    else:
        st.info("Ainda não há agendamentos cadastrados.")
