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
                  item_type TEXT, l1 TEXT, l2 TEXT, name TEXT, 
                  note TEXT, image BLOB, created_date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS categories 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  parent_name TEXT, child_name TEXT)''')
    c.execute("SELECT count(*) FROM categories")
    if c.fetchone()[0] == 0:
        defaults = [("📦 现实物品", "常用工具"), ("💻 电子资料", "重要文档")]
        c.executemany("INSERT INTO categories (parent_name, child_name) VALUES (?,?)", defaults)
    conn.commit()
    conn.close()
    return db_name

def compress_image(uploaded_file):
    if uploaded_file:
        img = Image.open(uploaded_file)
        img.thumbnail((800, 800))
        buf = io.BytesIO()
        if img.mode in ("RGBA", "P"): img = img.convert("RGB")
        img.save(buf, format="JPEG", quality=75)
        return buf.getvalue()
    return None

# --- 3. 界面逻辑 ---
st.set_page_config(page_title="❤️极简私人仓库", layout="wide")
init_db()

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user'] = ""

if not st.session_state['logged_in']:
    welcome_img = "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?q=80&w=1000&auto=format&fit=crop"
    c1, c2 = st.columns([1.5, 1])
    with c1: st.image(welcome_img, use_container_width=True); st.title("❤️ 欢迎来到您的私人保险箱")
    with st.sidebar:
        st.title("🔐 登录验证")
        u = st.text_input("用户名", key="l_u")
        p = st.text_input("密码", type='password', key="l_p")
        if st.button("进入仓库"):
            conn = sqlite3.connect('system_admin.db')
            c = conn.cursor()
            c.execute('SELECT * FROM userstable WHERE username=? AND password=?', (u, make_hashes(p)))
            if c.fetchone():
                st.session_state['logged_in'], st.session_state['user'] = True, u
                st.rerun()
            else: st.error("用户名或密码错误")
        with st.expander("✨ 注册新账号"):
            nu, np, code = st.text_input("新用户名"), st.text_input("新密码", type="password"), st.text_input("邀请码")
            if st.button("完成注册"):
                if code == INVITE_CODE and nu and np:
                    conn = sqlite3.connect('system_admin.db'); c = conn.cursor()
                    c.execute('INSERT INTO userstable(username, password) VALUES (?,?)', (nu, make_hashes(np)))
                    conn.commit(); conn.close(); st.success("注册成功！请登录")
                else: st.error("信息不全或邀请码错误")
else:
    st.sidebar.write(f"👤 主人: **{st.session_state['user']}**")
    if st.sidebar.button("安全退出"): st.session_state['logged_in'] = False; st.rerun()
    
    user_db = init_user_db(st.session_state['user'])
    t_list = ["📋 浏览仓库", "📥 存入宝贝", "📁 整理分类"]
    if st.session_state['user'] == ADMIN_USER: t_list.append("🛠️ 楼管后台")
    tabs = st.tabs(t_list)

    with tabs[0]:
        q = st.text_input("🔍 搜索物品...")
        conn = sqlite3.connect(user_db); df = pd.read_sql_query("SELECT * FROM all_items", conn)
        if not df.empty:
            csv = df.drop(columns=['image']).to_csv(index=False).encode('utf-8-sig')
            st.download_button("💾 导出文字备份", csv, "backup.csv")
            if q: df = df[df['name'].str.contains(
