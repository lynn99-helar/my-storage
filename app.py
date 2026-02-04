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

# --- 3. MUJI & THE ROW 风格 UI 注入 ---
st.set_page_config(page_title="Storage Collection", layout="wide")

st.markdown("""
    <style>
    /* 全局背景：MUJI 米白色 */
    .stApp {
        background-color: #F7F5F2;
        color: #434343;
        font-family: "Optima", "PingFang SC", "Hiragino Sans GB", sans-serif;
    }
    /* 侧边栏样式 */
    [data-testid="stSidebar"] {
        background-color: #EFECE7;
        border-right: 1px solid #DED9D1;
    }
    /* 按钮样式：The Row 冷淡风格 */
    .stButton>button {
        border: 1px solid #434343 !important;
        background-color: transparent !important;
        color: #434343 !important;
        border-radius: 0px !important;
        font-weight: 300;
        letter-spacing: 1px;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #434343 !important;
        color: white !important;
    }
    /* 卡片式设计 */
    .stExpander {
        background-color: white !important;
        border: none !important;
        border-radius: 2px !important;
        margin-bottom: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }
    /* 输入框 */
    .stTextInput>div>div>input {
        border-radius: 0px !important;
        border: none !important;
        border-bottom: 1px solid #DED9D1 !important;
        background-color: transparent !important;
    }
    h1, h2, h3 {
        font-weight: 300 !important;
        letter-spacing: 2px;
        color: #2C2C2C;
    }
    </style>
    """, unsafe_allow_html=True)

init_db()

if 'page' not in st.session_state: st.session_state['page'] = 'login'
if 'user' not in st.session_state: st.session_state['user'] = ""

def go_to(page_name):
    st.session_state['page'] = page_name
    st.rerun()

# --- 4. 页面逻辑 ---
if st.session_state['page'] == 'login':
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.write("---")
        st.title("COLLECTION")
        st.write("Clean lines. Organized life.")
        u = st.text_input("USERNAME / 用户名")
        p = st.text_input("PASSWORD / 密码", type='password')
        if st.button("ENTER / 进入"):
            conn = sqlite3.connect('system_admin.db'); c = conn.cursor()
            c.execute('SELECT * FROM userstable WHERE username=? AND password=?', (u, make_hashes(p)))
            if c.fetchone():
                st.session_state['user'] = u
                go_to('main')
            else: st.error("Incorrect credentials.")
        
        st.write("")
        c_a, c_b = st.columns(2)
        if c_a.button("CREATE / 注册"): go_to('signup')
        if c_b.button("RESET / 重置"): go_to('reset')

elif st.session_state['page'] == 'signup':
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.title("NEW ACCOUNT")
        nu = st.text_input("SET USERNAME")
        np = st.text_input("SET PASSWORD", type='password')
        nc = st.text_input("INVITE CODE")
        if st.button("CONFIRM / 确认"):
            if nc == INVITE_CODE and nu and np:
                conn = sqlite3.connect('system_admin.db'); c = conn.cursor()
                c.execute('INSERT INTO userstable(username, password) VALUES (?,?)', (nu, make_hashes(np)))
                conn.commit(); conn.close()
                go_to('login')
        if st.button("BACK"): go_to('login')

elif st.session_state['page'] == 'reset':
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.title("PASSWORD RESET")
        ru = st.text_input("USERNAME")
        rc = st.text_input("INVITE CODE")
        rp = st.text_input("NEW PASSWORD", type='password')
        if st.button("UPDATE / 更新"):
            if rc == INVITE_CODE and ru and rp:
                conn = sqlite3.connect('system_admin.db'); c = conn.cursor()
                c.execute("UPDATE userstable SET password=? WHERE username=?", (make_hashes(rp), ru))
                conn.commit(); conn.close(); go_to('login')
        if st.button("BACK"): go_to('login')

