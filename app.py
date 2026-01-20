import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import hashlib

# --- 1. 密码加密小工具 (让密码在数据库里不显示明文) ---
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return hashed_text
    return False

# --- 2. 数据库初始化 (增加用户表) ---
def init_db():
    conn = sqlite3.connect('system_admin.db')
    c = conn.cursor()
    # 用户表：存用户名和加密后的密码
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
                  rule TEXT, suggest TEXT, note TEXT, 
                  image BLOB, created_date TEXT)''')
    conn.commit()
    conn.close()
    return db_name

# --- 3. 用户管理功能 ---
def add_userdata(username, password):
    conn = sqlite3.connect('system_admin.db')
    c = conn.cursor()
    c.execute('INSERT INTO userstable(username, password) VALUES (?,?)', (username, password))
    conn.commit()
    conn.close()

def login_user(username, password):
    conn = sqlite3.connect('system_admin.db')
    c = conn.cursor()
    c.execute('SELECT * FROM userstable WHERE username =? AND password =?', (username, password))
    data = c.fetchall()
    conn.close()
    return data

# --- 页面配置 ---
st.set_page_config(page_title="❤️极简生活私密仓库", layout="wide")
init_db()

# --- 4. 侧边栏：登录/注册系统 ---
st.sidebar.title("🔐 私人保险箱")
username = st.sidebar.text_input("用户名")
password = st.sidebar.text_input("密码", type='password')
login_btn = st.sidebar.checkbox("进入仓库")

if login_btn:
    hashed_pswd = make_hashes(password)
    result = login_user(username, hashed_pswd)
    
    if result:
        st.sidebar.success(f"欢迎回来，{username}！")
        # --- 以下是登录成功后的代码 ---
        user_db = init_user_db(username)
        st.title(f"✨ {username} 的私人极简仓库")
        
        # 录入部分
        st.sidebar.divider()
        st.sidebar.header("✨ 新增入库")
        mode = st.sidebar.radio("选择类型", ["📦 现实物品", "💻 电子资料"])
        item_name = st.sidebar.text_input("物品名称")
        start_date = st.sidebar.date_input("开始日期", datetime.now())
        uploaded_file = st.sidebar.file_uploader("上传照片", type=['jpg', 'png', 'jpeg'])
        img_byte = uploaded_file.read() if uploaded_file else None

        if st.sidebar.button("确认存入"):
            if item_name:
                conn = sqlite3.connect(user_db)
                c = conn.cursor()
                c.execute("INSERT INTO all_items (item_type, name, image, created_date) VALUES (?,?,?,?)",
                          (mode, item_name, img_byte, start_date.strftime("%Y-%m-%d")))
                conn.commit()
                conn.close()
                st.sidebar.success("✅ 已存入私人空间")
                st.rerun()

        # 展示部分
        search_query = st.text_input("🔍 搜索我的物品", "")
        conn = sqlite3.connect(user_db)
        df = pd.read_sql_query("SELECT * FROM all_items", conn)
        conn.close()

        if not df.empty:
            if search_query:
                df = df[df['name'].str.contains(search_query, case=False)]
            for index, row in df.iterrows():
                with st.expander(f"{row['name']}"):
                    if row['image']: st.image(row['image'], width=200)
                    st.write(f"日期: {row['created_date']}")
                    if st.button("🗑️ 删除", key=f"del_{row['id']}"):
                        conn = sqlite3.connect(user_db)
                        c = conn.cursor()
                        c.execute("DELETE FROM all_items WHERE id=?", (row['id'],))
                        conn.commit()
                        conn.close()
                        st.rerun()
    else:
        # 如果用户名不存在，提示可以创建
        st.warning("用户名或密码错误。")
        if st.button("以此名字和密码创建一个新仓库"):
            add_userdata(username, make_hashes(password))
            st.success("账号创建成功！请勾选‘进入仓库’登录。")
else:
    st.title("❤️ 欢迎来到极简生活仓库")
    st.info("请在左侧输入用户名和密码。如果是第一次使用，请输入你想用的名字和密码，然后点击下方的‘创建新仓库’。")
    
