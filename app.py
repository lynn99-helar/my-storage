import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import hashlib
from PIL import Image
import io

# --- 1. 安全与加密 ---
INVITE_CODE = "pl"  # 👈 这是您的注册邀请码，可以修改

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
                  item_type TEXT, name TEXT, note TEXT, 
                  image BLOB, created_date TEXT)''')
    conn.commit()
    conn.close()
    return db_name

# --- 3. 图片处理优化 (专业程序员必做) ---
def compress_image(uploaded_file):
    if uploaded_file is not None:
        img = Image.open(uploaded_file)
        # 如果图片很大，自动调整尺寸
        img.thumbnail((800, 800)) 
        buf = io.BytesIO()
        # 转换为高压缩率的 JPEG
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(buf, format="JPEG", quality=70)
        return buf.getvalue()
    return None

# --- 页面配置 ---
st.set_page_config(page_title="❤️极简生活私密仓库", layout="wide")
init_db()

# --- 4. 登录状态管理 ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user'] = ""

# --- 5. 侧边栏逻辑 ---
if not st.session_state['logged_in']:
    st.sidebar.title("🔐 私人保险箱")
    user = st.sidebar.text_input("用户名")
    passwd = st.sidebar.text_input("密码", type='password')
    
    col1, col2 = st.sidebar.columns(2)
    if col1.button("登录"):
        conn = sqlite3.connect('system_admin.db')
        c = conn.cursor()
        c.execute('SELECT * FROM userstable WHERE username =? AND password =?', (user, make_hashes(passwd)))
        if c.fetchall():
            st.session_state['logged_in'] = True
            st.session_state['user'] = user
            st.rerun()
        else:
            st.sidebar.error("账号或密码错误")

    with st.sidebar.expander("✨ 第一次使用？点击注册"):
        new_user = st.text_input("想用的用户名")
        new_passwd = st.text_input("想用的密码", type='password')
        code = st.text_input("输入注册邀请码")
        if st.button("立即创建仓库"):
            if code == INVITE_CODE:
                conn = sqlite3.connect('system_admin.db')
                c = conn.cursor()
                c.execute('INSERT INTO userstable(username, password) VALUES (?,?)', (new_user, make_hashes(new_passwd)))
                conn.commit()
                conn.close()
                st.success("注册成功！请在上方登录")
            else:
                st.error("邀请码不对哦")
else:
    # 登录成功后，缩小并只显示退出按钮
    st.sidebar.write(f"👤 当前用户: **{st.session_state['user']}**")
    if st.sidebar.button("退出登录"):
        st.session_state['logged_in'] = False
        st.rerun()
    
    # --- 登录后的核心功能 ---
    user_db = init_user_db(st.session_state['user'])
    st.title(f"✨ {st.session_state['user']} 的私人极简仓库")
    
    # 分页标签
    tab1, tab2 = st.tabs(["📋 仓库浏览", "📥 新增入库"])
    
    with tab2:
        st.header("✨ 新增物品")
        c1, c2 = st.columns(2)
        with c1:
            item_name = st.text_input("物品名称")
            mode = st.selectbox("类型", ["📦 现实物品", "💻 电子资料"])
        with c2:
            start_date = st.date_input("开始日期", datetime.now())
            uploaded_file = st.file_uploader("上传照片", type=['jpg', 'png', 'jpeg'])
        
        note = st.text_area("备注信息")
        
        if st.button("🚀 确认存入"):
            if item_name:
                img_byte = compress_image(uploaded_file)
                conn = sqlite3.connect(user_db)
                c = conn.cursor()
                c.execute("INSERT INTO all_items (item_type, name, note, image, created_date) VALUES (?,?,?,?,?)",
                          (mode, item_name, note, img_byte, start_date.strftime("%Y-%m-%d")))
                conn.commit()
                conn.close()
                st.success("✅ 已存入！")
            else:
                st.error("名字不能为空")

    with tab1:
        # 搜索与导出
        sc1, sc2 = st.columns([3, 1])
        with sc1:
            search = st.text_input("🔍 搜索物品", "")
        
        conn = sqlite3.connect(user_db)
        df = pd.read_sql_query("SELECT * FROM all_items", conn)
        conn.close()

        with sc2:
            if not df.empty:
                # 导出备份功能
                csv = df.drop(columns=['image']).to_csv(index=False).encode('utf-8-sig')
                st.download_button("💾 导出数据备份", csv, "my_storage_backup.csv", "text/csv")

        if not df.empty:
            if search:
                df = df[df['name'].str.contains(search, case=False)]
            
            for index, row in df.iterrows():
                with st.expander(f"{row['name']} ({row['created_date']})"):
                    col_img, col_txt = st.columns([1, 2])
                    with col_img:
                        if row['image']: st.image(row['image'])
                    with col_txt:
                        st.write(f"**类型:** {row['item_type']}")
                        st.write(f"**备注:** {row['note']}")
                        if st.button("🗑️ 删除记录", key=f"del_{row['id']}"):
                            conn = sqlite3.connect(user_db)
                            c = conn.cursor()
                            c.execute("DELETE FROM all_items WHERE id=?", (row['id'],))
                            conn.commit()
                            conn.close()
                            st.rerun()
