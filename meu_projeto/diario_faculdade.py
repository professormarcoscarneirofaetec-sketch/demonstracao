# diario_faculdade.py (DIÁRIO PARA ENSINO SUPERIOR - NOTAS P1/P2/P3 - VERSÃO FINAL FREE)
# --- IMPORTS GERAIS ---
import streamlit as st
import pandas as pd
import numpy as np
import datetime
import os
from datetime import date
import sqlite3 

# REMOÇÃO: Desativamos a lógica de PostgreSQL e SQLAlchemy.
# from sqlalchemy import create_engine, Column, Integer, String, Date, Float
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker

# =========================================================================
# 1. CONFIGURAÇÃO DE CONEXÃO E CONSTANTES
# =========================================================================

# **IMPORTANTE**: A lógica de RENDER_DB_URL foi removida.
DB_NAME = 'diario_faculdade_temp.db' # <--- DB ISOLADO (SQLITE)

# Constantes de regra de negócio (Ensino Superior: Média Ponderada/Simples)
CORTE_FREQUENCIA = 75
NOTA_MINIMA_APROVACAO = 7.0 # Média mínima para aprovação direta (P1+P2+P3)/3
NOTA_MINIMA_EXAME = 4.0     # Média mínima para fazer o Exame Final
NOTA_MINIMA_FINAL = 5.0     # Média mínima (Média + Exame) / 2 para aprovação final

# Dados de exemplo para inicialização do SQLite
diario_de_classe_sup = {
    "Aluno X": {},
    "Aluno Y": {},
    "Aluno Z": {},
}

# REMOÇÃO: Modelos de SQLAlchemy e Conexão foram removidos.
# Base = declarative_base()
# Engine = None 
# Session = None 

# =========================================================================
# 2. FUNÇÕES DE BANCO DE DADOS (Lógica PostgreSQL removida/mockada)
# =========================================================================

# Função de inserção de aula no PostgreSQL foi removida/mockada:
def lancar_aula_e_frequencia_postgres(disciplina, data_aula, conteudo):
    """MOCK: Simula o lançamento no DB principal, mas não faz nada."""
    # Apenas para evitar erros no código que chama esta função
    pass 

# Lógica Premium/Upgrade removida
MP_CHECKOUT_LINK = "https://mpago.la/19wM16s"

def verificar_acesso_premium(email_usuario):
    """MOCK: Sempre retorna True ou False, pois a conexão externa foi removida."""
    # Retornamos True para que o admin sempre veja a aba "Gerenciar Alunos"
    return True

# =========================================================================
# 3. FUNÇÕES DE LÓGICA E BD (SQLite)
# =========================================================================

