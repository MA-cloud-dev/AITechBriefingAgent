"""
GitHub Trending 爬虫
爬取 https://github.com/trending 页面的热门仓库
"""
import uuid
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Any

from config import GITHUB_TRENDING_COUNT
from crawlers.utils import retry_on_failure, safe_request, get_random_user_agent


@retry_on_failure(max_retries=3, delay=1.0)
def crawl_github_trending() -> List[Dict[str, Any]]:
    """
    爬取 GitHub Trending 仓库
    返回文章列表
    """
    url = "https://github.com/trending"
    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    response = safe_request(url, headers=headers, timeout=30)
    soup = BeautifulSoup(response.text, "lxml")
    articles = []
    
    # 查找所有仓库条目
    repo_items = soup.select("article.Box-row")[:GITHUB_TRENDING_COUNT]
    
    for item in repo_items:
        try:
            # 仓库名和链接
            title_elem = item.select_one("h2 a")
            if not title_elem:
                continue
            
            repo_path = title_elem.get("href", "").strip()
            repo_name = " / ".join([
                s.strip() for s in title_elem.get_text().strip().split("\n") if s.strip()
            ])
            repo_url = f"https://github.com{repo_path}"
            
            # 描述
            desc_elem = item.select_one("p")
            description = desc_elem.get_text().strip() if desc_elem else "暂无描述"
            
            # 今日 star 数
            star_elem = item.select_one("span.d-inline-block.float-sm-right")
            today_stars = star_elem.get_text().strip() if star_elem else ""
            
            article = {
                "id": str(uuid.uuid4()),
                "title": repo_name,
                "url": repo_url,
                "source": "github",
                "description": description,
                "extra": {"today_stars": today_stars},
                "crawl_time": datetime.now().isoformat()
            }
            articles.append(article)
            
        except Exception as e:
            print(f"[GitHub] 解析条目失败: {e}")
            continue
    
    print(f"[GitHub] 成功爬取 {len(articles)} 个仓库")
    return articles


if __name__ == "__main__":
    # 测试爬虫
    results = crawl_github_trending()
    for r in results:
        print(f"- {r['title']}: {r['description'][:50]}...")
