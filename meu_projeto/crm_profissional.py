# crm_profissional.py - MINI-CRM PARA PROFISSIONAIS LIBERAIS
# --- IMPORTS ---
import streamlit as st
import pandas as pd
import numpy as np
import sqlite3 
import datetime

# =========================================================================
# 1. CONFIGURAÇÃO DE CONEXÃO E CONSTANTES
# =========================================================================

DB_NAME = 'CRM_PROFISSIONAL.db'

# =========================================================================
# 2. FUNÇÃO DE CRIAÇÃO E POPULAÇÃO DO DB (SQLite)
# =========================================================================

@st.cache_resource
def criar_e_popular_sqlite():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. TABELA CLIENTES (Quem?)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Clientes (
            id_cliente INTEGER PRIMARY KEY,
            nome_cliente TEXT NOT NULL,
            contato_principal TEXT,
            data_cadastro DATE NOT NULL
        );
    ''')
    
    # 2. TABELA SESSOES_ATIVIDADES (Quando? Quanto?)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Sessoes_Atividades (
            id_sessao INTEGER PRIMARY KEY,
            id_cliente INTEGER NOT NULL,
            data_servico DATE NOT NULL,
            descricao_servico TEXT,
            valor_cobrado REAL,
            status_pagamento TEXT NOT NULL, 
            FOREIGN KEY (id_cliente) REFERENCES Clientes(id_cliente)
        );
    ''')
    
    # --- POPULANDO DADOS INICIAIS (DEMO) ---
    hoje = datetime.date.today().strftime('%Y-%m-%d')
    
    # Clientes Demo
    clientes_demo = [
        ("Advogado Marcos", "marcos.adv@email.com", hoje),
        ("Psicóloga Ana", "ana.psi@email.com", hoje),
        ("Consultor Pedro", "pedro.consultor@email.com", hoje),
    ]
    cursor.executemany("INSERT OR IGNORE INTO Clientes (nome_cliente, contato_principal, data_cadastro) VALUES (?, ?, ?)", clientes_demo)
    
    # Sessões Demo
    # Assumindo IDs de cliente 1, 2, 3
    sessoes_demo = [
        (1, hoje, "Consulta Inicial - Direito", 350.00, "Pago"),
        (2, hoje, "Sessão Terapia Semanal", 150.00, "Pendente"),
        (3, hoje, "Reunião de Escopo Projeto X", 800.00, "Pago"),
    ]
    cursor.executemany("INSERT OR IGNORE INTO Sessoes_Atividades (id_cliente, data_servico, descricao_servico, valor_cobrado, status_pagamento) VALUES (?, ?, ?, ?, ?)", sessoes_demo)
    
    conn.commit()
    conn.close()
    st.info("✅ Estrutura do Banco de Dados criada e populada com sucesso!")
    
    # Retorna o mapa de clientes para uso na interface
    conn = sqlite3.connect(DB_NAME)
    df_clientes = pd.read_sql_query("SELECT id_cliente, nome_cliente FROM Clientes", conn)
    conn.close()
    return {nome: id for id, nome in df_clientes[['id_cliente', 'nome_cliente']].values}

# =========================================================================
# 3. FUNÇÃO PRINCIPAL DO STREAMLIT (Interface)
# =========================================================================

def main():
    st.set_page_config(layout="wide")
    st.title("💼 Mini-CRM: Gestão de Clientes e Atividades")
    st.markdown("---")

    # Chama a função para criar o DB e obter o mapa de clientes
    cliente_mapa = criar_e_popular_sqlite() 
    
    # Interface inicial de demonstração
    st.header("Visão Geral (Dashboard)")
    st.write(f"Clientes cadastrados: **{len(cliente_mapa)}**")
    
    st.markdown("---")
    
    # Placeholder para a próxima etapa: Cadastrar Clientes
    st.header("Próxima Etapa: Cadastrar Nova Atividade/Sessão")


if __name__ == "__main__":
    main()


# --- FUNÇÃO DE INSERÇÃO DE DADOS ---
def inserir_sessao_no_db(id_cliente, data_servico, descricao, valor, status):
    """Insere um novo registro na tabela Sessoes_Atividades."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO Sessoes_Atividades 
            (id_cliente, data_servico, descricao_servico, valor_cobrado, status_pagamento) 
            VALUES (?, ?, ?, ?, ?)
            """, 
            (id_cliente, data_servico, descricao, valor, status)
        )
        conn.commit()
        st.success("✅ Sessão/Atividade registrada com sucesso!")
        return True
    except Exception as e:
        st.error(f"❌ Erro ao registrar sessão: {e}")
        return False
    finally:
        conn.close()

