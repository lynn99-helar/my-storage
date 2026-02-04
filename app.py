import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import hashlib
from PIL import Image
import io
import os

# --- 1. 配置与安全 ---
INVITE_CODE = "666666" 
ADMIN_USER = "lynn"

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# --- 2. 数据库逻辑 ---
def init_db():
    conn = sqlite3.connect('system_admin.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS userstable(username TEXT, password TEXT)')
    conn.commit()
    conn.close()

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
    conn.commit()
    conn.close()
    return db_name

def compress_image(uploaded_file):
    if uploaded_file:
        img = Image.open(uploaded_file)
        img.thumbnail((1200, 1200)) # 提高一点清晰度以匹配 The Row 质感
        buf = io.BytesIO()
        if img.mode in ("RGBA", "P"): img = img.convert("RGB")
        img.save(buf, format="JPEG", quality=85)
        return buf.getvalue()
    return None

# --- 3. MUJI & THE ROW 风格自定义 CSS ---
st.set_page_config(page_title="Storage Collection", layout="wide")

st.markdown("""
    <style>
    /* 整体背景：和纸色 */
    .stApp {
        background-color: #F7F3F0;
        color: #2C2C2C;
    }
    
    /* 隐藏顶部红线 */
    header {visibility: hidden;}
    
    /* 字体设计 */
    html, body, [class*="css"] {
        font-family: 'Optima', 'Candara', 'Noto Sans SC', sans-serif;
        font-weight: 300;
    }

    /* 输入框样式：极简线条 */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: transparent !important;
        border: none !important;
        border-bottom: 1px solid #D1CDC9 !important;
        border-radius: 0px !important;
        color: #2C2C2C !important;
    }

    /* 按钮样式：The Row 黑色哲学 */
    .stButton>button {
        background-color: #2C2C2C !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 0px !important;
        font-weight: 200 !important;
        letter-spacing: 2px !important;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #4A4A4A !important;
        opacity: 0.8;
    }

    /* 选项卡样式 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 50px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: transparent !important;
        border: none !important;
        color: #8C8C8C !important;
    }
    .stTabs [aria-selected="true"] {
        color: #2C2C2C !important;
        border-bottom: 2px solid #2C2C2C !important;
    }

    /* 物品展示卡片 */
    .stExpander {
        background-color: #FFFFFF !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03) !important;
        margin-bottom: 20px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. 逻辑处理 ---
init_db()
if 'page' not in st.session_state: st.session_state['page'] = 'login'
if 'user' not in st.session_state: st.session_state['user'] = ""

def go_to(page_name):
    st.session_state['page'] = page_name
    st.rerun()

# --- 5. 页面展示 ---
if st.session_state['page'] == 'login':
    _, col2, _ = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center; font-weight: 100; letter-spacing: 5px;'>COLLECTION</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #8C8C8C;'>Less, but better.</p>", unsafe_allow_html=True)
        u = st.text_input("USER")
        p = st.text_input("PASSWORD", type='password')
        if st.button("ENTER"):
            conn = sqlite3.connect('system_admin.db'); c = conn.cursor()
            c.execute('SELECT * FROM userstable WHERE username=? AND password=?', (u, make_hashes(p)))
            if c.fetchone():
                st.session_state['user'] = u
                go_to('main')
            else: st.error("Invalid credentials.")
        
        st.markdown("<br>", unsafe_allow_html=True)
        c_left, c_right = st.columns(2)
        if c_left.button("JOIN"): go_to('signup')
        if c_right.button("RESET"): go_to('reset')

elif st.session_state['page'] == 'signup':
    st.title("JOIN COLLECTION")
    nu = st.text_input("USERNAME")
    np = st.text_input("PASSWORD", type='password')
    nc = st.text_input("INVITATION CODE")
    if st.button("CREATE"):
        if nc == INVITE_CODE and nu and np:
            conn = sqlite3.connect('system_admin.db'); c = conn.cursor()
            c.execute('INSERT INTO userstable(username, password) VALUES (?,?)', (nu, make_hashes(np)))
            conn.commit(); conn.close()
            go_to('login')
    if st.button("BACK"): go_to('login')

elif st.session_state['page'] == 'reset':
    st.title("RESET ACCESS")
    ru = st.text_input("USERNAME")
    rc = st.text_input("INVITATION CODE")
    rp = st.text_input("NEW PASSWORD", type='password')
    if st.button("CONFIRM RESET"):
        if rc == INVITE_CODE and ru and rp:
            conn = sqlite3.connect('system_admin.db'); c = conn.cursor()
            c.execute("UPDATE userstable SET password=? WHERE username=?", (make_hashes(rp), ru))
            conn.commit(); conn.close()
            go_to('login')
    if st.button("BACK"): go_to('login')

elif st.session_state['page'] == 'main':
    st.sidebar.markdown(f"<h2 style='font-weight:100;'>{st.session_state['user']}</h2>", unsafe_allow_html=True)
    if st.sidebar.button("EXIT"): st.session_state['user'] = ""; go_to('login')
    
    user_db = init_user_db(st.session_state['user'])
    tabs = st.tabs(["VIEW", "ADD", "EDIT"])

    with tabs[0]: # 浏览
        q = st.text_input("SEARCH")
        conn = sqlite3.connect(user_db); df = pd.read_sql_query("SELECT * FROM all_items", conn)
        if not df.empty:
            if q: df = df[df['name'].str.contains(q, case=False) | df['l2'].str.contains(q, case=False)]
            for i, r in df.iterrows():
                with st.expander(f"{r['l2']} / {r['name']}"):
                    ci, ct = st.columns([1, 1.5])
                    if r['image']: ci.image(r['image'], use_container_width=True)
                    ct.markdown(f"<p style='color:#8C8C8C; font-size:12px;'>{r['created_date']}</p>", unsafe_allow_html=True)
                    ct.write(r['note'])
                    if ct.button("REMOVE", key=f"d_{r['id']}"):
                        conn.execute("DELETE FROM all_items WHERE id=?", (r['id'],)); conn.commit(); st.rerun()
        conn.close()

    with tabs[1]: # 入库
        conn = sqlite3.connect(user_db); cat_df = pd.read_sql_query("SELECT * FROM categories", conn); conn.close()
        m = st.selectbox("TYPE", ["📦 现实物品", "💻 虚拟资产"])
        subs = cat_df[cat_df['parent_name'] == m]['child_name'].tolist()
        l2 = st.selectbox("CATEGORY", subs if subs else ["None"])
        name = st.text_input("ITEM NAME")
        pic = st.file_uploader("IMAGE", type=['jpg','png','jpeg'])
        note = st.text_area("NOTE")
        if st.button("ARCHIVE"):
            if name:
                img = compress_image(pic)
                conn = sqlite3.connect(user_db)
                conn.execute("INSERT INTO all_items (item_type,l2,name,note,image,created_date) VALUES (?,?,?,?,?,?)",
                          (m,l2,name,note,img,datetime.now().strftime("%Y.%m.%d")))
                conn.commit(); conn.close(); st.rerun()

    with tabs[2]: # 分类管理
        conn = sqlite3.connect(user_db); c1, c2 = st.columns(2)
        p_sel = c1.selectbox("GROUP", ["📦 现实物品", "💻 虚拟资产"])
        new_c = c1.text_input("NEW CATEGORY")
        if c1.button("ADD CATEGORY"):
            conn.execute("INSERT INTO categories (parent_name, child_name) VALUES (?,?)", (p_sel, new_c))
            conn.commit(); st.rerun()
        cat_df = pd.read_sql_query("SELECT * FROM categories", conn)
        if not cat_df.empty:
            del_c = c2.selectbox("REMOVE CATEGORY", cat_df['child_name'].tolist())
            if c2.button("CONFIRM REMOVE"):
                conn.execute("DELETE FROM categories WHERE child_name=?", (del_c,)); conn.commit(); st.rerun()
        conn.close()
