"""
AI工具聚合爬虫
从多个AI工具聚合站点获取热门AI应用
"""
import uuid
from datetime import datetime
from typing import List, Dict, Any
from bs4 import BeautifulSoup

from crawlers.utils import retry_on_failure, safe_request, get_random_user_agent


def crawl_ai_tools(count: int = 5, days_limit: int = 10) -> List[Dict[str, Any]]:
    """
    爬取多个AI工具聚合站点
    优先级：futurepedia > toolify > github-ai
    """
    articles = []
    
    # 1. 尝试 Futurepedia (AI工具目录)
    try:
        futurepedia_articles = crawl_futurepedia(count, days_limit)
        articles.extend(futurepedia_articles)
    except Exception as e:
        print(f"[Futurepedia] 爬取失败: {e}")
    
    # 2. 如果不够，尝试 Toolify
    if len(articles) < count:
        try:
            toolify_articles = crawl_toolify(count - len(articles), days_limit)
            articles.extend(toolify_articles)
        except Exception as e:
            print(f"[Toolify] 爬取失败: {e}")
    
    # 3. 如果还不够，尝试 GitHub AI topics
    if len(articles) < count:
        try:
            github_ai = crawl_github_ai_topics(count - len(articles))
            articles.extend(github_ai)
        except Exception as e:
            print(f"[GitHub AI] 爬取失败: {e}")
    
    print(f"[AI工具] 共获取 {len(articles)} 个AI应用")
    return articles[:count]


@retry_on_failure(max_retries=2, delay=1.0)
def crawl_futurepedia(count: int = 5, days_limit: int = 10) -> List[Dict[str, Any]]:
    """
    爬取 Futurepedia.io - AI工具目录
    """
    url = "https://www.futurepedia.io/ai-tools"
    headers = {
        "User-Agent": get_random_user_agent()
    }
    
    response = safe_request(url, headers=headers, timeout=30)
    soup = BeautifulSoup(response.text, "html.parser")
    articles = []
    
    # 查找工具卡片
    tool_cards = soup.select("div[class*='tool-card'], a[href*='/tool/']")
    
    for card in tool_cards[:count * 2]:
        if len(articles) >= count:
            break
            
        try:
            # 提取标题
            title_elem = card.select_one("h2, h3, [class*='title']")
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            if not title or len(title) < 3:
                continue
            
            # 提取链接
            if card.name == "a":
                link = card.get("href", "")
            else:
                link_elem = card.select_one("a")
                link = link_elem.get("href", "") if link_elem else ""
            
            if not link.startswith("http"):
                link = f"https://www.futurepedia.io{link}"
            
            # 提取描述
            desc_elem = card.select_one("p, [class*='description']")
            description = desc_elem.get_text(strip=True)[:150] if desc_elem else ""
            
            article = {
                "id": str(uuid.uuid4()),
                "title": title,
                "url": link,
                "source": "futurepedia",
                "description": description if description else "AI工具",
                "extra": {},
                "crawl_time": datetime.now().isoformat(),
                "ai_category": "AI应用"
            }
            articles.append(article)
            
        except Exception as e:
            continue
    
    print(f"[Futurepedia] 成功爬取 {len(articles)} 个AI工具")
    return articles


@retry_on_failure(max_retries=2, delay=1.0)
def crawl_toolify(count: int = 5, days_limit: int = 10) -> List[Dict[str, Any]]:
    """
    爬取 Toolify.ai - AI工具排行
    """
    url = "https://www.toolify.ai/Best-AI-Tools-list"
    headers = {
        "User-Agent": get_random_user_agent()
    }
    
    response = safe_request(url, headers=headers, timeout=30)
    soup = BeautifulSoup(response.text, "html.parser")
    articles = []
    
    # 查找工具列表
    tool_items = soup.select("a[href*='/ai-tool/']")
    
    for item in tool_items[:count * 2]:
        if len(articles) >= count:
            break
            
        try:
            title = item.get_text(strip=True)
            if not title or len(title) < 3:
                continue
                
            link = item.get("href", "")
            if not link.startswith("http"):
                link = f"https://www.toolify.ai{link}"
            
            article = {
                "id": str(uuid.uuid4()),
                "title": title,
                "url": link,
                "source": "toolify",
                "description": "热门AI工具",
                "extra": {},
                "crawl_time": datetime.now().isoformat(),
                "ai_category": "AI应用"
            }
            articles.append(article)
            
        except Exception as e:
            continue
    
    print(f"[Toolify] 成功爬取 {len(articles)} 个AI工具")
    return articles


@retry_on_failure(max_retries=2, delay=1.0)
def crawl_github_ai_topics(count: int = 3) -> List[Dict[str, Any]]:
    """
    爬取 GitHub AI 主题下的热门仓库
    """
    url = "https://github.com/topics/ai?o=desc&s=updated"
    headers = {
        "User-Agent": get_random_user_agent()
    }
    
    response = safe_request(url, headers=headers, timeout=30)
    soup = BeautifulSoup(response.text, "html.parser")
    articles = []
    
    repo_links = soup.select("article h3 a")
    
    for link in repo_links[:count]:
        try:
            href = link.get("href", "")
            title = link.get_text(strip=True).replace("\n", "").replace("  ", " ")
            
            # 获取描述
            article_elem = link.find_parent("article")
            desc_elem = article_elem.select_one("p") if article_elem else None
            description = desc_elem.get_text(strip=True)[:150] if desc_elem else ""
            
            article = {
                "id": str(uuid.uuid4()),
                "title": title,
                "url": f"https://github.com{href}",
                "source": "github-ai",
                "description": description if description else "GitHub AI项目",
                "extra": {},
                "crawl_time": datetime.now().isoformat(),
                "ai_category": "AI应用"
            }
            articles.append(article)
            
        except Exception as e:
            continue
    
    print(f"[GitHub AI] 成功爬取 {len(articles)} 个AI项目")
    return articles


if __name__ == "__main__":
    results = crawl_ai_tools(5)
    for r in results:
        print(f"- {r['title']}")
        print(f"  {r['url']}")
