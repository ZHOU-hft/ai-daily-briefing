import os
import requests
import json
from datetime import datetime

# 从 GitHub Secrets 获取密钥
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
PUSHPUSH_TOKEN = os.getenv("PUSHPUSH_TOKEN")

# 关键词配置
KEYWORDS = ["人工智能", "大模型", "合肥科技"]

def fetch_news():
    """
    模拟抓取新闻（因为 RSS 可能需要特定解析库，这里用静态数据保证流程跑通）
    如果你需要真实 RSS，可以后续集成 feedparser 库
    """
    # 这里为了稳定性，暂时使用模拟数据，确保 AI 总结环节能测试通过
    # 如果你有真实的 RSS 解析逻辑，可以替换这部分
    articles = [
        {"title": "国产大模型 DeepSeek-V3 性能全面评测", "url": "https://example.com/deepseek-v3"},
        {"title": "合肥高新区发布最新 AI 产业扶持政策", "url": "https://example.com/hefei-ai"},
        {"title": "全球算力芯片需求持续高涨", "url": "https://example.com/chip-demand"}
    ]
    return articles

def summarize_with_ai(articles):
    # 构建新闻内容字符串
    content = "\n".join([f"- {a['title']} ({a['url']})" for a in articles])
    
    prompt = f"""
你是一位专业科技编辑，请根据以下新闻列表，生成一份简洁的中文日报摘要。
要求：
1. 用 bullet points（•）列出，每条不超过 30 字；
2. 突出关键信息，去掉营销语言；
3. 不要编造未提及的内容。

新闻列表：
{content}
"""

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # ✅ 关键修复：模型名称必须是 deepseek-chat
    data = {
        "model": "deepseek-chat", 
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "stream": False
    }
    
    url = "https://api.deepseek.com/v1/chat/completions"
    
    try:
        print(f"正在请求 DeepSeek API...")
        resp = requests.post(url, headers=headers, json=data, timeout=30)
        
        # 打印状态码和响应内容，方便调试
        print(f"API Status Code: {resp.status_code}")
        print(f"API Response Body: {resp.text}")
        
        if resp.status_code != 200:
            return f"AI 服务返回错误 ({resp.status_code}): {resp.text}"
            
        result = resp.json()
        
        # 检查返回结构是否安全
        if "choices" in result and len(result["choices"]) > 0:
            summary = result["choices"][0]["message"]["content"]
            return summary.strip()
        else:
            return "AI 返回了空结果，数据结构异常。"
            
    except Exception as e:
        return f"AI 总结失败 (网络或代码错误): {str(e)}"

def send_to_wechat(summary):
    url = "http://www.pushplus.plus/send"
    payload = {
        "token": PUSHPUSH_TOKEN,
        "title": f"📰 AI 每日简报 {datetime.now().strftime('%Y-%m-%d')}",
        "content": summary,
        "template": "html"
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code == 200:
            print("✅ 推送到微信成功！")
        else:
            print(f"❌ PushPlus 返回错误: {resp.text}")
    except Exception as e:
        print(f"❌ 推送失败: {e}")

if __name__ == "__main__":
    print("🚀 开始执行每日简报任务...")
    
    # 1. 获取新闻
    articles = fetch_news()
    print(f"🔍 获取到 {len(articles)} 条新闻")
    
    # 2. AI 总结
    print("🧠 正在调用 DeepSeek 进行总结...")
    summary = summarize_with_ai(articles)
    print(f"📝 总结结果: {summary[:50]}...") # 打印前50个字
    
    # 3. 发送微信
    print("📲 正在推送到微信...")
    send_to_wechat(summary)
    
    print("✅ 任务结束")
