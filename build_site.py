import os
import requests
from datetime import datetime

OUTPUT_DIR = "output"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "index.html")


def get_mock_news():
    """
    先用一些示例数据，后面你愿意可以再换成真正的爬虫结果
    """
    news = [
        {
            "title": "大模型应用加速落地，AI 工具进入日常工作",
            "summary": "越来越多公司在内部接入 AI 助手，用来写文案、写代码、做报表。",
            "source": "知乎热榜",
            "url": "https://www.example.com/ai-tools",
        },
        {
            "title": "互联网公司持续裁员与重组，重点投入 AI 方向",
            "summary": "多家厂商宣布组织调整，将更多资源投入到大模型与搜索增强上。",
            "source": "微博热搜",
            "url": "https://www.example.com/reorg",
        },
        {
            "title": "短视频与直播电商依然火爆，但监管持续收紧",
            "summary": "平台在加强内容审核，鼓励更加“长效价值”的内容创作。",
            "source": "B 站热门",
            "url": "https://www.example.com/shortvideo",
        },
    ]

    # 为了做“多平台对比”，给每条新闻一个“热度分数”
    for i, n in enumerate(news):
        n["score"] = 80 - i * 10
    return news


def call_deepseek_summary(news_list):
    """
    调用 DeepSeek，生成《今日趋势解读》
    """
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        return "（未配置 DEEPSEEK_API_KEY，暂时无法生成 AI 总结。）"

    titles = [f"{n['source']}：{n['title']}" for n in news_list]
    prompt = (
        "你是一名互联网趋势分析师。下面是今天来自不同平台的热点标题，"
        "请用中文写一段 150 字左右的《今日趋势解读》，"
        "要求：1）整体概括今天大家在关心什么；2）指出一个你认为未来几天可能持续发酵的方向：\n\n"
        + "\n".join(titles)
    )

    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=20)
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"调用 DeepSeek 失败：{e}"


def build_html(news_list, ai_summary):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    labels = [n["source"] for n in news_list]
    scores = [n["score"] for n in news_list]
    titles = [n["title"] for n in news_list]

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8" />
    <title>TrendRadar - 今日热点趋势</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui;
            margin: 0;
            padding: 20px;
            background: #0f172a;
            color: #e5e7eb;
        }}
        h1, h2 {{
            margin-bottom: 10px;
        }}
        a {{ color: #38bdf8; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .grid {{
            display: grid;
            grid-template-columns: 2fr 1.5fr;
            gap: 20px;
        }}
        .card {{
            background: rgba(15,23,42,0.9);
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.4);
        }}
        .tag {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 999px;
            font-size: 12px;
            background: #1e293b;
            margin-right: 6px;
        }}
        .news-item + .news-item {{
            margin-top: 12px;
            padding-top: 12px;
            border-top: 1px solid #1f2937;
        }}
        .pill {{
            display: inline-block;
            padding: 2px 10px;
            border-radius: 999px;
            background: #1e293b;
            font-size: 12px;
            margin-left: 8px;
        }}
    </style>
</head>
<body>
    <h1>🔥 TrendRadar 今日热点趋势</h1>
    <p>最后更新：{now}</p>

    <div class="grid">
        <div class="card">
            <h2>📌 今日热点新闻</h2>
            {"".join(
                f'<div class="news-item"><div><span class="tag">{n["source"]}</span>'
                f'<strong><a href="{n["url"]}" target="_blank">{n["title"]}</a></strong></div>'
                f'<div style="margin-top:4px;font-size:14px;color:#9ca3af;">{n["summary"]}</div>'
                '</div>'
                for n in news_list
            )}
        </div>

        <div class="card">
            <h2>🧠 AI 生成 · 今日趋势解读</h2>
            <div style="font-size:14px;line-height:1.7;white-space:pre-wrap;">
                {ai_summary}
            </div>
        </div>
    </div>

    <div class="grid" style="margin-top:20px;">
        <div class="card">
            <h2>📈 各平台热度对比</h2>
            <canvas id="heatChart" height="120"></canvas>
        </div>
        <div class="card">
            <h2>☁ 热点词云（简单版）</h2>
            {"".join(
                f'<span style="font-size:{20 + i*4}px;margin-right:10px;color:#bfdbfe;">{t.split("：")[-1][:6]}</span>'
                for i, t in enumerate(titles)
            )}
        </div>
    </div>

    <script>
        const ctx = document.getElementById('heatChart').getContext('2d');
        new Chart(ctx, {{
            type: 'bar',
            data: {{
                labels: {labels},
                datasets: [{{
                    label: '热度评分（示例）',
                    data: {scores},
                    backgroundColor: ['#38bdf8','#a855f7','#f97316'],
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{ labels: {{ color: '#e5e7eb' }} }},
                }},
                scales: {{
                    x: {{ ticks: {{ color: '#e5e7eb' }} }},
                    y: {{ ticks: {{ color: '#e5e7eb' }} }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ 已生成 {OUTPUT_FILE}")


def main():
    news_list = get_mock_news()
    ai_summary = call_deepseek_summary(news_list)
    build_html(news_list, ai_summary)


if __name__ == "__main__":
    main()
