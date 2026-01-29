"""
Hacker News 爬虫
获取 HN 热门文章
"""
import uuid
import requests
from datetime import datetime
from typing import List, Dict, Any

from crawlers.utils import retry_on_failure, RateLimiter


@retry_on_failure(max_retries=3, delay=1.0)
def crawl_hackernews(count: int = 10) -> List[Dict[str, Any]]:
    """
    爬取 Hacker News 热门文章
    使用官方 API
    """
    # HN 官方 API - 获取热门故事 ID
    top_stories_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
    
    response = requests.get(top_stories_url, timeout=30)
    response.raise_for_status()
    story_ids = response.json()[:count * 2]  # 多取一些，过滤掉非文章类型
    
    articles = []
    limiter = RateLimiter(min_interval=0.2)  # 避免请求过快
    
    for story_id in story_ids:
        if len(articles) >= count:
            break
        
        try:
            limiter.wait()
            
            # 获取单个故事详情
            item_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
            item_resp = requests.get(item_url, timeout=10)
            item = item_resp.json()
            
            # 只要有标题的 story 类型
            if not item or item.get("type") != "story" or not item.get("title"):
                continue
            
            # HN 有些是讨论帖没有 URL，用 HN 链接代替
            url = item.get("url", f"https://news.ycombinator.com/item?id={story_id}")
            
            article = {
                "id": str(uuid.uuid4()),
                "title": item.get("title", ""),
                "url": url,
                "source": "hackernews",
                "description": f"Score: {item.get('score', 0)} | Comments: {item.get('descendants', 0)}",
                "extra": {
                    "score": item.get("score", 0),
                    "comments": item.get("descendants", 0),
                    "author": item.get("by", "")
                },
                "crawl_time": datetime.now().isoformat()
            }
            articles.append(article)
            
        except Exception as e:
            print(f"[HN] 获取故事 {story_id} 失败: {e}")
            continue
    
    print(f"[HN] 成功爬取 {len(articles)} 篇文章")
    return articles


if __name__ == "__main__":
    results = crawl_hackernews(5)
    for r in results:
        print(f"- {r['title']}")
        print(f"  {r['url']}")