@st.cache_resource
def criar_e_popular_sqlite():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. CRIAÇÃO DAS TABELAS
    cursor.execute('''CREATE TABLE IF NOT EXISTS Professores (id_professor INTEGER PRIMARY KEY, usuario TEXT UNIQUE NOT NULL, senha TEXT NOT NULL, nome_completo TEXT, is_admin BOOLEAN NOT NULL, data_expiracao DATE);''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS Turmas (id_turma INTEGER PRIMARY KEY, nome_turma TEXT NOT NULL, ano_letivo INTEGER NOT NULL);''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS Alunos (id_aluno INTEGER PRIMARY KEY, nome TEXT NOT NULL, matricula TEXT UNIQUE NOT NULL);''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS Disciplinas (id_disciplina INTEGER PRIMARY KEY, nome_disciplina TEXT UNIQUE NOT NULL);''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS Aulas (id_aula INTEGER PRIMARY KEY, id_turma INTEGER, id_disciplina INTEGER, data_aula DATE NOT NULL, conteudo_lecionado TEXT, FOREIGN KEY (id_turma) REFERENCES Turmas(id_turma), FOREIGN KEY (id_disciplina) REFERENCES Disciplinas(id_disciplina));''')
    # Notas P1, P2, P3 e Final
    cursor.execute('''CREATE TABLE IF NOT EXISTS Notas (id_nota INTEGER PRIMARY KEY, id_aluno INTEGER, id_disciplina INTEGER, tipo_avaliacao TEXT NOT NULL, valor_nota REAL NOT NULL, UNIQUE(id_aluno, id_disciplina, tipo_avaliacao), FOREIGN KEY (id_aluno) REFERENCES Alunos(id_aluno), FOREIGN KEY (id_disciplina) REFERENCES Disciplinas(id_disciplina));''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS Frequencia (id_frequencia INTEGER PRIMARY KEY, id_aula INTEGER, id_aluno INTEGER, presente BOOLEAN NOT NULL, UNIQUE(id_aula, id_aluno), FOREIGN KEY (id_aula) REFERENCES Aulas(id_aula), FOREIGN KEY (id_aluno) REFERENCES Alunos(id_aluno));''')
    conn.commit()

    try:
        cursor.execute("ALTER TABLE Professores ADD COLUMN nome_completo TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass
    
    # --- POPULANDO DADOS DE PROFESSORES ---
    data_expiracao_demo = (datetime.date.today() + datetime.timedelta(days=30)).strftime('%Y-%m-%d')
    cursor.execute("INSERT OR IGNORE INTO Professores (usuario, senha, nome_completo, is_admin, data_expiracao) VALUES (?, ?, ?, ?, ?)", 
                    ("demonstracao", "Teste2026", "Professor Admin FAC", 1, None)) 
    
    demo_users_data = [
        ("demo_fac_a", "Senha123", "Prof. Demo FAC A"),
        ("demo_fac_b", "Senha123", "Prof. Demo FAC B"),
    ]
    for user, pwd, name in demo_users_data:
        cursor.execute("INSERT OR IGNORE INTO Professores (usuario, senha, nome_completo, is_admin, data_expiracao) VALUES (?, ?, ?, ?, ?)", 
                        (user, pwd, name, 0, data_expiracao_demo))
    
    # --- POPULANDO DEMAIS TABELAS ---
    aluno_map = {}; disciplina_map = {}; id_turma_padrao = 2
    cursor.execute("INSERT OR IGNORE INTO Turmas (id_turma, nome_turma, ano_letivo) VALUES (?, ?, ?)", (id_turma_padrao, "Superior 2026/1", 2026))
    
    disciplinas_list = ["Cálculo 1", "Algoritmos", "Física 1", "Química Orgânica", "Comunicação"]
    for i, disc in enumerate(disciplinas_list): 
        cursor.execute("INSERT OR IGNORE INTO Disciplinas (id_disciplina, nome_disciplina) VALUES (?, ?)", (i+1, disc))
    
    alunos_list = list(diario_de_classe_sup.keys())
    for i, aluno in enumerate(alunos_list): 
        cursor.execute("INSERT OR IGNORE INTO Alunos (id_aluno, nome, matricula) VALUES (?, ?, ?)", (i+1, aluno, f"FAC2026{200 + i + 1}"))
    
    cursor.execute("SELECT id_disciplina, nome_disciplina FROM Disciplinas")
    for id_disc, nome_disc in cursor.fetchall(): 
        disciplina_map[nome_disc] = id_disc
    
    cursor.execute("SELECT id_aluno, nome FROM Alunos")
    for id_aluno, nome_aluno in cursor.fetchall(): 
        aluno_map[nome_aluno] = id_aluno

    conn.commit()
    conn.close()
    return aluno_map, disciplina_map


def calcular_media_final(avaliacoes):
    """Calcula média final para Ensino Superior (P1/P2/P3 e Final)."""
    notas_vals = [avaliacoes.get(f"P{i}") for i in range(1, 4)] # P1, P2, P3
    final_val = avaliacoes.get("Final")
    
    notas = [float(val) for val in notas_vals if pd.notna(val) and val is not None]
    
    num_notas = len(notas)
    media_parcial = sum(notas) / 3 if num_notas >= 3 else (sum(notas) / num_notas if num_notas > 0 else 0.0)
    
    nota_final = media_parcial
    situacao_nota = ""
    
    if media_parcial >= NOTA_MINIMA_APROVACAO:
        situacao_nota = "APROVADO"
        nota_final = media_parcial
    
    elif media_parcial >= NOTA_MINIMA_EXAME and num_notas == 3:
        if pd.notna(final_val) and final_val is not None:
            nota_final = (media_parcial + float(final_val)) / 2
            if nota_final >= NOTA_MINIMA_FINAL:
                situacao_nota = "APROVADO (Final)"
            else:
                situacao_nota = "REPROVADO POR NOTA"
        else:
            situacao_nota = "PENDENTE (Exame Final)"
            nota_final = media_parcial
            
    else:
        if num_notas < 3:
            situacao_nota = f"PENDENTE ({num_notas} de 3 Provas)"
        else:
            situacao_nota = "REPROVADO POR NOTA"

    return nota_final, situacao_nota, media_parcial


def lancar_aula_e_frequencia(id_disciplina, data_aula, conteudo):
    """Insere a frequência no DB SQLite temporário."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    id_turma_padrao = 2 # Turma Superior
    try:
        cursor.execute("""INSERT INTO Aulas (id_turma, id_disciplina, data_aula, conteudo_lecionado) VALUES (?, ?, ?, ?)""", (id_turma_padrao, id_disciplina, data_aula, conteudo))
        conn.commit()
        id_aula = cursor.lastrowid
        
        cursor.execute("SELECT id_aluno FROM Alunos")
        alunos_ids = [row[0] for row in cursor.fetchall()]
        
        if not alunos_ids: return

        registros_frequencia = [(id_aula, id_aluno, 1) for id_aluno in alunos_ids]
        cursor.executemany("""INSERT INTO Frequencia (id_aula, id_aluno, presente) VALUES (?, ?, ?)""", registros_frequencia)
        conn.commit()
    except Exception as e:
        st.error(f"❌ Erro ao lançar aula no SQLite (Frequência): {e}")
    finally:
        conn.close()

def inserir_nota_no_db(id_aluno, id_disciplina, tipo_avaliacao, valor_nota):
    if valor_nota is None or valor_nota < 0 or valor_nota > 10.0:
        st.warning("⚠️ Erro: Insira um valor de nota válido (0.0 a 10.0).")
        return
    # Valida se o tipo de avaliação é P1, P2, P3 ou Final
    if tipo_avaliacao not in ['P1', 'P2', 'P3', 'Final']:
        st.error("❌ Erro: Tipo de avaliação inválido para Ensino Superior. Use P1, P2, P3 ou Final.")
        return
        
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("""REPLACE INTO Notas (id_aluno, id_disciplina, tipo_avaliacao, valor_nota) VALUES (?, ?, ?, ?)""", (id_aluno, id_disciplina, tipo_avaliacao, valor_nota))
        conn.commit()
        st.success(f"✅ Nota {tipo_avaliacao} ({valor_nota:.1f}) inserida/atualizada.")
    except Exception as e:
        st.error(f"❌ Erro ao inserir nota: {e}")
    finally: conn.close()

def obter_frequencia_por_aula(id_disciplina, data_aula):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    id_turma_padrao = 2
    cursor.execute("""
        SELECT id_aula FROM Aulas WHERE id_turma = ? AND id_disciplina = ? AND data_aula = ?
    """, (id_turma_padrao, id_disciplina, data_aula)) 
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        return None, "Aula não encontrada para essa data/disciplina."
        
    id_aula = result[0]
    df = pd.read_sql_query(f"""
        SELECT 
            A.nome AS "Aluno", 
            F.id_frequencia,
            F.presente 
        FROM Frequencia F
        JOIN Alunos A ON F.id_aluno = A.id_aluno
        WHERE F.id_aula = {id_aula}
        ORDER BY A.nome;
    """, conn)
    conn.close()
    
    if df.empty:
        return None, f"Nenhum registro de frequência encontrado para a Aula ID: {id_aula}."
        
    df['Status Atual'] = df['presente'].apply(lambda x: 'PRESENTE ✅' if x == 1 else 'FALTA 🚫')
    df['Opção'] = df['id_frequencia'].astype(str) + ' - ' + df['Aluno']
    return df, id_aula


def atualizar_status_frequencia(id_frequencia, novo_status):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE Frequencia SET presente = ? WHERE id_frequencia = ?
        """, (novo_status, id_frequencia))
        conn.commit()
        st.success(f"✅ Status de Presença Atualizado! (ID Frequência: {id_frequencia})")
    except Exception as e:
        st.error(f"❌ Erro ao atualizar frequência: {e}")
    finally:
        conn.close()

