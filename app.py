import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import hashlib
from PIL import Image
import io

# --- 1. 安全与加密 ---
INVITE_CODE = "666666"

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# --- 2. 数据库管理 ---
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
                  item_type TEXT, l1 TEXT, l2 TEXT, name TEXT, 
                  note TEXT, image BLOB, created_date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS categories 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  parent_name TEXT, child_name TEXT)''')
    c.execute("SELECT count(*) FROM categories")
    if c.fetchone()[0] == 0:
        default_cats = [("📦 现实物品", "衣物"), ("📦 现实物品", "电子设备"), ("💻 电子资料", "工作")]
        c.executemany("INSERT INTO categories (parent_name, child_name) VALUES (?,?)", default_cats)
    conn.commit()
    conn.close()
    return db_name

# --- 3. 图片优化 ---
def compress_image(uploaded_file):
    if uploaded_file is not None:
        img = Image.open(uploaded_file)
        img.thumbnail((800, 800)) 
        buf = io.BytesIO()
        if img.mode in ("RGBA", "P"): img = img.convert("RGB")
        img.save(buf, format="JPEG", quality=70)
        return buf.getvalue()
    return None

st.set_page_config(page_title="❤️极简生活私密仓库", layout="wide")
init_db()

# --- 登录状态 ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user'] = ""

# --- 4. 登录/注册界面 ---
if not st.session_state['logged_in']:
    st.sidebar.title("🔐 私人保险箱")
    user = st.sidebar.text_input("用户名")
    passwd = st.sidebar.text_input("密码", type='password')
    if st.sidebar.button("登录"):
        conn = sqlite3.connect('system_admin.db')
        c = conn.cursor()
        c.execute('SELECT * FROM userstable WHERE username =? AND password =?', (user, make_hashes(passwd)))
        if c.fetchall():
            st.session_state['logged_in'] = True
            st.session_state['user'] = user
            st.rerun()
        else: st.sidebar.error("账号或密码错误")

    with st.sidebar.expander("✨ 注册新账号"):
        nu, np, code = st.text_input("用户名"), st.text_input("密码", type='password'), st.text_input("邀请码")
        if st.button("创建新仓库"):
            if code == INVITE_CODE and nu and np:
                conn = sqlite3.connect('system_admin.db')
                c = conn.cursor()
                c.execute('INSERT INTO userstable(username, password) VALUES (?,?)', (nu, make_hashes(np)))
                conn.commit()
                conn.close()
                st.success("注册成功！请登录")
            else: st.error("请确保邀请码正确且信息完整")
else:
    # 登录后显示退出按钮，增加确认
    st.sidebar.write(f"👤 用户: **{st.session_state['user']}**")
    if st.sidebar.button("退出登录"):
        st.session_state['logged_in'] = False
        st.rerun()
    
    user_db = init_user_db(st.session_state['user'])
    st.title(f"✨ {st.session_state['user']} 的极简仓库")
    
    tab1, tab2, tab3 = st.tabs(["📋 仓库浏览", "📥 新增入库", "📁 分类管理"])
    
    # --- 1. 分类管理 (增加确认) ---
    with tab3:
        st.header("📁 分类管理")
        conn = sqlite3.connect(user_db)
        cat_df = pd.read_sql_query("SELECT * FROM categories", conn)
        
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("➕ 新增分类")
            p_cat = st.selectbox("所属一级", ["📦 现实物品", "💻 电子资料"])
            c_cat = st.text_input("新分类名称")
            if st.button("确认添加此分类"):
                if c_cat:
                    conn.execute("INSERT INTO categories (parent_name, child_name) VALUES (?,?)", (p_cat, c_cat))
                    conn.commit()
                    st.toast(f"✅ 分类 {c_cat} 已添加")
                    st.rerun()
        
        with c2:
            st.subheader("➖ 删除分类")
            if not cat_df.empty:
                del_id = st.selectbox("选择要删除的分类", cat_df['id'].tolist(), 
                                      format_func=lambda x: f"{cat_df[cat_df['id']==x]['child_name'].values[0]}")
                # 删除确认
                if st.button("⚠️ 点击删除所选分类"):
                    st.warning("再次点击下方的确认按钮即可永久删除。")
                    if st.button("🔥 我确定要删除该分类", key="confirm_del_cat"):
                        conn.execute("DELETE FROM categories WHERE id=?", (del_id,))
                        conn.commit()
                        st.rerun()
        conn.close()

    # --- 2. 新增入库 (增加确认) ---
    with tab2:
        st.header("✨ 新增物品")
        conn = sqlite3.connect(user_db)
        cat_df = pd.read_sql_query("SELECT * FROM categories", conn)
        conn.close()

        c1, c2 = st.columns(2)
