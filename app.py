import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import hashlib
from PIL import Image
import io
import os

# --- 1. 核心配置 ---
INVITE_CODE = "666666" 
ADMIN_USER = "lynn"

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# --- 2. 数据库逻辑 ---
def init_db():
    conn = sqlite3.connect('system_admin.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS userstable(username TEXT, password TEXT)')
    conn.commit(); conn.close()

def init_user_db(username):
    db_name = f"{username}_storage.db"
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS all_items 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  item_type TEXT, l2 TEXT, name TEXT, 
                  note TEXT, image BLOB, created_date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS categories 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  parent_name TEXT, child_name TEXT)''')
    
    c.execute("SELECT count(*) FROM categories")
    if c.fetchone()[0] == 0:
        rich_defaults = [
            ("📦 现实物品", "👕 穿戴配饰"), ("📦 现实物品", "💻 数码电子"), 
            ("📦 现实物品", "🏠 家居日用"), ("📦 现实物品", "💄 美妆护肤"),
            ("📦 现实物品", "📚 图书文具"), ("📦 现实物品", "🧸 收藏爱好"),
            ("📦 现实物品", "💊 医疗健康"), ("📦 现实物品", "⚽ 运动户外"),
            ("💻 虚拟资产", "🔐 账号密码"), ("💻 虚拟资产", "🧾 电子票据"),
            ("💻 虚拟资产", "📄 重要文档"), ("💻 虚拟资产", "🎫 会员卡券")
        ]
        c.executemany("INSERT INTO categories (parent_name, child_name) VALUES (?,?)", rich_defaults)
    conn.commit(); conn.close()
    return db_name

def compress_image(uploaded_file):
    if uploaded_file:
        img = Image.open(uploaded_file)
        img.thumbnail((1000, 1000))
        buf = io.BytesIO()
        if img.mode in ("RGBA", "P"): img = img.convert("RGB")
        img.save(buf, format="JPEG", quality=85)
        return buf.getvalue()
    return None

# --- 3. 强化 UI 样式 (MUJI清晰版) ---
st.set_page_config(page_title="Minimalist Collection", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #F4F1ED; color: #333333; }
    [data-testid="stSidebar"] { background-color: #E8E4DE; border-right: 1px solid #D1CDC7; }
    h1, h2, h3 { color: #5D544B !important; font-weight: 500 !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { color: #8C8479 !important; font-size: 18px; }
    .stTabs [aria-selected="true"] { color: #5D544B !important; border-bottom-color: #5D544B !important; }
    .stButton>button {
        border: 2px solid #5D544B !important;
        color: #5D544B !important;
        background-color: white !important;
        border-radius: 4px !important;
        font-weight: 600;
    }
    .stButton>button:hover { background-color: #5D544B !important; color: white !important; }
    .stTextInput>div>div>input, .stSelectbox>div>div>div {
        border: 1px solid #BDB7B0 !important;
        background-color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

init_db()

if 'page' not in st.session_state: st.session_state['page'] = 'login'
if 'user' not in st.session_state: st.session_state['user'] = ""

def go_to(page_name):
    st.session_state['page'] = page_name
    st.rerun()

# --- 4. 页面内容 ---
if st.session_state['page'] == 'login':
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.write("### COLLECTION")
        u = st.text_input("用户名 USERNAME")
        p = st.text_input("密码 PASSWORD", type='password')
        if st.button("登 录"):
            conn = sqlite