def gerar_relatorio_final_completo(): 
    try:
        conn = sqlite3.connect(DB_NAME)
        # BUSCA P1, P2, P3 e Final (Superior)
        query_sql_completa = """
        SELECT A.nome AS "Aluno", D.nome_disciplina AS "Disciplina", 
            MAX(CASE WHEN N.tipo_avaliacao = 'P1' THEN N.valor_nota ELSE NULL END) AS "P1",
            MAX(CASE WHEN N.tipo_avaliacao = 'P2' THEN N.valor_nota ELSE NULL END) AS "P2",
            MAX(CASE WHEN N.tipo_avaliacao = 'P3' THEN N.valor_nota ELSE NULL END) AS "P3",
            MAX(CASE WHEN N.tipo_avaliacao = 'Final' THEN N.valor_nota ELSE NULL END) AS "Exame Final",
            COUNT(CASE WHEN F.presente = 1 THEN 1 ELSE NULL END) AS "Total_Presencas",
            COUNT(AU.id_aula) AS "Total_Aulas"
        FROM Alunos A CROSS JOIN Disciplinas D 
        LEFT JOIN Notas N ON A.id_aluno = N.id_aluno AND D.id_disciplina = N.id_disciplina
        LEFT JOIN Aulas AU ON D.id_disciplina = AU.id_disciplina
        LEFT JOIN Frequencia F ON A.id_aluno = F.id_aluno AND AU.id_aula = F.id_aula
        GROUP BY A.nome, D.nome_disciplina;
        """
        df_relatorio = pd.read_sql_query(query_sql_completa, conn)

    except Exception as e:
        st.error(f"❌ ERRO FATAL na consulta SQL/Pandas. Verifique a estrutura do DB. Mensagem: {e}")
        return

    if df_relatorio.empty:
        st.info("Nenhum dado de aluno/disciplina encontrado no DB para o relatório.")
        return None

    resultados_finais = []
    for index, row in df_relatorio.iterrows():
        total_aulas = row['Total_Aulas'] or 0; total_presencas = row['Total_Presencas'] or 0
        frequencia_percentual = (total_presencas / total_aulas * 100) if total_aulas > 0 else 0
        
        avaliacoes = {"P1": row.get('P1'), "P2": row.get('P2'), "P3": row.get('P3'), "Final": row.get('Exame Final')}
        
        nota_final, situacao_nota, media_parcial = calcular_media_final(avaliacoes)
        situacao_frequencia = "REPROVADO POR FALTA" if frequencia_percentual < CORTE_FREQUENCIA else "APROVADO POR FREQUÊNCIA"

        situacao_final = situacao_nota
        if situacao_frequencia.startswith("REPROVADO"):
            situacao_final = "REPROVADO GERAL 🔴"
        elif situacao_nota.startswith("APROVADO") and situacao_frequencia.startswith("APROVADO"):
            situacao_final = "APROVADO GERAL 🟢"
        elif situacao_nota.startswith("PENDENTE"):
            situacao_final = "PENDENTE ⚠️"

        resultados_finais.append({
            "Aluno": row['Aluno'], "Disciplina": row['Disciplina'],
            "P1": f"{row['P1']:.1f}" if pd.notna(row['P1']) else '-',
            "P2": f"{row['P2']:.1f}" if pd.notna(row['P2']) else '-',
            "P3": f"{row['P3']:.1f}" if pd.notna(row['P3']) else '-',
            "Exame Final": f"{row['Exame Final']:.1f}" if pd.notna(row['Exame Final']) else '-',
            "Média Final": f"{nota_final:.1f}",
            "Frequência (%)": f"{frequencia_percentual:.1f}",
            "Situação Final": situacao_final
        })

    if not resultados_finais: st.info("Nenhum dado encontrado para o relatório.")
    
    st.markdown("### Relatório Final Consolidado")
    df_final = pd.DataFrame(resultados_finais)
    st.dataframe(df_final.set_index(["Aluno", "Disciplina"]), use_container_width=True)
    
    return df_final

