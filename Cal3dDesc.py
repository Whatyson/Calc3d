import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, time
import urllib.parse

# ==========================================
# 0. CONFIGURAÇÃO DA PÁGINA E ARQUIVOS
# ==========================================
st.set_page_config(page_title="Gestor 3D Pro - Connect", layout="wide", page_icon="📊")

# Arquivos de dados na raiz do projeto
PATH_ORCAMENTOS = "orcamentos.json"
PATH_CONFIG = "config.json"

# --- FUNÇÕES DE PERSISTÊNCIA JSON ---
def load_json(path, default_value):
    if not os.path.exists(path):
        with open(path, 'w') as f:
            json.dump(default_value, f)
        return default_value
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except:
        return default_value

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)

# --- ESTILO VISUAL ENTERPRISE ---
def aplicar_estilo_customizado():
    st.markdown("""
        <style>
        .stApp { background-color: #f8f9fa; }
        h1, h2, h3 { color: #004a99 !important; font-weight: 800 !important; }
        [data-testid="stMetric"] {
            background-color: #ffffff; border: 1px solid #e9ecef;
            border-radius: 10px; padding: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }
        [data-testid="stMetricValue"] { font-size: 32px; color: #004a99; font-weight: bold; }
        div.stButton > button {
            background-color: #004a99; color: white; border-radius: 8px;
            padding: 10px 20px; font-weight: bold; transition: all 0.3s;
        }
        div.stButton > button:hover { background-color: #003366; color: #ffcc00; border: 1px solid #ffcc00; }
        .stTabs [data-baseweb="tab-list"] { gap: 15px; background-color: #ffffff; padding: 10px; border-radius: 10px; }
        .stTabs [aria-selected="true"] { background-color: #004a99 !important; color: white !important; }
        </style>
    """, unsafe_allow_html=True)

aplicar_estilo_customizado()

# ==========================================
# 1. SIDEBAR - PARÂMETROS DE CUSTO
# ==========================================
def carregar_config():
    return load_json(PATH_CONFIG, {"kwh": 0.90, "watts": 250, "v_maq": 3500.0, "meses": 24, "h_mes": 160})

c_atual = carregar_config()

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3233/3233513.png", width=80)
    st.header("⚙️ Configurações de Custo")
    
    v_kwh = st.number_input("Preço kWh (R$)", value=float(c_atual["kwh"]))
    v_watts = st.number_input("Consumo da Máquina (W)", value=int(c_atual["watts"]))
    v_maq = st.number_input("Valor da Impressora (R$)", value=float(c_atual["v_maq"]))
    v_meses = st.number_input("Vida Útil Estimada (Meses)", value=int(c_atual["meses"]))
    v_horas = st.number_input("Horas de Uso/Mês", value=int(c_atual["h_mes"]))

    if st.button("💾 Salvar Configurações", use_container_width=True):
        save_json(PATH_CONFIG, {"kwh": v_kwh, "watts": v_watts, "v_maq": v_maq, "meses": v_meses, "h_mes": v_horas})
        st.toast("Configurações atualizadas!", icon="✅")

# Cálculo automático do Custo por Hora (Energia + Depreciação)
custo_hora = ((v_watts/1000) * v_kwh) + ((v_maq/v_meses)/v_horas) if (v_meses > 0 and v_horas > 0) else 0

# ==========================================
# 2. INTERFACE PRINCIPAL
# ==========================================
st.title("🖨️ Gestor 3D - Connect Tecnologia")

tab1, tab2 = st.tabs(["💰 Calculadora de Orçamentos", "📊 Histórico e Métricas"])

