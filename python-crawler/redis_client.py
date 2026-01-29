"""
Redis 客户端封装
"""
import json
import redis
from datetime import datetime, date
from typing import List, Dict, Any

from config import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, REDIS_KEY_PREFIX


class RedisClient:
    def __init__(self):
        self.client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD,
            decode_responses=True
        )
    
    def get_today_key(self) -> str:
        """获取今天的 Redis Key"""
        today = date.today().isoformat()
        return f"{REDIS_KEY_PREFIX}:{today}"
    
    def save_articles(self, articles: List[Dict[str, Any]]) -> int:
        """
        保存文章列表到 Redis
        返回保存的文章数量
        """
        if not articles:
            return 0
        
        key = self.get_today_key()
        
        # 清空今天的旧数据
        self.client.delete(key)
        
        # 逐条存入 List
        for article in articles:
            self.client.rpush(key, json.dumps(article, ensure_ascii=False))
        
        # 设置24小时过期
        self.client.expire(key, 86400)
        
        return len(articles)
    
    def get_articles(self) -> List[Dict[str, Any]]:
        """获取今天的文章列表"""
        key = self.get_today_key()
        raw_list = self.client.lrange(key, 0, -1)
        return [json.loads(item) for item in raw_list]
    
    def save_football(self, data: Dict[str, Any]) -> bool:
        """保存足球数据到Redis"""
        if not data:
            return False
        
        key = f"{REDIS_KEY_PREFIX}:football:{date.today().isoformat()}"
        self.client.set(key, json.dumps(data, ensure_ascii=False))
        self.client.expire(key, 86400)
        return True
    
    def get_football(self) -> Dict[str, Any]:
        """获取足球数据"""
        key = f"{REDIS_KEY_PREFIX}:football:{date.today().isoformat()}"
        data = self.client.get(key)
        return json.loads(data) if data else {}
    
    def ping(self) -> bool:
        """测试 Redis 连接"""
        try:
            return self.client.ping()
        except Exception:
            return False


# 单例
redis_client = RedisClient()
