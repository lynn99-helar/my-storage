import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import hashlib
from PIL import Image
import io
import os

# --- 1. 安全配置 ---
INVITE_CODE = "pl"
ADMIN_USER = "lynn"  # 👈 奶奶，这里改成您想用的管理员名字

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
        defaults = [("📦 现实物品", "常用工具"), ("💻 电子资料", "重要文档")]
        c.executemany("INSERT INTO categories (parent_name, child_name) VALUES (?,?)", defaults)
    conn.commit()
    conn.close()
    return db_name

def compress_image(uploaded_file):
    if uploaded_file is not None:
        img = Image.open(uploaded_file)
        img.thumbnail((800, 800)) 
        buf = io.BytesIO()
        if img.mode in ("RGBA", "P"): img = img.convert("RGB")
        img.save(buf, format="JPEG", quality=75)
        return buf.getvalue()
    return None

st.set_page_config(page_title="❤️极简私人仓库管理版", layout="wide")
init_db()

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user'] = ""

# --- 3. 登录界面 ---
if not st.session_state['logged_in']:
    welcome_img = "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?q=80&w=1000&auto=format&fit=crop"
    col_main1, col_main2 = st.columns([1.5, 1])
    with col_main1:
        st.image(welcome_img, use_container_width=True)
        st.title("❤️ 欢迎来到您的私人保险箱")
    with st.sidebar:
        st.title("🔐 登录验证")
        user = st.text_input("用户名", key="login_user")
        passwd = st.text_input("密码", type='password', key="login_pass")
        if st.button("开启仓库"):
            conn = sqlite3.connect('system_admin.db')
            c = conn.cursor()
            c.execute('SELECT * FROM userstable WHERE username =? AND password =?', (user, make_hashes(passwd)))
            if c.fetchall():
                st.session_state['logged_in'] = True
                st.session_state['user'] = user
                st.rerun()
            else: st.error("账号或密码不对哦")
        with st.expander("✨ 注册新账号"):
            nu = st.text_input("新用户名", key="reg_user")
            np = st.text_input("新密码", type='password', key="reg_pass")
            code = st.text_input("注册邀请码", key="reg_code")
            if st.button("提交注册"):
                if code == INVITE_CODE and nu and np:
                    conn = sqlite3.connect('system_admin.db')
                    c = conn.cursor()
                    c.execute('INSERT INTO userstable(username, password) VALUES (?,?)', (nu, make_hashes(np)))
                    conn.commit()
                    conn.close()
                    st.success("注册成功！")
                else: st.error("信息有误")
else:
    # --- 4. 登录后的界面 ---
    st.sidebar.write(f"👤 当前主人: **{st.session_state['user']}**")
    if st.sidebar.button("安全退出"):
        st.session_state['logged_in'] = False
        st.rerun()
    
    user_db = init_user_db(st.session_state['user'])
    
    # 根据是否是管理员动态生成标签页
    tabs_list = ["📋 查看仓库", "📥 存入宝贝", "📁 整理分类"]
    if st.session_state['user'] == ADMIN_USER:
        tabs_list.append("🛠️ 楼管后台")
    
    tabs = st.tabs(tabs_list)
    
    # --- 前三个标签页保持不变 (略，见下方整合代码) ---
    with tabs[0]: # 查看仓库
        st.header(f"🏠 {st.session_state['user']} 的空间")
        # ... (此处省略重复的查看逻辑，已整合在代码中)
        search = st.text_input("🔍 快速查找...")
        conn = sqlite3.connect(user_db)
        df = pd.read_sql_query("SELECT * FROM all_items", conn)
        if not df.empty:
            if search: df = df[df['name'].str.contains(search, case=False)]
            for idx, row in df.iterrows():
                with st.expander(f"[{row['l2']}] {row['name']} | 📅 {row['created_date']}"):
                    c_i, c_t = st.columns([1, 2])
                    if row['image']: c_i.image(row['image'])
                    with c_t:
                        st.write(f"备注: {row['note']}")
                        if st.button("🗑️ 删除", key=f"del_{row['id']}"):
                            st.warning("确定吗？")
                            if st.button("🔥 确认删", key=f"fdel_{row['id']}"):
                                conn.execute("DELETE FROM all_items WHERE id=?", (row['id'],))
                                conn.commit()
                                st.rerun()
        conn.close()

    with tabs[1]: # 存入宝贝
        st.header("📥 存入新物品")
        conn = sqlite3.connect(user_db); cat_df = pd.read_sql_query("SELECT * FROM categories", conn); conn.close()
        ca, cb = st.columns(2)
        m = ca.selectbox("大类", ["📦 现实物品", "💻 电子资料"])
        subs = cat_df[cat_df['parent_name'] == m]['child_name'].tolist()
        l2 = ca.selectbox("子类", subs if subs else ["无"])
        name = ca.text_input("名称")
        dt = cb.date_input("日期", datetime.now())
        pic = cb.file_uploader("照片", type=['jpg', 'png', 'jpeg'])
        note = st.text_area("备注")
        if st.button("🚀 准备入库"):
            st.info(f"即将存入：{name}")
            if st.button("✅ 确定"):
                img_data = compress_image(pic)
                conn = sqlite3.connect(user_db)
                conn.execute("INSERT INTO all_items (item_type, l1, l2, name, note, image, created_date) VALUES (?,?,?,?,?,?,?)",
                          (m, m, l2, name, note, img_data, dt.strftime("%Y-%m-%d")))
                conn.commit(); conn.close()
                st.success("成功！"); st.balloons()

    with tabs[2]: # 整理分类
        st.header("📁 分类管理")
        conn = sqlite3.connect(user_db); cat_df = pd.read_sql_query("SELECT * FROM categories", conn)
        c1, c2 = st.columns(2)
        new_c = c1.text_input("新分类名")
        if c1.button("确认增加"):
            conn.execute("INSERT INTO categories (parent_name, child_name) VALUES (?,?)", ("📦 现实物品", new_c))
            conn.commit(); st.rerun()
        if not cat_df.empty:
            del_cat = c2.selectbox("删分类", cat_df['child_name'].tolist())
            if c2.button("确认删除分类"):
                conn.execute("DELETE FROM categories WHERE child_name=?", (del_cat,)); conn.commit(); st.rerun()
        conn.close()

    # --- 5. 🛠️ 楼管后台 (仅 ADMIN_USER 可见) ---
    if st.session_state['user'] == ADMIN_USER:
        with tabs[3]:
            st.header("🛠️ 管理员控制台")
            st.write("您好，管理员！这里可以管理所有住户。")
            
            conn = sqlite3.connect('system_admin.db')
            users_df = pd.read_sql_query("SELECT username FROM userstable", conn)
            conn.close()
            
            st.metric("总注册户数", len(users_df))
            
            st.subheader("📋 所有住户名单")
            for u in users_df['username']:
                col_u, col_d = st.columns([3, 1])
                col_u.write(f"👤 用户名: **{u}**")
                # 管理员可以删除其他用户
                if u != ADMIN_USER:
                    if col_d.button(f"注销该户", key=f"manage_{u}"):
                        st.error(f"警告：这将永久删除 {u} 的账号和所有数据！")
                        if st.