elif st.session_state['page'] == 'main':
    st.sidebar.write(f"USER: {st.session_state['user']}")
    if st.sidebar.button("SIGN OUT / 退出"): st.session_state['user'] = ""; go_to('login')
    
    user_db = init_user_db(st.session_state['user'])
    tabs = st.tabs(["INVENTORY / 浏览", "ADD / 入库", "LABEL / 分类"])
    
    if st.session_state['user'] == ADMIN_USER:
        tabs = st.tabs(["INVENTORY / 浏览", "ADD / 入库", "LABEL / 分类", "SYSTEM / 管理"])

    with tabs[0]:
        q = st.text_input("SEARCH / 搜索", placeholder="Looking for something?")
        conn = sqlite3.connect(user_db); df = pd.read_sql_query("SELECT * FROM all_items ORDER BY id DESC", conn)
        if not df.empty:
            if q: df = df[df['name'].str.contains(q, case=False) | df['l2'].str.contains(q, case=False)]
            for i, r in df.iterrows():
                with st.expander(f"{r['l2']} | {r['name']}"):
                    ci, ct = st.columns([1, 2])
                    if r['image']: ci.image(r['image'])
                    ct.write(f"Date: {r['created_date']}")
                    ct.write(f"Note: {r['note']}")
                    if ct.button("DELETE", key=f"d_{r['id']}"):
                        conn.execute("DELETE FROM all_items WHERE id=?", (r['id'],)); conn.commit(); st.rerun()
        conn.close()

    with tabs[1]:
        conn = sqlite3.connect(user_db); cat_df = pd.read_sql_query("SELECT * FROM categories", conn); conn.close()
        c1, c2 = st.columns(2)
        m = c1.selectbox("CATEGORY / 大类", ["📦 现实物品", "💻 虚拟资产"])
        subs = cat_df[cat_df['parent_name'] == m]['child_name'].tolist()
        l2 = c1.selectbox("SUB-CATEGORY / 二级分类", subs)
        name = c1.text_input("NAME / 名称")
        pic = c2.file_uploader("IMAGE / 照片", type=['jpg','png','jpeg'])
        note = c2.text_area("DESCRIPTION / 备注")
        if st.button("SAVE TO COLLECTION / 确认存入"):
            if name:
                img = compress_image(pic)
                conn = sqlite3.connect(user_db)
                conn.execute("INSERT INTO all_items (item_type,l2,name,note,image,created_date) VALUES (?,?,?,?,?,?)",
                          (m,l2,name,note,img,datetime.now().strftime("%Y-%m-%d")))
                conn.commit(); conn.close(); st.rerun()

    with tabs[2]:
        conn = sqlite3.connect(user_db)
        c1, c2 = st.columns(2)
        p_sel = c1.selectbox("PARENT / 父级", ["📦 现实物品", "💻 虚拟资产"], key="cp")
        new_c = c1.text_input("NEW LABEL / 新分类名称")
        if c1.button("ADD LABEL"):
            conn.execute("INSERT INTO categories (parent_name, child_name) VALUES (?,?)", (p_sel, new_c))
            conn.commit(); st.rerun()
        cat_df = pd.read_sql_query("SELECT * FROM categories", conn)
        if not cat_df.empty:
            del_c = c2.selectbox("REMOVE / 删除", cat_df['child_name'].tolist())
            if c2.button("CONFIRM REMOVE"):
                conn.execute("DELETE FROM categories WHERE child_name=?", (del_c,)); conn.commit(); st.rerun()
        conn.close()

    if st.session_state['user'] == ADMIN_USER:
        with tabs[3]:
            conn = sqlite3.connect('system_admin.db'); u_df = pd.read_sql_query("SELECT username FROM userstable", conn)
            st.write(f"Active Users: {len(u_df)}")
            for u in u_df['username']:
                if u != ADMIN_USER:
                    c_u, c_d = st.columns([4, 1])
                    c_u.write(f"Account: {u}")
                    if c_d.button("REMOVE ACCOUNT", key=f"m_{u}"):
                        conn.execute("DELETE FROM userstable WHERE username=?", (u,)); conn.commit()
                        try: os.remove(f"{u}_storage.db")
                        except: pass
                        st.rerun()
            conn.close()
