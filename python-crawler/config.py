"""
Python 爬虫配置
使用环境变量管理敏感信息
"""
import os
from pathlib import Path

# 尝试加载 .env 文件
try:
    from dotenv import load_dotenv
    # 查找项目根目录的 .env 文件
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"[Config] 已加载环境变量: {env_path}")
except ImportError:
    pass  # python-dotenv 未安装时静默忽略

# Redis 配置 (从环境变量读取)
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD") or None

# 足球 API 配置
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY", "")

# 爬虫配置 (多抓取，Java端筛选)
GITHUB_TRENDING_COUNT = 8
JUEJIN_HOT_COUNT = 8

# Redis Key 前缀
REDIS_KEY_PREFIX = "tech_briefing:articles"