def adicionar_aluno_db(nome, matricula):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("""INSERT INTO Alunos (nome, matricula) VALUES (?, ?)""", (nome, matricula))
        conn.commit()
        st.cache_resource.clear() 
        st.success(f"✅ Aluno(a) '{nome}' (Matrícula: {matricula}) adicionado(a) com sucesso!")
        return True
    except sqlite3.IntegrityError:
        st.error(f"❌ Erro: Matrícula '{matricula}' já existe no sistema.")
        return False
    except Exception as e:
        st.error(f"❌ Erro ao adicionar aluno: {e}")
        return False
    finally:
        conn.close()

def remover_aluno_db(id_aluno, nome_aluno):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        # Ações de DELETAR CASCATA: Notas, Frequência, e depois o Aluno.
        cursor.execute("DELETE FROM Notas WHERE id_aluno = ?", (id_aluno,))
        cursor.execute("DELETE FROM Frequencia WHERE id_aluno = ?", (id_aluno,))
        
        cursor.execute("DELETE FROM Alunos WHERE id_aluno = ?", (id_aluno,))
        conn.commit()
        st.cache_resource.clear() 
        st.success(f"🗑️ Aluno(a) '{nome_aluno}' e seus dados foram removidos com sucesso.")
        return True
    except Exception as e:
        st.error(f"❌ Erro ao remover aluno: {e}")
        return False
    finally:
        conn.close()

