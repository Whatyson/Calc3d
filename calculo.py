import streamlit as st
import pandas as pd
from datetime import datetime, time
import urllib.parse
from sqlalchemy import create_engine, text

# ==========================================
# 0. CONFIGURAÇÃO DA PÁGINA (VISUAL ENTERPRISE)
# ==========================================
st.set_page_config(page_title="Gestor 3D Pro - Connect", layout="wide", page_icon="📊")

# --- FUNÇÃO DE INJEÇÃO DE CSS (O SEU NOVO TEMA) ---
def aplicar_estilo_customizado():
    st.markdown("""
        <style>
        /* 1. Reset e Fundo Global */
        .stApp {
            background-color: #f8f9fa; /* Fundo cinza claro profissional */
        }
        
        /* 2. Estilização dos Títulos Principais */
        h1, h2, h3 {
            color: #004a99 !important; /* Azul Connect */
            font-weight: 800 !important;
        }
        
        /* 3. Estilização das Métricas (Cards de Lucro) */
        [data-testid="stMetric"] {
            background-color: #ffffff;
            border: 1px solid #e9ecef;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }
        [data-testid="stMetricValue"] {
            font-size: 32px;
            color: #004a99; /* Azul nas métricas */
            font-weight: bold;
        }
        
        /* 4. Estilização de Botões (Enterprise) */
        div.stButton > button {
            background-color: #004a99;
            color: white;
            border-radius: 8px;
            border: none;
            padding: 10px 20px;
            font-weight: bold;
            transition: all 0.3s;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        div.stButton > button:hover {
            background-color: #003366; /* Azul Marinho ao passar o mouse */
            color: #ffcc00; /* Destaque amarelo suave */
            border: 1px solid #ffcc00;
        }

        /* 5. Estilização das Abas (Tabs) */
        .stTabs [data-baseweb="tab-list"] {
            gap: 15px;
            background-color: #ffffff;
            padding: 10px;
            border-radius: 10px;
            border: 1px solid #e9ecef;
        }

        .stTabs [data-baseweb="tab"] {
            background-color: #f8f9fa;
            border-radius: 5px;
            padding: 12px 25px;
            color: #495057;
            font-weight: 600;
        }

        .stTabs [aria-selected="true"] {
            background-color: #004a99 !important; /* Aba ativa em Azul */
            color: white !important;
        }
        
        /* 6. Outros detalhes (Sidebar) */
        .st-emotion-cache-6qobw {
            background-color: #ffffff; /* Fundo da sidebar branco */
            border-right: 1px solid #e9ecef;
        }
        </style>
    """, unsafe_allow_html=True)

# Aplica o tema visual Enterprise logo após a config
aplicar_estilo_customizado()

# ==========================================
# 1. CONEXÃO COM SQL SERVER (Via PyMSSQL)
# ==========================================
DB_CONFIG = {
    "user": "sa",
    "pass": "basf2533", 
    "server": "contec1.duckdns.org:1433", # Mantemos os dois pontos e a porta
    "database": "TEST_PY"
}

# String limpa usando pymssql (não precisa declarar driver do Windows)
conn_str = f"mssql+pymssql://{DB_CONFIG['user']}:{DB_CONFIG['pass']}@{DB_CONFIG['server']}/{DB_CONFIG['database']}"

@st.cache_resource
def get_engine():
    return create_engine(conn_str, fast_executemany=False)

engine = get_engine()

