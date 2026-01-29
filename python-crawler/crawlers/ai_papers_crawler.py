"""
Hugging Face Daily Papers 爬虫
获取AI前沿技术论文（AI前沿类）
"""
import uuid
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any
from bs4 import BeautifulSoup

from crawlers.utils import retry_on_failure, safe_request, get_random_user_agent


@retry_on_failure(max_retries=3, delay=1.0)
def crawl_huggingface_papers(count: int = 5, days_limit: int = 10) -> List[Dict[str, Any]]:
    """
    爬取 Hugging Face Daily Papers
    来源：https://huggingface.co/papers
    """
    url = "https://huggingface.co/papers"
    
    headers = {
        "User-Agent": get_random_user_agent()
    }
    
    response = safe_request(url, headers=headers, timeout=30)
    soup = BeautifulSoup(response.text, "html.parser")
    articles = []
    
    # 查找论文卡片
    paper_cards = soup.select("article.paper-card, div[data-target='paper']")
    if not paper_cards:
        # 备用选择器
        paper_cards = soup.select("a[href*='/papers/']")
    
    cutoff_date = datetime.now() - timedelta(days=days_limit)
    
    for card in paper_cards[:count * 2]:  # 多取一些用于过滤
        if len(articles) >= count:
            break
            
        try:
            # 提取标题
            title_elem = card.select_one("h3, h4, .paper-title") or card
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            if not title or len(title) < 5:
                continue
            
            # 提取链接
            if card.name == "a":
                link = card.get("href", "")
            else:
                link_elem = card.select_one("a[href*='/papers/']")
                link = link_elem.get("href", "") if link_elem else ""
            
            if not link.startswith("http"):
                link = f"https://huggingface.co{link}"
            
            # 提取描述/摘要
            desc_elem = card.select_one("p, .paper-summary, .truncate")
            description = desc_elem.get_text(strip=True)[:200] if desc_elem else ""
            
            # 提取日期（如果有）
            date_elem = card.select_one("time, .date, span[data-date]")
            paper_date = None
            if date_elem:
                date_str = date_elem.get("datetime") or date_elem.get_text(strip=True)
                try:
                    paper_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                except:
                    pass
            
            # 时效性过滤（HF papers 通常都是当天的，这里主要过滤异常数据）
            if paper_date and paper_date.replace(tzinfo=None) < cutoff_date:
                continue
            
            article = {
                "id": str(uuid.uuid4()),
                "title": title,
                "url": link,
                "source": "huggingface",
                "description": description if description else "AI前沿论文",
                "extra": {
                    "paper_date": paper_date.isoformat() if paper_date else None
                },
                "crawl_time": datetime.now().isoformat(),
                "ai_category": "AI前沿"  # 预设分类
            }
            articles.append(article)
            
        except Exception as e:
            print(f"[HF Papers] 解析单条失败: {e}")
            continue
    
    print(f"[HF Papers] 成功爬取 {len(articles)} 篇AI前沿论文")
    return articles


@retry_on_failure(max_retries=3, delay=1.0)
def crawl_arxiv_ai(count: int = 3, days_limit: int = 10) -> List[Dict[str, Any]]:
    """
    备用：爬取 arXiv AI 论文
    """
    # arXiv API for cs.AI, cs.LG, cs.CL categories
    url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": "cat:cs.AI OR cat:cs.LG OR cat:cs.CL",
        "start": 0,
        "max_results": count * 2,
        "sortBy": "submittedDate",
        "sortOrder": "descending"
    }
    
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, "xml")
    entries = soup.find_all("entry")
    articles = []
    cutoff_date = datetime.now() - timedelta(days=days_limit)
    
    for entry in entries:
        if len(articles) >= count:
            break
            
        try:
            # 解析发布日期
            published = entry.find("published")
            if published:
                pub_date = datetime.fromisoformat(published.text.replace("Z", "+00:00"))
                if pub_date.replace(tzinfo=None) < cutoff_date:
                    continue
            
            title = entry.find("title").text.strip().replace("\n", " ") if entry.find("title") else ""
            summary = entry.find("summary").text.strip()[:200] if entry.find("summary") else ""
            link = entry.find("id").text if entry.find("id") else ""
            
            article = {
                "id": str(uuid.uuid4()),
                "title": title,
                "url": link,
                "source": "arxiv",
                "description": summary,
                "extra": {
                    "published": published.text if published else None
                },
                "crawl_time": datetime.now().isoformat(),
                "ai_category": "AI前沿"
            }
            articles.append(article)
            
        except Exception as e:
            print(f"[arXiv] 解析单条失败: {e}")
            continue
    
    print(f"[arXiv] 成功爬取 {len(articles)} 篇AI论文")
    return articles


if __name__ == "__main__":
    print("=== Hugging Face Papers ===")
    hf_results = crawl_huggingface_papers(3)
    for r in hf_results:
        print(f"- {r['title'][:60]}...")
    
    print("\n=== arXiv AI ===")
    arxiv_results = crawl_arxiv_ai(3)
    for r in arxiv_results:
        print(f"- {r['title'][:60]}...")
