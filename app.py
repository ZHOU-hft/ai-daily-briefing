import streamlit as st
import json
import os
import re

st.set_page_config(page_title="AI 情报控制台", layout="centered")
st.title("🛡️ 权威 AI 情报控制台")

# 文件路径
CONFIG_FILE = 'config.json'
STATUS_FILE = 'status.json'

# 初始化状态文件
if not os.path.exists(STATUS_FILE):
    with open(STATUS_FILE, 'w', encoding='utf-8') as f:
        json.dump({"is_active": True, "last_run": "从未运行"}, f)

def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

config = load_json(CONFIG_FILE)
status = load_json(STATUS_FILE)

# --- 核心控制区 ---
st.subheader("⚙️ 系统运行状态")
col1, col2 = st.columns([1, 3])

with col1:
    is_active = status.get("is_active", True)
    # 开关按钮
    new_status = st.toggle("🟢 工作流启用", value=is_active)
    
    if new_status != is_active:
        status["is_active"] = new_status
        save_json(STATUS_FILE, status)
        st.rerun()

with col2:
    if status["is_active"]:
        st.success("系统正在运行。每日定时任务将正常执行。")
    else:
        st.error("⛔ 系统已暂停。定时任务将跳过，不消耗任何 Token。")
    
    st.caption(f"上次运行时间: {status.get('last_run', '无记录')}")

st.divider()

# --- 配置编辑区 ---
st.subheader("📝 策略配置")

# 关键词
keywords_input = st.text_area(
    "🔍 关注关键词 (逗号分隔)",
    value=", ".join(config.get('keywords', [])),
    height=80
)

# 权威源管理
st.markdown("#### 🛡️ 权威信源白名单 (仅从此处获取)")
sources_text = ""
for src in config.get('trusted_sources', []):
    sources_text += f"{src['name']}: {src['url']}\n"

sources_input = st.text_area(
    "格式: 源名称: RSS链接 (每行一个)",
    value=sources_text,
    height=150
)

# 其他设置
col_a, col_b = st.columns(2)
with col_a:
    max_count = st.slider("💰 最大总结条数 (成本控制)", 1, 10, config.get('max_news_count', 5))
with col_b:
    cron_time = st.text_input("⏰ 定时任务 (Cron UTC)", value=config.get('schedule_time_utc', "0 1 * * *"))

# 保存逻辑
if st.button("💾 保存所有更改"):
    # 1. 更新 Config
    new_keywords = [k.strip() for k in keywords_input.split(',') if k.strip()]
    
    # 解析源列表
    new_sources = []
    for line in sources_input.split('\n'):
        if ':' in line:
            parts = line.split(':', 1)
            if len(parts) == 2:
                name = parts[0].strip()
                url = parts[1].strip()
                if name and url:
                    new_sources.append({"name": name, "url": url})
    
    new_config = {
        "system_status": "active",
        "keywords": new_keywords,
        "max_news_count": int(max_count),
        "schedule_time_utc": cron_time.strip(),
        "trusted_sources": new_sources,
        "exclude_words": config.get('exclude_words', [])
    }
    
    save_json(CONFIG_FILE, new_config)
    
    # 2. 自动更新 Workflow 的 Cron
    workflow_path = '.github/workflows/daily.yml'
    if os.path.exists(workflow_path):
        with open(workflow_path, 'r', encoding='utf-8') as f:
            content = f.read()
        pattern = r"cron:\s*'[^\']*'"
        replacement = f"cron: '{cron_time.strip()}'"
        new_content = re.sub(pattern, replacement, content)
        with open(workflow_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
    
    st.success("✅ 配置已保存！工作流状态和定时时间已更新。")
    st.info("💡 提示：如果刚刚关闭了开关，下一次定时任务将自动跳过。")

# 侧边栏
st.sidebar.header("📘 操作指南")
st.sidebar.markdown("""
1. **关闭工作流**：点击右上角开关，系统将立即停止响应定时任务，**0 Token 消耗**。
2. **权威信源**：只添加官方或高信誉媒体的 RSS 链接。
3. **安全性**：AI 被指令严禁编造信息，仅基于提供的链接总结。
""")
