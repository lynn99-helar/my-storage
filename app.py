import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- 1. 数据库初始化 ---
def init_db():
    conn = sqlite3.connect('minimalist_storage.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS all_items 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  item_type TEXT, l1 TEXT, l2 TEXT, name TEXT, 
                  rule TEXT, suggest TEXT, note TEXT, 
                  image BLOB, created_date TEXT)''')
    conn.commit()
    conn.close()

DATA_MAP = {
    "📦 现实物品": {
        "穿戴配饰类": ["衣物", "鞋履", "配饰", "其他"],
        "日用消耗类": ["洗漱护理", "清洁用品", "餐厨用品", "其他"],
        "数码工具类": ["电子设备", "配件耗材", "维修工具", "其他"],
        "运动健康类": ["健身装备", "健康用品", "其他"],
        "收藏纪念类": ["藏品手办", "书籍画册", "其他"],
        "其他": ["其他"]
    },
    "💻 电子资料": {
        "工作场景": ["项目资料", "客户相关", "日常办公", "其他"],
        "学习场景": ["技能提升", "考证备考", "兴趣拓展", "其他"],
        "生活场景": ["家庭事务", "旅行出行", "健身健康", "其他"],
        "休闲场景": ["娱乐影音", "社交记录", "其他"],
        "其他": ["其他"]
    }
}

st.set_page_config(page_title="❤️MY极简生活仓库", layout="wide")
st.title("❤️MY极简生活仓库")
init_db()

# --- 侧边栏：录入功能 ---
st.sidebar.header("✨ 新增入库")
mode = st.sidebar.radio("选择类型", ["📦 现实物品", "💻 电子资料"])
l1 = st.sidebar.selectbox("一级分类", list(DATA_MAP[mode].keys()))
l2 = st.sidebar.selectbox("二级分类", DATA_MAP[mode][l1])
item_name = st.sidebar.text_input("物品/文件名称")
start_date = st.sidebar.date_input("开始使用/购入日期", datetime.now())
uploaded_file = st.sidebar.file_uploader("上传照片", type=['jpg', 'png', 'jpeg'], key="main_upload")
img_byte = uploaded_file.read() if uploaded_file else None

if st.sidebar.button("确认存入仓库"):
    if item_name:
        conn = sqlite3.connect('minimalist_storage.db')
        c = conn.cursor()
        c.execute("""INSERT INTO all_items (item_type, l1, l2, name, rule, suggest, note, image, created_date) 
                     VALUES (?,?,?,?,?,?,?,?,?)""",
                  (mode, l1, l2, item_name, "", "", "", img_byte, start_date.strftime("%Y-%m-%d")))
        conn.commit()
        conn.close()
        st.sidebar.success(f"✅ 已存入：{item_name}")
        st.rerun()

# --- 主界面 ---
search_query = st.text_input("🔍 搜索物品（输入名称、分类或备注）", "")

conn = sqlite3.connect('minimalist_storage.db')
df = pd.read_sql_query("SELECT * FROM all_items", conn)
conn.close()

if not df.empty:
    if search_query:
        df = df[df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)]

    df['created_date_dt'] = pd.to_datetime(df['created_date'])
    df['days_used'] = (datetime.now() - df['created_date_dt']).dt.days

    for index, row in df.iterrows():
        with st.expander(f"{row['item_type']} | {row['name']} (📅 已使用 {row['days_used']} 天)"):
            edit_key = f"edit_{row['id']}"
            if edit_key not in st.session_state:
                st.session_state[edit_key] = False

            if not st.session_state[edit_key]:
                col1, col2 = st.columns([1, 2])
                with col1:
                    if row['image']:
                        st.image(row['image'], width=200)
                    else:
                        st.write("📷 暂无照片")
                with col2:
                    st.write(f"**分类:** {row['l1']} - {row['l2']}")
                    st.write(f"**开始日期:** {row['created_date']}")
                    st.write(f"**备注:** {row['note']}")
                    if st.button("📝 修改资料", key=f"btn_edit_{row['id']}"):
                        st.session_state[edit_key] = True
                        st.rerun()
            else:
                # --- 编辑模式（含图片编辑） ---
                st.info("🔧 正在编辑信息...")
                new_name = st.text_input("名称", row['name'], key=f"inp_name_{row['id']}")
                new_date = st.date_input("开始日期", datetime.strptime(row['created_date'], "%Y-%m-%d"), key=f"inp_date_{row['id']}")
                new_note = st.text_area("备注", row['note'], key=f"inp_note_{row['id']}")
                
                # 图片编辑区
                st.write("🖼️ **图片管理**")
                if row['image']:
                    st.image(row['image'], width=100, caption="当前照片")
                new_img_file = st.file_uploader("点击上传新照片（不上传则保留原图）", type=['jpg', 'png', 'jpeg'], key=f"up_{row['id']}")
                
                ec1, ec2, ec3 = st.columns(3)
                if ec1.button("💾 保存修改", key=f"btn_save_{row['id']}"):
                    # 如果传了新图，就用新图；否则用原来的图
                    final_img = new_img_file.read() if new_img_file else row['image']
                    
                    conn = sqlite3.connect('minimalist_storage.db')
                    c = conn.cursor()
                    c.execute("""UPDATE all_items SET name=?, created_date=?, note=?, image=? WHERE id=?""",
                              (new_name, new_date.strftime("%Y-%m-%d"), new_note, final_img, row['id']))
                    conn.commit()
                    conn.close()
                    st.session_state[edit_key] = False
                    st.rerun()
                
                if ec2.button("❌ 取消", key=f"btn_cancel_{row['id']}"):
                    st.session_state[edit_key] = False
                    st.rerun()
                
                if ec3.button("🗑️ 删除记录", key=f"btn_del_{row['id']}"):
                    conn = sqlite3.connect('minimalist_storage.db')
                    c = conn.cursor()
                    c.execute("DELETE FROM all_items WHERE id=?", (row['id'],))
                    conn.commit()
                    conn.close()
                    st.rerun()
else:
    st.info("仓库里还没有东西。")
