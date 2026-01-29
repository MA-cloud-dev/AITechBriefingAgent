"""
掘金热榜爬虫
使用掘金 API 获取热门文章
"""
import uuid
import requests
from datetime import datetime
from typing import List, Dict, Any

from config import JUEJIN_HOT_COUNT
from crawlers.utils import retry_on_failure, get_random_user_agent


@retry_on_failure(max_retries=3, delay=1.0)
def crawl_juejin_hot() -> List[Dict[str, Any]]:
    """
    爬取掘金热榜文章
    返回文章列表
    """
    # 掘金综合热榜 API
    url = "https://api.juejin.cn/recommend_api/v1/article/recommend_all_feed"
    payload = {
        "id_type": 2,
        "sort_type": 200,  # 热门排序
        "cursor": "0",
        "limit": JUEJIN_HOT_COUNT
    }
    headers = {
        "User-Agent": get_random_user_agent(),
        "Content-Type": "application/json",
        "Origin": "https://juejin.cn",
        "Referer": "https://juejin.cn/"
    }
    
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    response.raise_for_status()
    data = response.json()
    
    if data.get("err_no") != 0:
        raise ValueError(f"API返回错误: {data.get('err_msg')}")
    
    articles = []
    items = data.get("data", [])[:JUEJIN_HOT_COUNT]
    
    for item in items:
        try:
            # API返回格式: item_type + item_info
            item_type = item.get("item_type")
            if item_type != 2:  # 2 = 文章类型
                continue
            
            item_info = item.get("item_info", {})
            article_info = item_info.get("article_info", {})
            author_info = item_info.get("author_user_info", {})
            article_id = article_info.get("article_id", "")
            
            if not article_id:
                continue
            
            article = {
                "id": str(uuid.uuid4()),
                "title": article_info.get("title", "无标题"),
                "url": f"https://juejin.cn/post/{article_id}",
                "source": "juejin",
                "description": article_info.get("brief_content", "暂无摘要"),
                "extra": {
                    "author": author_info.get("user_name", "未知"),
                    "view_count": article_info.get("view_count", 0),
                    "digg_count": article_info.get("digg_count", 0)
                },
                "crawl_time": datetime.now().isoformat()
            }
            articles.append(article)
            
        except Exception as e:
            print(f"[掘金] 解析条目失败: {e}")
            continue
    
    print(f"[掘金] 成功爬取 {len(articles)} 篇文章")
    return articles


if __name__ == "__main__":
    # 测试爬虫
    results = crawl_juejin_hot()
    for r in results:
        print(f"- {r['title']}: {r['description'][:50]}...")
