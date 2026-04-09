# 路径：AI_News_Agency/tools/rss_scraper.py

import feedparser
from typing import List, Dict
from langchain_core.tools import tool

# 💡 架构优化：支持多个信息源，扩大我们的“漏斗”顶部
RSS_URLS =[
    "https://www.solidot.org/index.rss",               # Solidot 极客资讯 (中文，极度稳定)
    "https://techcrunch.com/feed/",                    # TechCrunch 最新官方源 (英文全球科技)
    "https://sspai.com/feed",  # 少数派（国内直连，内容极佳）
    # 提示：如果你有特定的 AI 资讯源，只要是标准的 RSS 链接，都可以往这里加！
]


@tool
def fetch_tech_news(max_news_per_source: int = 15) -> List[Dict]:
    """
    必须调用此工具获取今天最新的科技与 AI 行业新闻。
    返回一个结构化的新闻字典列表，包含 title, link, summary, source。
    """
    # 为什么返回 List[Dict] 而不是直接返回字符串？
    # 答：结构化数据才能让下游的 Agent 针对每一条新闻进行独立的打分和过滤！

    all_news = []

    for url in RSS_URLS:
        print(f"📡[雷达工具] 正在扫描新闻源: {url} ...")
        try:
            feed = feedparser.parse(url)

            # 容错处理：如果抓取失败，跳过这个源继续下一个
            if not feed.entries:
                print(f"⚠️ [警告] 无法从 {url} 获取数据。")
                continue

            for entry in feed.entries[:max_news_per_source]:
                # 清洗和组装数据
                title = entry.get("title", "无标题")
                link = entry.get("link", "无链接")
                # 简单清洗 HTML 标签（实际项目中可能需要用到 BeautifulSoup 深度清洗）
                summary_raw = entry.get("summary", "无摘要")
                summary = summary_raw[:300] + "..." if len(summary_raw) > 300 else summary_raw

                # 构建单个新闻的字典结构
                news_dict = {
                    "title": title,
                    "link": link,
                    "summary": summary,
                    "source": url
                }
                all_news.append(news_dict)

        except Exception as e:
            # 💡 永远不要让爬虫的一个报错导致整个智能体崩溃
            print(f"❌ [错误] 解析 {url} 时发生异常: {str(e)}")
            continue

    print(f"✅ [雷达工具] 扫描完毕，共抓取到 {len(all_news)} 条原始新闻。")
    return all_news


# ==================== 单元测试 ====================
if __name__ == "__main__":
    print("测试雷达工具: \n" + "=" * 40)
    # 注意 tool.invoke 的调用方式
    results = fetch_tech_news.invoke({"max_news_per_source": 2})

    # 打印出结构化数据，你可以直观地看到变化
    for idx, news in enumerate(results):
        print(f"【新闻 {idx + 1}】来自 {news['source']}")
        print(f"标题: {news['title']}")
        print(f"链接: {news['link']}")
        print("-" * 30)