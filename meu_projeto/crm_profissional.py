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