# --- FUNÇÃO DE INSERÇÃO DE DADOS ---
def inserir_sessao_no_db(id_cliente, data_servico, descricao, valor, status):
    """Insere um novo registro na tabela Sessoes_Atividades."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO Sessoes_Atividades 
            (id_cliente, data_servico, descricao_servico, valor_cobrado, status_pagamento) 
            VALUES (?, ?, ?, ?, ?)
            """, 
            (id_cliente, data_servico, descricao, valor, status)
        )
        conn.commit()
        st.success("✅ Sessão/Atividade registrada com sucesso!")
        return True
    except Exception as e:
        st.error(f"❌ Erro ao registrar sessão: {e}")
        return False
    finally:
        conn.close()

# =========================================================================
# 3. FUNÇÃO PRINCIPAL DO STREAMLIT (Interface)
# =========================================================================

def main():
    st.set_page_config(layout="wide")
    st.title("💼 Mini-CRM: Gestão de Clientes e Atividades")
    st.markdown("---")

    # Chama a função para criar o DB e obter o mapa de clientes
    cliente_mapa_nome = criar_e_popular_sqlite() 
    
    # -------------------------------------------------------------------------
    # ESTRUTURA DE ABAS
    # -------------------------------------------------------------------------
    
    abas = st.tabs(["Dashboard", "Lançamento", "Clientes", "Relatório"])
    tab_dashboard = abas[0]
    tab_lancamento = abas[1]
    tab_clientes = abas[2]
    tab_relatorio = abas[3]

    # --- ABA: DASHBOARD (Placeholder) ---
    with tab_dashboard:
        st.header("📊 Dashboard - Visão Geral")
        st.write(f"Clientes cadastrados: **{len(cliente_mapa_nome)}**")
        st.info("Aqui será exibido o resumo de Faturamento e Pendências.")
        
    # --- ABA: LANÇAMENTO DE SESSÕES ---
    with tab_lancamento:
        st.header("🗓️ Lançamento de Nova Sessão/Atividade")

        # Inverte o mapa para facilitar a busca de ID pelo nome
        cliente_mapa_id = {v: k for k, v in cliente_mapa_nome.items()}
        
        with st.form("form_lancamento_sessao"): 
            col1, col2 = st.columns(2)
            col3, col4, col5 = st.columns(3)
            
            # 1. Seleção do Cliente
            cliente_nome = col1.selectbox(
                'Cliente', 
                options=list(cliente_mapa_nome.keys()), 
                key="sel_cliente_lancamento"
            )
            
            # 2. Data do Serviço
            data_servico = col2.date_input(
                'Data do Serviço', 
                value=datetime.date.today(), 
                key="data_servico_lancamento"
            )
            
            # 3. Valor Cobrado
            valor_cobrado = col3.number_input(
                'Valor Cobrado (R$)', 
                min_value=0.0, 
                step=10.0, 
                value=150.0, 
                key="valor_cobrado_lancamento"
            )
            
            # 4. Status de Pagamento
            status_pagamento = col4.selectbox(
                'Status de Pagamento', 
                options=['Pago', 'Pendente', 'Cancelado'], 
                key="status_pagamento_lancamento"
            )

            # 5. Descrição do Serviço
            descricao = st.text_area(
                'Descrição do Serviço/Conteúdo', 
                key="descricao_lancamento"
            )

            submitted = st.form_submit_button("Registrar Sessão/Atividade")

            if submitted:
                # Obter o ID do cliente selecionado
                id_cliente_selecionado = cliente_mapa_nome.get(cliente_nome)
                
                if id_cliente_selecionado is not None:
                    # Formatar a data para o SQLite
                    data_str = data_servico.strftime("%Y-%m-%d")
                    
                    inserir_sessao_no_db(
                        id_cliente_selecionado, 
                        data_str, 
                        descricao, 
                        valor_cobrado, 
                        status_pagamento
                    )
                    st.experimental_rerun() # Para limpar o formulário
                else:
                    st.error("❌ Cliente não encontrado no sistema.")


    # --- ABA: CLIENTES (Placeholder) ---
    with tab_clientes:
        st.header("👥 Gestão de Clientes")
        st.info("Aqui você poderá cadastrar novos clientes e editar informações.")

    # --- ABA: RELATÓRIO (Placeholder) ---
    with tab_relatorio:
        st.header("📈 Relatórios Financeiros")
        st.info("Aqui você verá relatórios de faturamento, pagamentos pendentes e histórico.")


if __name__ == "__main__":
    main()
