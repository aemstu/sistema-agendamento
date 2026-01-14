# Sistema de Agendamento e Triagem (Serverless)

Este projeto é uma aplicação web desenvolvida para gerenciar agendamentos e triagem de pacientes de forma remota e colaborativa. O sistema utiliza uma arquitetura **Serverless** (sem servidor de banco de dados tradicional), usando o **Google Sheets** como backend para persistência de dados em tempo real.

## Funcionalidades

* **Cadastro Simplificado:** Formulário para inserção de pacientes, data de atendimento, profissional responsável e observações.
* **Banco de Dados em Nuvem:** Todos os dados são salvos instantaneamente em uma planilha do Google Sheets, permitindo fácil exportação e manipulação via Excel/Drive.
* **Consulta em Tempo Real:** Interface de busca para filtrar agendamentos por nome ou profissional.
* **Acesso Mobile:** Interface responsiva (Mobile First) via Streamlit.
* **Reset Automático:** Limpeza automática de campos após submissão para agilidade no atendimento.

## Tecnologias Utilizadas

* **Linguagem:** [Python 3.x](https://www.python.org/)
* **Frontend:** [Streamlit](https://streamlit.io/)
* **Integração/Backend:** [Google Sheets API](https://developers.google.com/sheets/api) & [Google Drive API](https://developers.google.com/drive)
* **Bibliotecas Principais:** `gspread`, `pandas`, `google-auth`

## Arquitetura

O sistema opera no modelo de **Front-end as Code**:
1.  O usuário acessa a aplicação web hospedada no **Streamlit Cloud**.
2.  A aplicação autentica-se no Google Cloud Platform via **Service Account** (Credenciais seguras).
3.  Os dados são enviados (JSON) para a API do Google Sheets.
4.  A planilha é atualizada em tempo real, servindo como "Fonte da Verdade".

## Como rodar localmente

Para rodar este projeto na sua máquina, siga os passos:

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/SEU-USUARIO/sistema-agendamento.git](https://github.com/SEU-USUARIO/sistema-agendamento.git)
    cd sistema-agendamento
    ```

2.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configuração de Credenciais:**
    * Crie um projeto no Google Cloud Platform.
    * Habilite as APIs do Google Sheets e Google Drive.
    * Crie uma Service Account e baixe a chave JSON.
    * Renomeie o arquivo para `credentials.json` e coloque na raiz do projeto.
    * **Importante:** Compartilhe a planilha alvo com o e-mail da Service Account.

4.  **Execute a aplicação:**
    ```bash
    streamlit run app.py
    ```

## Segurança e Deploy

Este projeto está configurado para deploy no **Streamlit Cloud**.
Por motivos de segurança, o arquivo `credentials.json` **NÃO** está incluído no repositório.

Para produção, as credenciais são injetadas via **Secrets Management** (TOML) nas configurações do servidor.

---
Desenvolvido como solução ágil para gestão de clínicas.
