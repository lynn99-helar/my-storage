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
    # 物品表
    c.execute('''CREATE TABLE IF NOT EXISTS all_items 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  item_type TEXT, l1 TEXT, l2 TEXT, name TEXT, 
                  note TEXT, image BLOB, created_date TEXT)''')
    # 分类表 (存储层级关系)
    c.execute('''CREATE TABLE IF NOT EXISTS categories 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  parent_name TEXT, child_name TEXT)''')
    
    # 初始化默认分类 (如果分类表为空)
    c.execute("SELECT count(*) FROM categories")
    if c.fetchone()[0] == 0:
        default_cats = [
            ("📦 现实物品", "衣物"), ("📦 现实物品", "洗漱"), ("📦 现实物品", "电子设备"),
            ("💻 电子资料", "工作"), ("💻 电子资料", "学习"), ("💻 电子资料", "生活")
        ]
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

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user'] = ""

# --- 4. 登录逻辑 ---
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
        if st.button("创建仓库"):
            if code == INVITE_CODE:
                conn = sqlite3.connect('system_admin.db')
                c = conn.cursor()
                c.execute('INSERT INTO userstable(username, password) VALUES (?,?)', (nu, make_hashes(np)))
                conn.commit()
                conn.close()
                st.success("注册成功！")
            else: st.error("邀请码错误")
else:
    st.sidebar.write(f"👤 用户: **{st.session_state['user']}**")
    if st.sidebar.button("退出登录"):
        st.session_state['logged_in'] = False
        st.rerun()
    
    user_db = init_user_db(st.session_state['user'])
    st.title(f"✨ {st.session_state['user']} 的极简仓库")
    
    tab1, tab2, tab3 = st.tabs(["📋 仓库浏览", "📥 新增入库", "📁 分类管理"])
    
    # --- 分类管理面板 ---
    with tab3:
        st.header("📁 自定义分类管理")
        conn = sqlite3.connect(user_db)
        cat_df = pd.read_sql_query("SELECT * FROM categories", conn)
        
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("➕ 新增二级分类")
            p_cat = st.selectbox("选择所属一级分类", ["📦 现实物品", "💻 电子资料"], key="add_cat_p")
            c_cat = st.text_input("新二级分类名称 (例如: 鞋子, 电影)")
            if st.button("确认添加"):
                if c_cat:
                    conn.execute("INSERT INTO categories (parent_name, child_name) VALUES (?,?)", (p_cat, c_cat))
                    conn.commit()
                    st.success(f"已添加 {c_cat}")
                    st.rerun()
        
        with c2:
            st.subheader("➖ 删除现有分类")
            del_id = st.selectbox("选择要删除的分类", cat_df['id'].tolist(), 
                                  format_func=lambda x: f"{cat_df[cat_df['id']==x]['parent_name'].values[0]} > {cat_df[cat_df['id']==x]['child_name'].values[0]}")
            if st.button("确认删除", help="删除分类不会删除已有的物品，但新录入时将不可选"):
                conn.execute("DELETE FROM categories WHERE id=?", (del_id,))
                conn.commit()
                st.rerun()
        conn.close()

    # --- 新增入库 (使用动态分类) ---
    with tab2:
        st.header("✨ 新增物品")
        conn = sqlite3.connect(user_db)
        cat_df = pd.read_sql_query("SELECT * FROM categories", conn)
        conn.close()

        c1, c2 = st.columns(2)
        with c1:
            mode = st.selectbox("一级分类", ["📦 现实物品", "💻 电子资料"])
            # 根据一级分类动态筛选二级分类
            sub_cats = cat_df[cat_df['parent_name'] == mode]['child_name'].tolist()
            l2 = st.selectbox("二级分类", sub_cats if sub_cats else ["请先去管理面板添加分类"])
            item_name = st.text_input("物品名称")
        with c2:
            start_date = st.date_input("开始日期", datetime.now())
            uploaded_file = st.file_uploader("照片", type=['jpg', 'png', 'jpeg'])
            note = st.text_area("备注")
        
        if st.button("🚀 确认入库"):
            if item_name and sub_cats:
                img_byte = compress_image(uploaded_file)
                conn = sqlite3.connect(user_db)
                conn.execute("INSERT INTO all_items (item_type, l1, l2, name, note, image, created_date) VALUES (?,?,?,?,?,?,?)",
                          (mode, mode, l2, item_name, note, img_byte, start_date.strftime("%Y-%m-%d")))
                conn.commit()
                conn.close()
                st.success("✅ 入库成功！")
            else: st.error("请完善名称及分类信息")

    # --- 仓库浏览 ---
    with tab1:
        sc1, sc2 = st.columns([3, 1])
        search = sc1.text_input("🔍 搜索", "")
        conn = sqlite3.connect(user_db)
        df = pd.read_sql_query("SELECT * FROM all_items", conn)
        if not df.empty:
            csv = df.drop(columns=['image']).to_csv(index=False).encode('utf-8-sig')
            sc2.download_button("💾 备份数据", csv, "backup.csv")
            
            if search: df = df[df['name'].str.contains(search, case=False)]
            for index, row in df.iterrows():
                with st.expander(f"[{row['l2']}] {row['name']} - {row['created_date']}"):
                    col_img, col_txt = st.columns([1, 2])
                    if row['image']: col_img.image(row['image'])
                    col_txt.write(f"**备注:** {row['note']}")
                    if col_txt.button("🗑️ 删除", key=f"del_{row['id']}"):
                        conn.execute("DELETE FROM all_items WHERE id=?", (row['id'],))
                        conn.commit()
                        st.rerun()
        conn.close()