# --- ABA 1: CALCULADORA ---
with tab1:
    col_f, col_r = st.columns([1, 1.2])
    
    with col_f:
        with st.form("orcamento_form"):
            st.subheader("📝 Novo Orçamento")
            nome = st.text_input("Cliente / Nome da Peça")
            tel = st.text_input("WhatsApp (DDD + Número)")
            
            c1, c2 = st.columns(2)
            p_fil = c1.number_input("Preço do Filamento (kg)", value=100.0)
            peso = c2.number_input("Peso da Peça (g)", value=50.0)
            
            tempo = st.number_input("Tempo de Impressão (Horas)", value=2.0)
            margem = st.slider("Margem de Lucro (%)", 0, 400, 100)
            
            cd, ch, cs = st.columns(3)
            data_p = cd.date_input("Data de Entrega", datetime.now())
            hora_p = ch.time_input("Horário", time(18, 0))
            status_p = cs.selectbox("Status Inicial", ["Pendente", "Produzindo", "Finalizado"])
            
            if st.form_submit_button("⚡ Gerar e Salvar"):
                # Cálculo de custos
                custo_material = (p_fil / 1000) * peso
                custo_maquina = tempo * custo_hora
                custo_total = round(custo_material + custo_maquina, 2)
                valor_venda = round(custo_total * (1 + margem/100), 2)
                
                # Persistência
                db_orc = load_json(PATH_ORCAMENTOS, [])
                novo_id = max([x['id'] for x in db_orc], default=0) + 1
                
                db_orc.append({
                    "id": novo_id,
                    "data_reg": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "produto": nome or "Peça 3D",
                    "telefone": "".join(filter(str.isdigit, tel)),
                    "tempo": tempo,
                    "custo": custo_total,
                    "venda": valor_venda,
                    "lucro": round(valor_venda - custo_total, 2),
                    "status": status_p,
                    "entrega": f"{data_p.strftime('%d/%m/%Y')} {hora_p.strftime('%H:%M')}"
                })
                save_json(PATH_ORCAMENTOS, db_orc)
                st.success("Orçamento salvo com sucesso!")
                st.rerun()

    with col_r:
        db_orc = load_json(PATH_ORCAMENTOS, [])
        if db_orc:
            u = db_orc[-1]
            st.subheader("🏁 Resumo do Orçamento")
            m1, m2, m3 = st.columns(3)
            m1.metric("Custo Produção", f"R$ {u['custo']:.2f}")
            m2.metric("Preço de Venda", f"R$ {u['venda']:.2f}")
            m3.metric("Lucro Estimado", f"R$ {u['lucro']:.2f}")
            
            # Gerador de link de WhatsApp
            msg = (f"Olá! O orçamento para *{u['produto']}* ficou pronto. 🚀\n\n"
                   f"💰 *Valor:* R$ {u['venda']:.2f}\n"
                   f"📅 *Previsão:* {u['entrega']}\n\n"
                   f"Podemos confirmar o pedido?")
            
            if u['telefone']:
                st.link_button("🟢 Enviar para WhatsApp", 
                              f"https://wa.me/55{u['telefone']}?text={urllib.parse.quote(msg)}", 
                              use_container_width=True)
            st.code(msg, language="markdown")

# --- ABA 2: HISTÓRICO ---
with tab2:
    db_orc = load_json(PATH_ORCAMENTOS, [])
    if db_orc:
        df = pd.DataFrame(db_orc)
        
        # Métricas Consolidadas
        c1, c2, c3 = st.columns(3)
        c1.metric("Total de Pedidos", len(df))
        c2.metric("Faturamento Total", f"R$ {df['venda'].sum():.2f}")
        c3.metric("Lucro Acumulado", f"R$ {df['lucro'].sum():.2f}")
        
        st.divider()
        st.write("**🗄️ Gerenciar Orçamentos (Edição e Exclusão)**")
        
        # Editor de dados para deletar ou mudar status
        df['Remover'] = False
        df_editado = st.data_editor(
            df,
            column_config={
                "Remover": st.column_config.CheckboxColumn("Excluir?"),
                "status": st.column_config.SelectboxColumn("Status", options=["Pendente", "Produzindo", "Finalizado"]),
                "venda": st.column_config.NumberColumn("Venda (R$)", format="%.2f"),
                "lucro": st.column_config.NumberColumn("Lucro (R$)", format="%.2f")
            },
            hide_index=True,
            width='stretch'
        )

        if st.button("💾 Sincronizar Alterações", use_container_width=True):
            # Filtra apenas quem não foi marcado para remover
            dados_finais = df_editado[df_editado['Remover'] == False].drop(columns=['Remover']).to_dict(orient='records')
            save_json(PATH_ORCAMENTOS, dados_finais)
            st.success("Dados sincronizados!")
            st.rerun()
    else:
        st.info("Nenhum dado registrado até o momento.")