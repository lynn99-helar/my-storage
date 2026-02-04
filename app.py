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

# --- 2. 数据库逻辑 (升级分类体系) ---
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
    
    # 检查是否已有分类，如果没有，则插入更丰富的市面流行分类
    c.execute("SELECT count(*) FROM categories")
    if c.fetchone()[0] == 0:
        rich_defaults = [
            # 现实物品类
            ("📦 现实物品", "👕 穿戴配饰"), ("📦 现实物品", "💻 数码电子"), 
            ("📦 现实物品", "🏠 家居日用"), ("📦 现实物品", "💄 美妆护肤"),
            ("📦 现实物品", "📚 图书文具"), ("📦 现实物品", "🧸 收藏爱好"),
            ("📦 现实物品", "💊 医疗健康"), ("📦 现实物品", "⚽ 运动户外"),
            # 虚拟资产类
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
        img.thumbnail((800, 800))
        buf = io.BytesIO()
        if img.mode in ("RGBA", "P"): img = img.convert("RGB")
        img.save(buf, format="JPEG", quality=75)
        return buf.getvalue()
    return None

# --- 3. 页面样式 ---
st.set_page_config(page_title="Minimalist Storage", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #f9f9f9; }
    .stButton>button { border-radius: 5px; height: 3em; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

init_db()

if 'page' not in st.session_state: st.session_state['page'] = 'login'
if 'user' not in st.session_state: st.session_state['user'] = ""

def go_to(page_name):
    st.session_state['page'] = page_name
    st.rerun()

# --- 4. 路由逻辑 (登录/注册/重置) ---
if st.session_state['page'] == 'login':
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.image("https://images.unsplash.com/photo-1494438639946-1ebd1d20bf85?q=80&w=1000&auto=format&fit=crop", use_container_width=True)
        st.title("🪑 极简生活仓库")
        u = st.text_input("用户名")
        p = st.text_input("密码", type='password')
        if st.button("进入空间"):
            conn = sqlite3.connect('system_admin.db'); c = conn.cursor()
            c.execute('SELECT * FROM userstable WHERE username=? AND password=?', (u, make_hashes(p)))
            if c.fetchone():
                st.session_state['user'] = u
                go_to('main')
            else: st.error("用户名或密码错误")
        col_btn1, col_btn2 = st.columns(2)
        if col_btn1.button("✨ 开启新空间"): go_to('signup')
        if col_btn2.button("🔑 找回钥匙"): go_to('reset')

elif st.session_state['page'] == 'signup':
    st.title("✨ 注册新空间")
    nu = st.text_input("设定用户名")
    np = st.text_input("设定密码", type='password')
    nc = st.text_input("输入邀请码")
    if st.button("确认注册"):
        if nc == INVITE_CODE and nu and np:
            conn = sqlite3.connect('system_admin.db'); c = conn.cursor()
            c.execute('INSERT INTO userstable(username, password) VALUES (?,?)', (nu, make_hashes(np)))
            conn.commit(); conn.close()
            st.success("注册成功！")
            go_to('login')
    if st.button("返回"): go_to('login')

elif st.session_state['page'] == 'reset':
    st.title("🔑 重置密码")
    ru = st.text_input("用户名")
    rc = st.text_input("邀请码验证")
    rp = st.text_input("设定新密码", type='password')
    if st.button("立即重置"):
        if rc == INVITE_CODE and ru and rp:
            conn = sqlite3.connect('system_admin.db'); c = conn.cursor()
            c.execute('SELECT * FROM userstable WHERE username=?', (ru,))
            if c.fetchone():
                c.execute("UPDATE userstable SET password=? WHERE username=?", (make_hashes(rp), ru))
                conn.commit(); conn.close()
                st.success("密码重置成功！")
                go_to('login')
    if st.button("返回"): go_to('login')

elif st.session_state['page'] == 'main':
    st.sidebar.subheader(f"👤 {st.session_state['user']}")
    if st.sidebar.button("退出登录"): st.session_state['user'] = ""; go_to('login')
    
    user_db = init_user_db(st.session_state['user'])
    t_list = ["📋 浏览", "📥 入库", "📁 分类"]
    if st.session_state['user'] == ADMIN_USER: t_list.append("🛠️ 后台")
    tabs = st.tabs(t_list)

    with tabs[0]: # 浏览
        q = st.text_input("🔍 搜索物品...")
        conn = sqlite3.connect(user_db); df = pd.read_sql_query("SELECT * FROM all_items", conn)
        if not df.empty:
            if q: df = df[df['name'].str.contains(q, case=False) | df['l2'].str.contains(q, case=False)]
            for i, r in df.iterrows():
                with st.expander(f"{r['name']} ({r['l2']})"):
                    ci, ct = st.columns([1, 2])
                    if r['image']: ci.image(r['image'])
                    ct.write(f"📅 记录日期: {r['created_date']}\n\n📝 备注: {r['note']}")
                    if ct.button("🗑️ 删除记录", key=f"d_{r['id']}"):
                        st.warning("确定要删除吗？")
                        if st.button("🔥 确认删除", key=f"fd_{r['id']}"):
                            conn.execute("DELETE FROM all_items WHERE id=?", (r['id'],)); conn.commit(); st.rerun()
        conn.close()

    with tabs[1]: # 入库
        conn = sqlite3.connect(user_db); cat_df = pd.read_sql_query("SELECT * FROM categories", conn); conn.close()
        m = st.selectbox("大类", ["📦 现实物品", "💻 虚拟资产"])
        subs = cat_df[cat_df['parent_name'] == m]['child_name'].tolist()
        l2 = st.selectbox("二级分类", subs if subs else ["请先在分类页添加"])
        name = st.text_input("物品/资产名称")
        pic = st.file_uploader("上传图片(如有)", type=['jpg','png','jpeg'])
        note = st.text_area("备注信息")
        if st.button("🚀 录入仓库"):
            if name and l2:
                img = compress_image(pic)
                conn = sqlite3.connect(user_db)
                conn.execute("INSERT INTO all_items (item_type,l2,name,note,image,created_date) VALUES (?,?,?,?,?,?)",
                          (m,l2,name,note,img,datetime.now().strftime("%Y-%m-%d")))
                conn.commit(); conn.close(); st.success("已成功入库！"); st.balloons()

    with tabs[2]: # 分类管理
        conn = sqlite3.connect(user_db); c1, c2 = st.columns(2)
        p_sel = c1.selectbox("所属大类", ["📦 现实物品", "💻 虚拟资产"], key="add_cat_p")
        new_c = c1.text_input("新子分类名称 (例: 🗄️ 常用证件)")
        if c1.button("确认添加"):
            conn.execute("INSERT INTO categories (parent_name, child_name) VALUES (?,?)", (p_sel, new_c))
            conn.commit(); st.rerun()
        cat_df = pd.read_sql_query("SELECT * FROM categories", conn)
        if not cat_df.empty:
            del_c = c2.selectbox("要删除的分类", cat_df['child_name'].tolist())
            if c2.button("确认移除"):
                conn.execute("DELETE FROM categories WHERE child_name=?", (del_c,)); conn.commit(); st.rerun()
        conn.close()

    if st.session_state['user'] == ADMIN_USER:
        with tabs[3]: # 后台
            conn = sqlite3.connect('system_admin.db'); u_df = pd.read_sql_query("SELECT username FROM userstable", conn)
            st.metric("系统总用户", len(u_df))
            for u in u_df['username']:
                if u != ADMIN_USER:
                    c_u, c_d = st.columns([3, 1])
                    c_u.write(f"👤 住户: {u}")
                    if c_d.button("注销户口", key=f"m_{u}"):
                        conn.execute("DELETE FROM userstable WHERE username=?", (u,)); conn.commit()
                        try: os.remove(f"{u}_storage.db")
                        except: pass
                        st.rerun()
            conn.close()
