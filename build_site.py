import requests
import json
from datetime import datetime
import os

API_KEY = os.getenv("DEEPSEEK_API_KEY")   # **自动从 GitHub Secrets 获取**
if not API_KEY:
    raise Exception("❌ ERROR: 没有找到 DEEPSEEK_API_KEY，请检查 GitHub Secrets")

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# ===== 获取新闻（示例：腾讯新闻热点接口）=====
def fetch_news():
    print("📡 抓取今日热点新闻...")
    url = "https://i.news.qq.com/trpc.qqnews_web.kv_srv.kv_srv_http_proxy/list"
    params = {
        "sub_srv_id": "24hours",
        "offset": 0,
        "limit": 30,
    }
    resp = requests.get(url, params=params)
    data = resp.json()

    news_list = []
    for item in data.get("data", {}).get("list", []):
        news_list.append({
            "title": item.get("title"),
            "source": item.get("source"),
            "abstract": item.get("abstract"),
            "url": item.get("url")
        })
    return news_list


# ===== AI 生成趋势分析 =====
def ai_analyze(news_list):
    print("🤖 调用 DeepSeek 模型生成趋势分析...")
    titles = "\n".join([n["title"] for n in news_list])

    prompt = f"""
你是一个专业新闻分析师，请根据以下今日新闻标题，生成一份《今日趋势解读》分析报告。
要求：
- 语言简洁
- 提炼关键趋势（3~6 条）
- 指出情绪变化、关注度变化
- 给出整体判断与建议

新闻标题如下：
{titles}
    """

    body = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }

    resp = requests.post(
        "https://api.deepseek.com/chat/completions",
        headers=headers,
        data=json.dumps(body)
    )
    result = resp.json()
    return result["choices"][0]["message"]["content"]


# ===== 生成 HTML =====
def build_html(news_list, ai_text):
    print("📝 生成 HTML 页面...")

    items_html = ""
    for n in news_list:
        items_html += f"""
        <div class='item'>
            <h3>{n['title']}</h3>
            <p>{n['abstract']}</p>
            <p><em>{n['source']}</em> | <a href="{n['url']}" target="_blank">查看原文</a></p>
        </div>
        <hr>
        """

    today = datetime.now().strftime("%Y-%m-%d")

    html = f"""
    <html>
        <head>
            <meta charset='utf-8'>
            <title>今日趋势 - {today}</title>
        </head>
        <body>
            <h1>🔥 今日热点趋势（{today}）</h1>
            <h2>📊 AI 趋势解读</h2>
            <div>{ai_text}</div>
            <hr>
            <h2>📚 今日热点新闻</h2>
            {items_html}
        </body>
    </html>
    """

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print("✅ index.html 已生成！")


# ===== 主流程 =====
def main():
    news = fetch_news()
    analysis = ai_analyze(news)
    build_html(news, analysis)
    print("🎉 完成所有步骤")


if __name__ == "__main__":
    main()
