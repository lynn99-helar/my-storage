import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import os

# --- 1. 数据库初始化 ---
def init_db():
    conn = sqlite3.connect('minimalist_storage.db')
    c = conn.cursor()
    # 确保数据库有 created_date 字段
    c.execute('''CREATE TABLE IF NOT EXISTS all_items 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  item_type TEXT, l1 TEXT, l2 TEXT, name TEXT, 
                  rule TEXT, suggest TEXT, note TEXT, 
                  image BLOB, created_date TEXT)''')
    conn.commit()
    conn.close()

# --- 分类数据 ---
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

st.set_page_config(page_title="琳琳的极简生活", layout="wide")
st.title("❤️MY极简生活仓库")
init_db()

# --- 侧边栏：录入功能 ---
st.sidebar.header("✨ 新增入库")
mode = st.sidebar.radio("选择类型", ["📦 现实物品", "💻 电子资料"])

l1 = st.sidebar.selectbox("一级分类", list(DATA_MAP[mode].keys()))
l2 = st.sidebar.selectbox("二级分类", DATA_MAP[mode][l1])
item_name = st.sidebar.text_input("物品/文件名称")

# ⭐ 新功能：自主编辑使用日期
start_date = st.sidebar.date_input("开始使用/购入日期", datetime.now())

uploaded_file = st.sidebar.file_uploader("上传照片", type=['jpg', 'png', 'jpeg'])
img_byte = uploaded_file.read() if uploaded_file else None

rule, suggest, note = "", "", ""
if mode == "📦 现实物品":
    suggest = st.sidebar.text_area("收纳建议")
    note = st.sidebar.text_area("备注")
else:
    rule = st.sidebar.text_input("建议命名", f"{l1}_{item_name}_{start_date.strftime('%Y%m%d')}")
    suggest = st.sidebar.text_area("存储/备份建议")
    note = st.sidebar.text_area("备注/链接")

if st.sidebar.button("确认存入仓库"):
    if item_name:
        conn = sqlite3.connect('minimalist_storage.db')
        c = conn.cursor()
        # 将你选的 start_date 存入数据库
        c.execute("""INSERT INTO all_items 
                     (item_type, l1, l2, name, rule, suggest, note, image, created_date) 
                     VALUES (?,?,?,?,?,?,?,?,?)""",
                  (mode, l1, l2, item_name, rule, suggest, note, img_byte, start_date.strftime("%Y-%m-%d")))
        conn.commit()
        conn.close()
        st.sidebar.success(f"✅ 已存入：{item_name}")
        st.rerun()
    else:
        st.sidebar.error("请输入名称")

# --- 主界面 ---
conn = sqlite3.connect('minimalist_storage.db')
df = pd.read_sql_query("SELECT * FROM all_items", conn)
conn.close()

if not df.empty:
    # 计算已使用天数
    df['created_date_dt'] = pd.to_datetime(df['created_date'])
    df['days_used'] = (datetime.now() - df['created_date_dt']).dt.days

    # 展示列表
    for index, row in df.iterrows():
        # 这里会显示：已使用 XXX 天
        with st.expander(f"{row['item_type']} | {row['name']} (📅 已使用 {row['days_used']} 天)"):
            col1, col2 = st.columns([1, 2])
            with col1:
                if row['image']:
                    st.image(row['image'], width=200)
            with col2:
                st.write(f"**分类:** {row['l1']} - {row['l2']}")
                st.write(f"**开始日期:** {row['created_date']}")
                st.write(f"**建议:** {row['suggest']}")
                st.write(f"**备注:** {row['note']}")
                # 增加删除按钮，方便录错后重新编辑
                if st.button(f"删除这条记录", key=f"del_{row['id']}"):
                    conn = sqlite3.connect('minimalist_storage.db')
                    c = conn.cursor()
                    c.execute("DELETE FROM all_items WHERE id=?", (row['id'],))
                    conn.commit()
                    conn.close()
                    st.rerun()
else:
    st.info("仓库空空如也。")
