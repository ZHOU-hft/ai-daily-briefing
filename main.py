import os
import requests
import feedparser
import json
from datetime import datetime

# 加载配置与状态
def load_config():
    with open('config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def load_status():
    if os.path.exists('status.json'):
        with open('status.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"is_active": True, "last_run": None}

def save_status(status):
    with open('status.json', 'w', encoding='utf-8') as f:
        json.dump(status, f, ensure_ascii=False, indent=2)

CONFIG = load_config()
STATUS = load_status()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
PUSHPUSH_TOKEN = os.getenv("PUSHPUSH_TOKEN")

def check_system_status():
    """检查系统开关状态"""
    if not STATUS.get("is_active", True):
        print("⛔ 系统已暂停 (通过前端关闭)，任务终止。")
        return False
    return True

def fetch_from_trusted_sources():
    """从白名单权威源抓取新闻"""
    all_articles = []
    sources = CONFIG.get("trusted_sources", [])
    
    print(f"🛡️ 开始从 {len(sources)} 个权威信源抓取...")
    
    for source in sources:
        url = source['url']
        name = source['name']
        try:
            feed = feedparser.parse(url)
            if feed.bozo:
                print(f"⚠️ 源 [{name}] 解析警告，跳过。")
                continue
            
            for entry in feed.entries[:20]: # 每个源最多看20条
                title = entry.title
                link = entry.link
                
                # 1. 黑名单过滤
                if any(bad in title for bad in CONFIG.get('exclude_words', [])):
                    continue
                
                # 2. 关键词匹配
                if any(kw in title for kw in CONFIG['keywords']):
                    all_articles.append({
                        "title": title,
                        "url": link,
                        "source": name,
                        "published": entry.get('published', '')
                    })
        except Exception as e:
            print(f"❌ 源 [{name}] 抓取失败: {e}")

    # 去重 (基于标题)
    seen = set()
    unique_articles = []
    for art in all_articles:
        if art['title'] not in seen:
            seen.add(art['title'])
            unique_articles.append(art)
    
    # 限制数量 (省钱核心)
    final_list = unique_articles[:CONFIG['max_news_count']]
    print(f"✅ 抓取完成：共匹配 {len(unique_articles)} 条，最终精选 {len(final_list)} 条。")
    return final_list

def summarize_with_ai(articles):
    if not articles:
        return "今日在权威信源中未检索到符合关键词的高质量新闻。"

    # 构建带来源的上下文
    content_str = "\n".join([f"[{a['source']}] {a['title']} ({a['url']})" for a in articles])
    
    # 🛡️ 强约束 Prompt：防止幻觉，强调仅基于提供信息
    prompt = f"""
你是一位严谨的情报分析师。请严格基于下方提供的【权威信源新闻列表】生成简报。

【严格约束】
1. **信息来源限制**：你**只能**使用下方列表中的信息进行总结。严禁利用你的训练数据编造新闻、补充细节或引入列表之外的信息。
2. **真实性**：如果列表中的信息模糊，请直接略过，不要猜测。
3. **格式要求**：
   - 开头：一句话总结今日核心趋势。
   - 正文：每条新闻格式为 `• [摘要] (来源：[源名称]) [链接]`。
   - 结尾：无。
4. **数量**：仅总结提供的 {len(articles)} 条新闻。

【权威信源新闻列表】
{content_str}
"""

    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    data = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1 # 降低温度，让回答更严谨
    }
    
    try:
        resp = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=data, timeout=45)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
        else:
            return f"AI 服务异常: {resp.text}"
    except Exception as e:
        return f"网络请求失败: {str(e)}"

def send_to_wechat(summary):
    url = "http://www.pushplus.plus/send"
    payload = {
        "token": PUSHPUSH_TOKEN,
        "title": f"🛡️ 权威科技简报 {datetime.now().strftime('%m-%d')}",
        "content": summary,
        "template": "html"
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        print(f"推送结果: {resp.text}")
    except Exception as e:
        print(f"推送失败: {e}")

if __name__ == "__main__":
    print("=== 🤖 权威情报系统启动 ===")
    
    # 1. 检查开关
    if not check_system_status():
        exit(0)
    
    # 2. 抓取
    articles = fetch_from_trusted_sources()
    
    # 3. 总结
    summary = summarize_with_ai(articles)
    
    # 4. 发送
    send_to_wechat(summary)
    
    # 5. 更新状态记录
    status = load_status()
    status["last_run"] = datetime.now().isoformat()
    save_status(status)
    
    print("=== 🏁 任务结束 ===")