# ==========================================
# 2. CONTROLE DE ACESSO (SQL PERSISTENTE)
# ==========================================
def login():
    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False
        st.session_state["usuario_logado"] = None
        st.session_state["perfil"] = None

    if not st.session_state["autenticado"]:
        st.markdown("<h2 style='text-align: center;'>🔐 Login - Connect Tecnologia</h2>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 1.2, 1])
        with col2:
            with st.container(border=True): # Card em torno do login
                with st.form("login_form"):
                    u_input = st.text_input("Usuário")
                    p_input = st.text_input("Senha", type="password")
                    st.divider()
                    entrar = st.form_submit_button("Acessar Sistema", use_container_width=True)
                    
                    if entrar:
                        with engine.connect() as conn:
                            query = text("SELECT nome_usuario, perfil FROM usuarios WHERE nome_usuario = :u AND senha = :p")
                            user_db = conn.execute(query, {"u": u_input, "p": p_input}).fetchone()
                            
                            if user_db:
                                st.session_state["autenticado"] = True
                                st.session_state["usuario_logado"] = user_db[0]
                                st.session_state["perfil"] = user_db[1]
                                st.rerun()
                            else:
                                st.error("Usuário ou senha incorretos.")
        st.stop()

login()

# ==========================================
# 3. FUNÇÕES DE APOIO
# ==========================================
def carregar_config():
    try:
        with engine.connect() as conn:
            res = conn.execute(text("SELECT TOP 1 kwh, watts, v_maq, meses, h_mes FROM config_3d")).fetchone()
            if res: return {"kwh": res[0], "watts": res[1], "v_maq": res[2], "meses": res[3], "h_mes": res[4]}
    except: pass
    return {"kwh": 0.90, "watts": 250, "v_maq": 3500.0, "meses": 24, "h_mes": 160}

def salvar_config(c):
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM config_3d"))
        conn.execute(text("""
            INSERT INTO config_3d (id, kwh, watts, v_maq, meses, h_mes) 
            VALUES (1, :k, :w, :v, :m, :h)
        """), c)

# ==========================================
# 4. SIDEBAR (CONFIGURAÇÕES)
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3233/3233513.png", width=100) # Ícone profissional
    st.header("⚙️ Configurações")
    st.write(f"Usuário: **{st.session_state['usuario_logado']}** ({st.session_state['perfil']})")
    
    st.divider()
    with st.container(border=True): # Grupo de custos
        c_atual = carregar_config()
        v_kwh = st.number_input("Preço kWh", value=float(c_atual["kwh"]))
        v_watts = st.number_input("Consumo (W)", value=int(c_atual["watts"]))
        v_maq = st.number_input("Valor Máquina", value=float(c_atual["v_maq"]))
        v_meses = st.number_input("Vida Útil (Mês)", value=int(c_atual["meses"]))
        v_horas = st.number_input("Horas/Mês", value=int(c_atual["h_mes"]))

    if st.button("💾 Salvar Parâmetros"):
        salvar_config({"k": v_kwh, "w": v_watts, "v": v_maq, "m": v_meses, "h": v_horas})
        st.toast("Parâmetros salvos!", icon="✅")
    
    st.divider()
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state["autenticado"] = False
        st.rerun()

custo_hora = ((v_watts/1000) * v_kwh) + ((v_maq/v_meses)/v_horas) if (v_meses > 0 and v_horas > 0) else 0

# ==========================================
# 5. INTERFACE PRINCIPAL
# ==========================================
st.title("🖨️ Gestor 3D - Connect Tecnologia")

abas_lista = ["💰 Calculadora & Venda", "📊 Dashboard de Produção"]
if st.session_state["perfil"] == "adm":
    abas_lista.append("👥 Gestão de Usuários")

tabs = st.tabs(abas_lista)

# --- ABA 1: CALCULADORA ---
with tabs[0]:
    col_f, col_r = st.columns([1, 1.2])
    with col_f:
        with st.form("orcamento_form"):
            st.subheader("📝 Novo Orçamento")
            nome = st.text_input("Cliente / Produto")
            tel = st.text_input("WhatsApp (DDD+Número)")
            c1, c2 = st.columns(2)
            p_fil = c1.number_input("Preço Filamento (kg)", value=100.0)
            peso = c2.number_input("Peso Final (g)", value=50.0)
            tempo = st.number_input("Tempo de Impressão (h)", value=2.0)
            margem = st.slider("Margem de Lucro (%)", 0, 300, 100)
            
            st.divider()
            cd, ch, cs = st.columns(3)
            data_p = cd.date_input("Entrega", datetime.now())
            hora_p = ch.time_input("Hora", time(18, 0))
            status_p = cs.selectbox("Status", ["Pendente", "Produzindo", "Finalizado"])
            
            if st.form_submit_button("⚡ Registrar"):
                c_calc = round(((p_fil/1000)*peso) + (tempo*custo_hora), 2)
                v_venda = round(c_calc * (1 + margem/100), 2)
                with engine.begin() as conn:
                    conn.execute(text("""
                        INSERT INTO orcamentos (data_reg, produto, telefone, tempo, custo, venda, lucro, status, entrega) 
                        VALUES (GETDATE(), :p, :t, :tm, :c, :v, :l, :s, :e)
                    """), {"p": nome or "Peça 3D", "t": "".join(filter(str.isdigit, tel)), "tm": tempo, 
                           "c": c_calc, "v": v_venda, "l": v_venda-c_calc, "s": status_p,
                           "e": f"{data_p.strftime('%d/%m/%Y')} {hora_p.strftime('%H:%M')}"})
                st.success("Orçamento salvo!")
                st.rerun()

    with col_r:
        with engine.connect() as conn:
            u = conn.execute(text("SELECT TOP 1 * FROM orcamentos ORDER BY id DESC")).mappings().fetchone()
        if u:
            st.subheader("🏁 Resumo")
            m1, m2, m3 = st.columns(3)
            m1.metric("Custo", f"R$ {(u['custo'] or 0.0):.2f}")
            m2.metric("Venda", f"R$ {(u['venda'] or 0.0):.2f}")
            m3.metric("Lucro", f"R$ {(u['lucro'] or 0.0):.2f}")
            
            msg = (f"Olá! Orçamento para *{u['produto']}* pronto. 🚀\n\n"
                   f"💰 *Valor:* R$ {(u['venda'] or 0.0):.2f}\n"
                   f"📅 *Entrega:* {u['entrega']}\n"
                   f"📍 *Status:* {u['status']}\n\n"
                   f"Confirmamos?")
            if u['telefone']:
                st.link_button("🟢 Enviar WhatsApp", f"https://wa.me/55{u['telefone']}?text={urllib.parse.quote(msg)}", use_container_width=True)
            st.code(msg, language="markdown")

# --- ABA 2: DASHBOARD COMPLETO (COM VISUAL NOVO) ---
with tabs[1]:
    with engine.connect() as conn:
        df = pd.read_sql("SELECT * FROM orcamentos ORDER BY id DESC", conn)
    
    if not df.empty:
        df['deletar'] = False
        
        # Métricas de topo com fundo branco estilizado
        st.subheader("📊 Métricas Consolidadas")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Orçados", len(df))
        c2.metric("Faturamento", f"R$ {df['venda'].sum():.2f}")
        c3.metric("Lucro Total", f"R$ {df['lucro'].sum():.2f}")
        c4.metric("Ticket Médio", f"R$ {df['venda'].mean():.2f}")
        
        st.divider()
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            with st.container(border=True): # Card para gráfico
                st.write("**📦 Status dos Pedidos**")
                st.bar_chart(df['status'].value_counts(), color="#FF4B4B") # Mantém vermelho só aqui para alerta
        with col_g2:
            with st.container(border=True): # Card para gráfico
                st.write("**💰 Faturamento por Produto (Top 5)**")
                top_p = df.groupby('produto')['venda'].sum().sort_values(ascending=False).head(5)
                st.bar_chart(top_p, color="#29B5E8") # Azul para faturamento

        st.write("**🗄️ Gestão de Histórico (Edição)**")
        df_editado = st.data_editor(
            df, 
            column_config={
                "deletar": st.column_config.CheckboxColumn("Excluir?"),
                "status": st.column_config.SelectboxColumn("Status", options=["Pendente", "Produzindo", "Finalizado"]),
                "venda": st.column_config.NumberColumn("Venda (R$)", format="%.2f"),
                "lucro": st.column_config.NumberColumn("Lucro (R$)", format="%.2f")
            },
            hide_index=True, width='stretch'
        )

        if st.button("💾 Sincronizar Alterações com SQL Server", use_container_width=True):
            with engine.begin() as conn:
                for _, row in df_editado.iterrows():
                    if row['deletar']:
                        conn.execute(text("DELETE FROM orcamentos WHERE id = :id"), {"id": row['id']})
                    else:
                        conn.execute(text("UPDATE orcamentos SET status = :s WHERE id = :id"), {"s": row['status'], "id": row['id']})
            st.success("Banco sincronizado!")
            st.rerun()
    else:
        st.info("O banco de dados está vazio.")

# --- ABA 3: GESTÃO DE USUÁRIOS (SÓ ADM) ---
if st.session_state["perfil"] == "adm":
    with tabs[2]:
        st.subheader("👥 Controle de Acesso")
        c_add, c_list = st.columns([1, 1.5])
        
        with c_add:
            with st.form("novo_user_form", border=True):
                st.write("➕ **Novo Usuário**")
                n_u = st.text_input("Usuário")
                n_s = st.text_input("Senha", type="password")
                n_p = st.selectbox("Perfil", ["operador", "adm"])
                if st.form_submit_button("Cadastrar", use_container_width=True):
                    try:
                        with engine.begin() as conn:
                            conn.execute(text("INSERT INTO usuarios (nome_usuario, senha, perfil) VALUES (:u, :s, :p)"),
                                        {"u": n_u, "s": n_s, "p": n_p})
                        st.success(f"Usuário {n_u} cadastrado!")
                        st.rerun()
                    except: st.error("Erro: Usuário já existe.")
        
        with c_list:
            with st.container(border=True):
                st.write("📋 **Usuários Cadastrados**")
                df_u = pd.read_sql("SELECT id, nome_usuario, perfil FROM usuarios", engine)
                st.dataframe(df_u, use_container_width=True, hide_index=True)
