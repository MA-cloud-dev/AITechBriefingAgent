"""
智能技术资讯聚合系统 - Python 爬虫入口
"""
import sys
import argparse
from datetime import datetime

from crawlers.github_crawler import crawl_github_trending
from crawlers.juejin_crawler import crawl_juejin_hot
from crawlers.hackernews_crawler import crawl_hackernews
from crawlers.producthunt_crawler import crawl_ai_tools
from crawlers.ai_papers_crawler import crawl_huggingface_papers, crawl_arxiv_ai
from crawlers.football_crawler import get_football_summary, format_football_markdown
from redis_client import redis_client
from config import FOOTBALL_API_KEY

# 配置
DAYS_LIMIT = 10


def run_crawlers():
    """
    运行所有爬虫并存储结果
    优先级：AI内容 > 其他技术内容
    """
    print(f"\n{'='*50}")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始爬取技术资讯...")
    print(f"{'='*50}\n")
    
    all_articles = []
    
    # === 优先级1: AI内容 ===
    print("=" * 30)
    print("📌 优先爬取 AI 内容")
    print("=" * 30)
    
    # 1. AI应用 - 多源聚合 (Futurepedia/Toolify/GitHub AI)
    print("[1/6] 正在爬取 AI 应用工具...")
    try:
        ai_tools = crawl_ai_tools(count=5, days_limit=DAYS_LIMIT)
        all_articles.extend(ai_tools)
    except Exception as e:
        print(f"  ⚠ AI工具爬取失败: {e}")
    
    # 2. AI前沿 - Hugging Face Papers
    print("[2/6] 正在爬取 Hugging Face AI 论文...")
    try:
        hf_articles = crawl_huggingface_papers(count=5, days_limit=DAYS_LIMIT)
        all_articles.extend(hf_articles)
    except Exception as e:
        print(f"  ⚠ Hugging Face 爬取失败: {e}")
    
    # 3. AI前沿 - arXiv (备用)
    print("[3/6] 正在爬取 arXiv AI 论文...")
    try:
        arxiv_articles = crawl_arxiv_ai(count=3, days_limit=DAYS_LIMIT)
        all_articles.extend(arxiv_articles)
    except Exception as e:
        print(f"  ⚠ arXiv 爬取失败: {e}")
    
    # === 优先级2: 补充来源（减少数量） ===
    print("\n" + "=" * 30)
    print("📎 爬取补充来源")
    print("=" * 30)
    
    # 4. GitHub Trending (只取4篇，主要看AI相关)
    print("[4/6] 正在爬取 GitHub Trending...")
    try:
        github_articles = crawl_github_trending()[:4]
        all_articles.extend(github_articles)
    except Exception as e:
        print(f"  ⚠ GitHub 爬取失败: {e}")
    
    # 5. 掘金热榜 (只取3篇)
    print("[5/6] 正在爬取掘金热榜...")
    try:
        juejin_articles = crawl_juejin_hot()[:3]
        all_articles.extend(juejin_articles)
    except Exception as e:
        print(f"  ⚠ 掘金爬取失败: {e}")
    
    # 6. Hacker News (只取3篇)
    print("[6/6] 正在爬取 Hacker News...")
    try:
        hn_articles = crawl_hackernews(3)
        all_articles.extend(hn_articles)
    except Exception as e:
        print(f"  ⚠ Hacker News 爬取失败: {e}")
    
    # 存入 Redis
    print(f"\n[存储] 共 {len(all_articles)} 篇文章，正在存入 Redis...")
    saved_count = redis_client.save_articles(all_articles)
    print(f"[存储] 成功存入 {saved_count} 篇文章")
    
    # === 足球数据 ===
    print("\n" + "=" * 30)
    print("⚽ 获取足球数据")
    print("=" * 30)
    
    try:
        football_data = get_football_summary(FOOTBALL_API_KEY)
        if football_data.get("standings") or football_data.get("matches"):
            redis_client.save_football(football_data)
            print("[Football] 足球数据已存入 Redis")
        else:
            print("[Football] 未获取到足球数据")
    except Exception as e:
        print(f"[Football] 获取失败: {e}")
    
    # 打印汇总
    print(f"\n{'='*50}")
    print("爬取完成！汇总：")
    print(f"  🚀 AI应用 (多源聚合): {len(ai_tools) if 'ai_tools' in dir() else 0} 篇")
    print(f"  🔬 AI前沿 (HuggingFace): {len(hf_articles) if 'hf_articles' in dir() else 0} 篇")
    print(f"  📄 AI前沿 (arXiv): {len(arxiv_articles) if 'arxiv_articles' in dir() else 0} 篇")
    print(f"  📦 GitHub Trending: {len(github_articles) if 'github_articles' in dir() else 0} 篇")
    print(f"  📝 掘金热榜: {len(juejin_articles) if 'juejin_articles' in dir() else 0} 篇")
    print(f"  🔶 Hacker News: {len(hn_articles) if 'hn_articles' in dir() else 0} 篇")
    print(f"  ⚽ 足球数据: {'已获取' if 'football_data' in dir() and football_data else '未获取'}")
    print(f"  📊 总计: {len(all_articles)} 篇")
    print(f"  🔑 Redis Key: {redis_client.get_today_key()}")
    print(f"{'='*50}\n")
    
    return all_articles


def test_redis():
    """测试 Redis 连接"""
    print("正在测试 Redis 连接...")
    if redis_client.ping():
        print("✓ Redis 连接成功!")
        articles = redis_client.get_articles()
        print(f"✓ 当前存储 {len(articles)} 篇文章")
    else:
        print("✗ Redis 连接失败!")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="技术资讯爬虫")
    parser.add_argument("--test", action="store_true", help="仅测试 Redis 连接")
    parser.add_argument("--show", action="store_true", help="显示当前存储的文章")
    args = parser.parse_args()
    
    if args.test:
        test_redis()
    elif args.show:
        articles = redis_client.get_articles()
        if articles:
            print(f"当前存储 {len(articles)} 篇文章：\n")
            for i, a in enumerate(articles, 1):
                print(f"{i}. [{a['source']}] {a['title']}")
                print(f"   URL: {a['url']}")
                print(f"   描述: {a['description'][:80]}...")
                print()
        else:
            print("暂无存储的文章")
    else:
        run_crawlers()


if __name__ == "__main__":
    main()
