import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import hashlib
from PIL import Image
import io

# --- 1. 安全配置 ---
INVITE_CODE = "pl"

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# --- 2. 数据库初始化 ---
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

st.set_page_config(page_title="❤️我的极简私人仓库", layout="wide")
init_db()

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user'] = ""

# --- 3. 登录界面 (带图片) ---
if not st.session_state['logged_in']:
    # 这里您可以换成任何您喜欢的图片网址
    welcome_img = "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?q=80&w=1000&auto=format&fit=crop"
    
    col_main1, col_main2 = st.columns([1.5, 1])
    
    with col_main1:
        st.image(welcome_img, caption="极简生活，从有序开始", use_container_width=True)
        st.title("❤️ 欢迎来到您的私人保险箱")
        st.info("请在左侧侧边栏输入账号信息进入。")

    with st.sidebar:
        st.title("🔐 登录验证")
        user = st.text_input("用户名", key="login_user")
        passwd = st.text_input("密码", type='password', key="login_pass")
        if st.button("开启仓库", key="login_btn"):
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
            if st.button("创建并注册", key="reg_btn"):
                if code == INVITE_CODE and nu and np:
                    conn = sqlite3.connect('system_admin.db')
                    c = conn.cursor()
                    c.execute('INSERT INTO userstable(username, password) VALUES (?,?)', (nu, make_hashes(np)))
                    conn.commit()
                    conn.close()
                    st.success("注册成功！")
                else: st.error("请填全信息且邀请码正确")
else:
    # --- 登录后的界面 ---
    st.sidebar.write(f"👤 当前主人: **{st.session_state['user']}**")
    if st.sidebar.button("安全退出"):
        st.session_state['logged_in'] = False
        st.rerun()
    
    user_db = init_user_db(st.session_state['user'])
    st.title(f"🏠 {st.session_state['user']} 的极简空间")
    
    tab1, tab2, tab3 = st.tabs(["📋 查看仓库", "📥 存入宝贝", "📁 整理分类"])
    
    # --- 分类管理 ---
    with tab3:
        st.subheader("📁 自定义您的分类")
        conn = sqlite3.connect(user_db)
        cat_df = pd.read_sql_query("SELECT * FROM categories", conn)
        c1, c2 = st.columns(2)
        with c1:
            p_cat = st.selectbox("一级分类", ["📦 现实物品", "💻 电子资料"], key="mgr_p")
            new_c = st.text_input("新子分类名", key="mgr_c")
            if st.button("确认增加"):
                if new_c:
                    conn.execute("INSERT INTO categories (parent_name, child_name) VALUES (?,?)", (p_cat, new_c))
                    conn.commit()
                    st.rerun()
        with c2:
            if not cat_df.empty:
                del_cat = st.selectbox("要删除的子分类", cat_df['child_name'].tolist())
                if st.button("⚠️ 确定删除分类"):
                    conn.execute("DELETE FROM categories WHERE child_name=?", (del_cat,))
                    conn.commit()
                    st.rerun()
        conn.close()

    # --- 新增入库 ---
    with tab2:
        st.subheader("📥 存入新物品")
        conn = sqlite3.connect(user_db)
        cat_df = pd.read_sql_query("SELECT * FROM categories", conn)
        conn.close()
        
        ca, cb = st.columns(2)
        with ca:
            m = st.selectbox("选择大类", ["📦 现实物品", "💻 电子资料"], key="add_m")
            subs = cat_df[cat_df['parent_name'] == m]['child_name'].tolist()
            l2 = st.selectbox("选择子类", subs if subs else ["请先增加分类"])
            name = st.text_input("物品名称")
        with cb:
            dt = st.date_input("日期", datetime.now())
            pic = st.file_uploader("拍摄或上传照片", type=['jpg', 'png', 'jpeg'])
            note = st.text_area("备注")
            
        if st.button("🚀 准备入库"):
            st.warning(f"即将存入：{name} 到 {l2}，确认吗？")
            if st.button("✅ 确定入库"):
                img_data = compress_image(pic)
                conn = sqlite3.connect(user_db)
                conn.execute("INSERT INTO all_items (item_type, l1, l2, name, note, image, created_date) VALUES (?,?,?,?,?,?,?)",
                          (m, m, l2, name, note, img_data, dt.strftime("%Y-%m-%d")))
                conn.commit()
                conn.close()
                st.success("存入成功！")
                st.balloons()

    # --- 仓库展示 ---
    with tab1:
        search = st.text_input("🔍 快速查找...")
        conn = sqlite3.connect(user_db)
        df = pd.read_sql_query("SELECT * FROM all_items", conn)
        
        if not df.empty:
            if search: df = df[df['name'].str.contains(search, case=False)]
            
            for idx, row in df.iterrows():
                with st.expander(f"[{row['l2']}] {row['name']} | 📅 {row['created_date']}"):
                    c_i, c_t = st.columns([1, 2])
                    with c_i:
                        if row['image']: st.image(row['image'])
                        else: st.write("📷 暂无图片")
                    with c_t:
                        st.write(f"**详细备注:** {row['note']}")
                        if st.button("🗑️ 删除", key=f"del_{row['id']}"):
                            st.error("确定要删除吗？")
                            if st.button("🔥 确认永久删除", key=f"fdel_{row['id']}"):
                                conn.execute("DELETE FROM all_items WHERE id=?", (row['id'],))
                                conn.commit()
                                st.rerun()
        conn.close()
