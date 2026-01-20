import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import os

# --- 1. 数据库初始化（增加日期、图片、命名规则字段） ---
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

# --- 2. 自动生成命名（极简规则） ---
def generate_name(l1, name):
    date_str = datetime.now().strftime("%Y%m%d")
    return f"{l1}_{name}_{date_str}"

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

st.set_page_config(page_title="极简仓库专业版", layout="wide")
st.title("MY极简全能仓库")
init_db()

# --- 侧边栏：功能录入 ---
st.sidebar.header("✨ 新增入库")
mode = st.sidebar.radio("选择管理对象", ["📦 现实物品", "💻 电子资料"])

l1 = st.sidebar.selectbox("一级分类", list(DATA_MAP[mode].keys()))
l2 = st.sidebar.selectbox("二级分类", DATA_MAP[mode][l1])
item_name = st.sidebar.text_input("物品/文件名称")

# 增加：上传照片
uploaded_file = st.sidebar.file_uploader("上传照片 (如果是电子资料可不传)", type=['jpg', 'png', 'jpeg'])
img_byte = uploaded_file.read() if uploaded_file else None

rule, suggest, note = "", "", ""
if mode == "📦 现实物品":
    suggest = st.sidebar.text_area("收纳建议")
    note = st.sidebar.text_area("备注")
else:
    # 自动生成命名建议
    auto_name = generate_name(l1, item_name) if item_name else ""
    rule = st.sidebar.text_input("建议命名 (已自动生成)", auto_name)
    suggest = st.sidebar.text_area("存储/备份建议")
    note = st.sidebar.text_area("链接/路径")

if st.sidebar.button("确认存入仓库"):
    if item_name:
        conn = sqlite3.connect('minimalist_storage.db')
        c = conn.cursor()
        c.execute("""INSERT INTO all_items 
                     (item_type, l1, l2, name, rule, suggest, note, image, created_date) 
                     VALUES (?,?,?,?,?,?,?,?,?)""",
                  (mode, l1, l2, item_name, rule, suggest, note, img_byte, datetime.now().strftime("%Y-%m-%d")))
        conn.commit()
        conn.close()
        st.sidebar.success(f"✅ 已记录：{item_name}")
    else:
        st.sidebar.error("请输入名称")

# --- 主界面 ---
tabs = st.tabs(["📊 仓库概览", "🔍 深度搜索"])

with tabs[0]:
    conn = sqlite3.connect('minimalist_storage.db')
    df = pd.read_sql_query("SELECT * FROM all_items", conn)
    conn.close()

    if not df.empty:
        # 断舍离提醒：判断入库是否超过180天
        df['created_date'] = pd.to_datetime(df['created_date'])
        df['days_kept'] = (datetime.now() - df['created_date']).dt.days
        
        # 简单展示
        for index, row in df.iterrows():
            with st.expander(f"{row['item_type']} | {row['l1']} - {row['name']} (已存放 {row['days_kept']} 天)"):
                col1, col2 = st.columns([1, 2])
                with col1:
                    if row['image']:
                        st.image(row['image'], width=200)
                    else:
                        st.write("📷 无图片")
                with col2:
                    st.write(f"**二级分类:** {row['l2']}")
                    st.write(f"**收纳/备份建议:** {row['suggest']}")
                    st.info(f"**备注:** {row['note']}")
                    if row['days_kept'] > 180:
                        st.warning("⚠️ 此物品已入库超过半年，考虑一下是否还需要它？")
    else:
        st.info("仓库是空的。")

with tabs[1]:
    st.write("这里可以根据名称、分类或备注进行全局搜索。")
    # (搜索逻辑同前，您可以继续使用之前的 DataFrame 过滤逻辑)