def do_logout():
    st.session_state['user_login_name'] = None
    st.session_state['is_restricted'] = None
    st.session_state.pop('df_chamada', None)
    st.session_state.pop('msg_chamada', None)
    st.rerun()

# =========================================================================
# 6. FUNÇÃO PRINCIPAL DO STREAMLIT (Interface)
# =========================================================================

def main():
    # 1. CONFIGURAÇÃO DA PÁGINA
    st.set_page_config(layout="wide") 
    st.title("📚 Diário de Classe Interativo - Ensino Superior (Provas e Final)") 
    st.markdown("---") 

    st.sidebar.title("Login")

    if 'user_login_name' not in st.session_state: st.session_state['user_login_name'] = None 
    if 'is_restricted' not in st.session_state: st.session_state['is_restricted'] = None 

    # >>> INICIALIZAÇÃO DA SESSÃO DE FREQUÊNCIA (Layout da Faculdade)
    if 'df_chamada' not in st.session_state: st.session_state['df_chamada'] = None
    if 'id_aula' not in st.session_state: st.session_state['id_aula'] = None
    if 'msg_chamada' not in st.session_state: st.session_state['msg_chamada'] = None
    # <<< FIM DA CORREÇÃO CRÍTICA

    is_admin = False
    is_expired = True
    data_expiracao = None
    login_successful = False

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    aluno_map_nome, disciplina_map_nome = criar_e_popular_sqlite() 
    
    # 🚨 Formulário de Login na Sidebar
    
    if st.session_state.user_login_name is None:
        with st.sidebar.form("login_form_fac"): 
            username = st.text_input("Usuário", key="user_input_fac")
            password = st.text_input("Senha", type="password", key="pwd_input_fac") 
            submitted = st.form_submit_button("Entrar") # <-- BOTÃO DE ENTRAR NA SIDEBAR

    # 5. PORTÃO DE LOGIN COM VERIFICAÇÃO DE EXPIRAÇÃO
        if submitted:
            cursor.execute("SELECT usuario, senha, nome_completo, is_admin, data_expiracao FROM Professores WHERE usuario = ? AND senha = ?", (username, password))
            user_data = cursor.fetchone()
            
            if user_data:
                user, pwd, nome_completo_db, is_admin_db, data_expiracao_str = user_data
                
                is_admin = bool(is_admin_db)
                login_successful = True
                
                st.session_state.user_login_name = username
                st.session_state.user_full_name = nome_completo_db
                
                # --- ATRIBUIÇÃO DE ID DE USUÁRIO PARA ISOLAMENTO (PostgreSQL mockado) ---
                if username == "demonstracao": st.session_state['usuario_id'] = 1
                elif username == "demo_fac_a": st.session_state['usuario_id'] = 2 
                elif username == "demo_fac_b": st.session_state['usuario_id'] = 3
                else: st.session_state['usuario_id'] = 99 

                if is_admin: st.session_state.is_restricted = False; is_expired = False
                else:
                    if data_expiracao_str:
                        data_expiracao = datetime.date.fromisoformat(data_expiracao_str)
                        data_hoje = datetime.date.today()
                        
                        if data_hoje <= data_expiracao: st.session_state.is_restricted = False; is_expired = False
                        else: st.session_state.is_restricted = True; is_expired = True
                    else: st.session_state.is_restricted = True
                
                st.rerun() 
            else:
                  st.sidebar.error("Usuário ou senha incorretos.")

    conn.close()

    # 3. LÓGICA DE LOGIN BEM-SUCEDIDO (Verifica o estado da sessão)
    if st.session_state.user_login_name is not None:
        
        # Recarrega dados de status para exibição
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT nome_completo, is_admin, data_expiracao FROM Professores WHERE usuario = ?", (st.session_state.user_login_name,))
        user_data_reloaded = cursor.fetchone()
        conn.close()
        
        if user_data_reloaded:
            nome_exibicao, is_admin_db, data_expiracao_str = user_data_reloaded
            is_admin = bool(is_admin_db)
            
            is_expired = True
            if is_admin: is_expired = False
            elif data_expiracao_str:
                 data_expiracao = datetime.date.fromisoformat(data_expiracao_str)
                 data_hoje = datetime.date.today()
                 if data_hoje <= data_expiracao: is_expired = False
            
            
            # MENSAGENS DE STATUS NA BARRA LATERAL
            if is_admin: st.sidebar.success(f"Login bem-sucedido! Bem-vindo, {nome_exibicao} (Admin).")
            elif is_expired:
                data_expiracao_formatada = data_expiracao.strftime('%d/%m/%Y') if data_expiracao else 'N/A'
                st.sidebar.warning(f"Seu acesso total expirou em {data_expiracao_formatada}. Acesso Restrito Ativo.")
            else:
                dias_restantes = (data_expiracao - datetime.date.today()).days
                st.sidebar.success(f"Login bem-sucedido! Acesso total por mais {dias_restantes} dias.")
            
            # BOTÃO DE SAIR
            st.sidebar.button("🚪 Sair / Logout", on_click=do_logout, key="logout_fac") 
            
            # ** LÓGICA DE PREMIUM (BOTÃO DE UPGRADE - APENAS MOCKADO) **
            # A CONEXÃO FOI REMOVIDA, APENAS O VISUAL PERMANECE
            st.sidebar.markdown("---")
            st.sidebar.header("Status da Conta Premium")
            
            # Se for admin, assume acesso total para exibir a aba "Gerenciar Alunos"
            if is_admin:
                st.sidebar.success("✅ Você é Premium! Todos os recursos liberados.")
            else:
                st.sidebar.warning("🔒 Acesso Básico. Faça Upgrade para liberar tudo.")
                st.sidebar.markdown(
                    f"""
                    <a href="{MP_CHECKOUT_LINK}" target="_blank">
                        <button style="background-color: #009ee3; color: white; padding: 10px 20px; border-radius: 5px; border: none; font-weight: bold;">
                            Fazer Upgrade para Premium!
                        </button>
                    </a>
                    """,
                    unsafe_allow_html=True
                )
            
            # APLICAÇÃO DA LIMITAÇÃO DE USO (AVISO LATERAL) 
            if st.session_state.is_restricted:
                st.sidebar.warning("⚠️ **Aviso Demo:** A modificação de dados existentes está bloqueada.")
                st.sidebar.info("Apenas a criação e visualização são permitidas.")
                
            # 1. CONTINUAÇÃO DA INICIALIZAÇÃO DO DB e Persistência
            aluno_map_id = {v: k for k, v in aluno_map_nome.items()}
            disciplina_map_id = {v: k for v, k in disciplina_map_nome.items()}

            # -------------------------------------------------------------------------
            # 6. ESTRUTURA DE ABAS (TABS) E SEÇÕES DA INTERFACE
            # -------------------------------------------------------------------------

            abas_titles = ["Lançamento", "Frequência", "Notas", "Relatório"]
            
            is_admin_or_unrestricted = not st.session_state.is_restricted
            # A aba "Gerenciar Alunos" agora é exibida se for admin (pela função mockada acima)
            if is_admin_or_unrestricted:
                abas_titles.append("Gerenciar Alunos")

            abas = st.tabs(abas_titles)
            
            tab_lancamento = abas[0]
            tab_frequencia = abas[1]
            tab_notas = abas[2]
            tab_relatorio = abas[3]
            tab_gerenciar_alunos = abas[4] if len(abas) > 4 else None

            # =========================================================================
            # ABA: LANÇAMENTO DE AULAS (AGORA SÓ USA SQLITE)
            # =========================================================================
            with tab_lancamento:
                st.header("🗓️ Lançamento de Aulas (Liberado)")
                with st.form("form_aulas_fac"): 
                    col1, col2, col3 = st.columns(3)
                    
                    disciplina_aula_nome = col1.selectbox('Disciplina', options=list(disciplina_map_nome.keys()), key="tab_disc_aula_fac") 
                    data_input = col2.date_input('Data', value=datetime.date.today(), key="tab_data_aula_fac") 
                    conteudo = col3.text_input('Conteúdo da Aula', key="tab_conteudo_aula_fac") 
                    
                    id_disciplina = disciplina_map_nome.get(disciplina_aula_nome)

                    submitted_aula = st.form_submit_button("Lançar Aula e Marcar Todos Presentes")
                    
                    if submitted_aula:
                        # Chamada MOCKADA (não faz mais nada no PostgreSQL)
                        lancar_aula_e_frequencia_postgres(disciplina_aula_nome, data_input, conteudo)
                        
                        # Inserção de registro de frequência no SQLite (O que realmente funciona)
                        lancar_aula_e_frequencia(id_disciplina, data_input.strftime("%Y-%m-%d"), conteudo)
                        st.rerun() 

            # =========================================================================
            # ABA: AJUSTE DE FALTAS (BLOQUEIO CONDICIONAL)
            # =========================================================================
            with tab_frequencia:
                st.header("📋 Ajuste de Faltas Pontuais")
                
                col1, col2 = st.columns(2)
                disciplina_chamada_nome = col1.selectbox('Disciplina (Ajuste)', options=list(disciplina_map_nome.keys()), key="sel_disc_chamada_tab_fac") 
                data_consulta = col2.date_input('Data da Aula (Ajuste)', value=datetime.date.today(), key="data_chamada_tab_fac") 
                
                id_disciplina_chamada = disciplina_map_nome.get(disciplina_chamada_nome)
                
                col_carregar, col_recarregar = st.columns([1, 4])
                
                if col_carregar.button("Carregar Chamada da Aula", key="btn_carregar_chamada_fac"): 
                    df_frequencia_atual, id_aula_ou_erro = obter_frequencia_por_aula(id_disciplina_chamada, data_consulta.strftime("%Y-%m-%d"))
                    
                    if isinstance(df_frequencia_atual, pd.DataFrame):
                        st.session_state['df_chamada'] = df_frequencia_atual
                        st.session_state['id_aula'] = id_aula_ou_erro
                        st.session_state['msg_chamada'] = f"✅ Chamada Carregada (Aula ID: {id_aula_ou_erro})"
                    else:
                        st.session_state['df_chamada'] = None
                        st.session_state['msg_chamada'] = f"❌ ERRO: {id_aula_ou_erro}"
                        
                if 'df_chamada' in st.session_state and st.session_state['df_chamada'] is not None:
                    if col_recarregar.button("Recarregar/Atualizar a Lista", key="btn_recarregar_chamada_fac"): 
                        st.rerun() 
                        
                if 'msg_chamada' in st.session_state:
                    st.markdown(st.session_state['msg_chamada'])
                    if st.session_state['df_chamada'] is not None and not st.session_state['df_chamada'].empty:
                        
                        st.subheader(f"Lista de Alunos e Status (Aula ID: {st.session_state['id_aula']})") 
                        st.dataframe(st.session_state['df_chamada'][['Aluno', 'Status Atual']], hide_index=True)
                        st.markdown("---")

                        st.subheader("Alterar Status (Falta/Presença)")
                        
                        df_chamada = st.session_state['df_chamada']
                        opcoes_ajuste = {row['Aluno']: row['id_frequencia'] for index, row in df_chamada.iterrows()}
                        col_aluno, col_status = st.columns([2, 1])

                        aluno_ajuste = col_aluno.selectbox('Aluno para Ajuste', options=list(opcoes_ajuste.keys()), key="sel_aluno_ajuste_fac") 
                        novo_status_label = col_status.selectbox('Novo Status', options=['PRESENTE', 'FALTA'], key="sel_status_ajuste_fac") 

                        if st.button("Salvar Alteração de Frequência", key="btn_salvar_frequencia_fac"): 
                            
                            if st.session_state.is_restricted: 
                                st.error("❌ A alteração de frequência está bloqueada nesta conta de demonstração (modifica dados existentes).")
                                
                            else:
                                id_frequencia_registro = opcoes_ajuste[aluno_ajuste]
                                novo_status = 1 if novo_status_label == 'PRESENTE' else 0
                                
                                atualizar_status_frequencia(id_frequencia_registro, novo_status)
                                st.info("✅ Atualização salva. Clique em 'Recarregar/Atualizar a Lista' para confirmar.")
                                st.rerun() 

                        if st.session_state.is_restricted:
                            st.markdown("⚠️ **Aviso:** Este botão está desabilitado para contas de demonstração.")
            
            # =========================================================================
            # ABA: LANÇAMENTO DE NOTAS
            # =========================================================================
            with tab_notas:
                st.header("🖊️ Lançamento de Notas (Liberado)")
                with st.form("form_notas_tab_fac"): 
                    col1, col2, col3, col4 = st.columns(4)
                    
                    aluno_nome = col1.selectbox('Aluno(a)', options=list(aluno_map_nome.keys()), key="sel_aluno_nota_fac") 
                    disciplina_nome = col2.selectbox('Disciplina (Nota)', options=list(disciplina_map_nome.keys()), key="disc_nota_tab_fac") 
                    tipo_avaliacao = col3.selectbox('Avaliação', options=['P1', 'P2', 'P3', 'Final'], key="sel_avaliacao_nota_fac") 
                    valor_nota = col4.number_input('Nota (0-10)', min_value=0.0, max_value=10.0, step=0.5, value=7.0, key="input_nota_fac") 
                    
                    id_aluno = aluno_map_nome.get(aluno_nome)
                    id_disciplina = disciplina_map_nome.get(disciplina_nome)

                    submitted_nota = st.form_submit_button("Inserir/Atualizar Nota")

                    if submitted_nota:
                        inserir_nota_no_db(id_aluno, id_disciplina, tipo_avaliacao, valor_nota)
                        st.rerun()

            # =========================================================================
            # ABA: RELATÓRIO CONSOLIDADO
            # =========================================================================
            with tab_relatorio:
                st.header("📊 Relatório Consolidado")
                
                df_relatorio_final = gerar_relatorio_final_completo()
                
                if df_relatorio_final is not None and not df_relatorio_final.empty:
                    st.markdown("---")
                    col_csv, col_spacer = st.columns([1, 4]) 
                    
                    csv_data = df_relatorio_final.to_csv(index=False).encode('utf-8')
                    col_csv.download_button(
                        label="⬇️ Gerar Conteúdo (CSV)",
                        data=csv_data,
                        file_name=f'Relatorio_Diario_Classe_FAC_{datetime.date.today()}.csv', 
                        mime='text/csv',
                        key='download_csv_tab_fac' 
                    )

            # =========================================================================
            # ABA: GERENCIAR ALUNOS (APENAS ADMIN/ILIMITADO)
            # =========================================================================
            
            if tab_gerenciar_alunos:
                with tab_gerenciar_alunos:
                    st.header("⚙️ Gerenciar Cadastro de Alunos")
                    st.markdown("---")
                    
                    # --- SEÇÃO ADICIONAR ALUNO ---
                    st.subheader("➕ Adicionar Novo Aluno")
                    with st.form("form_add_aluno_fac"): 
                        nome_novo = st.text_input("Nome Completo do Novo Aluno")
                        matricula_nova = st.text_input("Matrícula (Única)")
                        
                        if st.form_submit_button("Cadastrar Aluno"):
                            if nome_novo and matricula_nova:
                                if adicionar_aluno_db(nome_novo, matricula_nova):
                                    st.rerun() 
                            else:
                                st.warning("Preencha Nome e Matrícula.")

                    st.markdown("---")
                    
                    # --- SEÇÃO REMOVER ALUNO ---
                    st.subheader("🗑️ Remover Aluno Existente")
                    st.warning("Remover um aluno apagará TODAS as suas notas e registros de frequência.")
                    
                    conn = sqlite3.connect(DB_NAME)
                    df_alunos = pd.read_sql_query("SELECT id_aluno, nome FROM Alunos ORDER BY nome", conn)
                    conn.close()
                    
                    opcoes_select = {row['nome']: row['id_aluno'] for index, row in df_alunos.iterrows()}

                    aluno_selecionado = st.selectbox(
                        'Selecione o Aluno para Remover',
                        options=[''] + list(opcoes_select.keys()),
                        key="sel_remover_aluno_fac" 
                    )
                    
                    if aluno_selecionado:
                        id_aluno_remover = opcoes_select[aluno_selecionado]
                        
                        if st.button(f"CONFIRMAR Remoção de {aluno_selecionado}", key="btn_confirmar_remocao_fac"): 
                            if remover_aluno_db(id_aluno_remover, aluno_selecionado):
                                st.rerun() 
                                
    # -------------------------------------------------------------------------
    # 7. LÓGICA DE FALHA DE LOGIN
    # -------------------------------------------------------------------------
    elif st.session_state.user_login_name is None:
        st.info("Insira seu nome de usuário e senha na barra lateral para acessar o Diário de Classe.")
        return 
    
    st.markdown("---") 

if __name__ == "__main__":
    main()
