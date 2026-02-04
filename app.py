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
    /* 背景色：温暖的米白 */
    .stApp { background-color: #F4F1ED; color: #333333; }
    
    /* 侧边栏 */
    [data-testid="stSidebar"] { background-color: #E8E4DE; border-right: 1px solid #D1CDC7; }
    
    /* 标题颜色加深 */
    h1, h2, h3 { color: #5D544B !important; font-weight: 500 !important; }

    /* 卡片容器：模仿示意图的方框 */
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] {
        color: #8C8479 !important; /* 不点的时候显示淡淡的灰啡色 */
        font-size: 18px;
    }
    .stTabs [aria-selected="true"] {
        color: #5D544B !important; /* 选中时加深 */
        border-bottom-color: #5D544B !important;
    }

    /* 按钮：清晰深色边框 */
    .stButton>button {
        border: 2px solid #5D544B !important;
        color: #5D544B !important;
        background-color: white !important;
        border-radius: 4px !important;
        font-weight: 600;
    }
    .stButton>button:hover { background-color: #5D544B !important; color: white !important; }

    /* 输入框边框加深 */
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

# --- 4. 页面逻辑 ---
if st.session_state['page'] == 'login':
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.write("### COLLECTION")
        st.write("---")
        u = st.text_input("用户名 USERNAME")
        p = st.text_input("密码 PASSWORD", type='password')
        if st.button("登 录"):
            conn = sqlite3.connect('system_admin.db'); c = conn.cursor()
            c.execute('SELECT * FROM userstable WHERE username=? AND password=?', (u, make_hashes(p)))
            if c.fetchone():
                st.session_state['user'] = u
                go_to('main')
            else: st.error("用户名或密码错误")
        c1, c2 = st.columns(2)
        if c1.button("新注册"): go_to('signup')
        if c2.button("找回密码"): go_to('reset')

elif st.session_state['page'] == 'signup':
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.write("### 开启新空间")
        nu = st.text_input("设定用户名")
        np = st.text_input("设定密码", type='password')
        nc = st.text_input("邀请码 (666666)")
        if st.button("确认注册"):
            if nc == INVITE_CODE and nu and np:
                conn = sqlite3.connect('system_admin.db'); c = conn.cursor()
                c.execute('INSERT INTO userstable(username, password) VALUES (?,?)', (nu, make_hashes(np)))
                conn.commit(); conn.close(); go_to('login')
        if st.button("返回"): go_to('login')

elif st.session_state['page'] == 'reset':
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.write("### 重置钥匙")
        ru = st.text_input("用户名")
        rc = st.text_input("邀请码验证")
        rp = st.text_input("新密码", type='password')
        if st.button("执行更新"):
            if rc == INVITE_CODE and ru and rp:
                conn = sqlite3.connect('system_admin.db'); c = conn.cursor()
                c.execute("UPDATE userstable SET password=? WHERE username=?", (make_hashes(rp), ru))
                conn.commit(); conn.close(); go_to('login')
        if st.button("返回"): go_to('login')

elif st.session_state['page'] == 'main':
    st.sidebar.subheader(f"👤 {st.session_state['user']}")
    if st.sidebar.button("安全退出"): st.session_state['user'] = ""; go_to('login')
    
    user_db = init_user_db(st.session_state['user'])
    
    # 顶部导航
    t_names = ["📋 浏览仓库", "📥 存入宝贝", "📁 分类整理"]
    if st.session_state['user'] == ADMIN_USER: t_names.append("🛠️ 后台管理")
    tabs = st.tabs(t_names)

    with tabs[0]: # 浏览
        st.subheader("MY COLLECTION")
        q = st.text_input("🔍 搜索物品或分类...")
        conn = sqlite3.connect(user_db); df = pd.read_sql_query("SELECT * FROM all_items ORDER BY id DESC", conn)
        if not df.empty:
            if q: df = df[df['name'].str.contains(q, case=False) | df['l2'].str.contains(q, case=False)]
            for i, r in df.iterrows():
                # 每一个物品都是一个清晰的方框
                with st.container():
                    st.markdown(f"**{r['l2']} | {r['name']}**")
                    c_img, c_info = st.columns([1, 3])
                    if r['image']: c_img.image(r['image'], use_container_width=True)
                    with c_info:
                        st.write(f"📅 录入日期: {r['created_date']}")
                        st.write(f"📝 备注: {r['note']}")
                        if st.button("🗑️ 删除", key=f"del_{r['id']}"):
                            st.error("确定要移除该物品吗？")
                            if st.button("🔥 确认移除", key=f"fdel_{r['id']}"):
                                conn.execute("DELETE FROM all_items WHERE id=?", (r['id'],)); conn.commit(); st.rerun()
                    st.write("---")
        conn.close()

    with tabs[1]: # 入库 (核心改动：关联分类)
        st.subheader("NEW ENTRY")
        conn = sqlite3.connect(user_db); cat_df = pd.read_sql_query("SELECT * FROM categories", conn); conn.close()
        
        # 分栏方框布局
        col_box1, col_box2 = st.columns(2)
        with col_box1:
            st.write("📍 **基本信息**")
            m = st.selectbox("一级分类 (大类)", ["📦 现实物品", "💻 虚拟资产"])
            # 💡 联动逻辑：过滤出对应大类的子类
            filtered_subs = cat_df[cat_df['parent_name'] == m]['child_name'].tolist()
            l2 = st.selectbox("二级分类 (子类)", filtered_subs if filtered_subs else ["无"])
            name = st.text_input("物品/资产名称")
        
        with col_box2:
            st.write("📷 **详情附件**")
            pic = st.file_uploader("上传照片", type=['jpg','png','jpeg'])
            note = st.text_area("详细备注 (如购入价、存放处)")
        
        st.write("---")
        if st.button("🚀 录 入 仓 库"):
            if name and l2:
                img = compress_image(pic)
                conn = sqlite3.connect(user_db)
                conn.execute("INSERT INTO all_items (item_type,l2,name,note,image,created_date) VALUES (?,?,?,?,?,?)",
                          (m,l2,name,note,img,datetime.now().strftime("%Y-%m-%d")))
                conn.commit(); conn.close(); st.success("入库成功！"); st.balloons()

    with tabs[2]: # 分类管理
        st.subheader("LABEL MANAGEMENT")
        conn = sqlite3.connect(user_db)
        c1, c2 = st.columns(2)
        with c1:
            st.write("➕ **增加分类**")
            p_sel = st.selectbox("所属大类", ["📦 现实物品", "💻 虚拟资产"], key="p_new")
            new_c_name = st.text_input("新子分类名 (例: 🏺 古董收藏)")
            if st.button("执行增加"):
                conn.execute("INSERT INTO categories (parent_name, child_name) VALUES (?,?)", (p_sel, new_c_name))
                conn.commit(); st.rerun()
        with c2:
            st.write("➖ **删除分类**")
            cat_df_now = pd.read_sql_query("SELECT * FROM categories", conn)
            if not cat_df_now.empty:
                del_target = st.selectbox("选择要移除的分类", cat_df_now['child_name'].
