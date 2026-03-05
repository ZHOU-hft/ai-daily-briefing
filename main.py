import os
import requests
import json
from datetime import datetime

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
PUSHPUSH_TOKEN = os.getenv("PUSHPUSH_TOKEN")

KEYWORDS = ["人工智能", "大模型", "合肥科技"]

def fetch_news():
    rss_url = "https://rss.app/feeds/fzMN6IGpgTPnBYCs.xml"
    try:
        response = requests.get(rss_url, timeout=10)
        articles = [
            {"title": "国产大模型DeepSeek发布新版本", "url": "https://example.com/1"},
            {"title": "合肥出台AI产业扶持政策", "url": "https://example.com/2"},
            {"title": "全球芯片产能扩张加速", "url": "https://example.com/3"}
        ]
        return articles
    except:
        return [{"title": "暂无新闻", "url": "#"}]

def summarize_with_ai(articles):
    content = "\n".join([f"- {a['title']} ({a['url']})" for a in articles])
    prompt = f"""
你是一位专业科技编辑，请根据以下新闻列表，生成一份简洁的中文日报摘要。
要求：
1. 用 bullet points（•）列出，每条不超过30字；
2. 突出关键信息，去掉营销语言；
3. 不要编造未提及的内容。

新闻列表：
{content}
"""

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }
    try:
        resp = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        result = resp.json()
        summary = result["choices"][0]["message"]["content"]
        return summary.strip()
    except Exception as e:
        return f"AI总结失败: {str(e)}"

def send_to_wechat(summary):
    url = "http://www.pushplus.plus/send"
    payload = {
        "token": PUSHPUSH_TOKEN,
        "title": f"📰 AI每日简报 {datetime.now().strftime('%Y-%m-%d')}",
        "content": summary,
        "template": "html"
    }
    try:
        requests.post(url, json=payload)
        print("✅ 推送成功！")
    except Exception as e:
        print(f"❌ 推送失败: {e}")

if __name__ == "__main__":
    print("🚀 开始抓取新闻...")
    articles = fetch_news()
    print(f"🔍 获取到 {len(articles)} 条新闻")
    
    print("🧠 调用AI总结...")
    summary = summarize_with_ai(articles)
    
    print("📲 推送到微信...")
    send_to_wechat(summary)
