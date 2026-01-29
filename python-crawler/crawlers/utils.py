"""
爬虫通用工具模块
提供重试装饰器、随机 User-Agent、请求工具等
"""
import random
import time
import functools
from typing import Callable, Any, List
import requests


# === 随机 User-Agent 池 ===
USER_AGENTS = [
    # Chrome on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    # Chrome on Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    # Firefox on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    # Firefox on Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    # Safari on Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    # Edge on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
]


def get_random_user_agent() -> str:
    """获取随机 User-Agent"""
    return random.choice(USER_AGENTS)


def get_default_headers() -> dict:
    """获取带随机 UA 的默认请求头"""
    return {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }


def retry_on_failure(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (requests.RequestException, Exception)
) -> Callable:
    """
    重试装饰器
    
    Args:
        max_retries: 最大重试次数
        delay: 初始延迟（秒）
        backoff: 退避倍数
        exceptions: 需要重试的异常类型
    
    Usage:
        @retry_on_failure(max_retries=3, delay=1.0)
        def my_crawler():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        # 添加随机抖动避免雷同请求
                        jitter = random.uniform(0.5, 1.5)
                        sleep_time = current_delay * jitter
                        print(f"  ⚠ 第 {attempt + 1} 次尝试失败: {e}")
                        print(f"  ⏳ {sleep_time:.1f} 秒后重试...")
                        time.sleep(sleep_time)
                        current_delay *= backoff
                    else:
                        print(f"  ✗ 已达最大重试次数 ({max_retries})")
            
            raise last_exception
        return wrapper
    return decorator


def safe_request(
    url: str,
    method: str = "GET",
    timeout: int = 30,
    headers: dict = None,
    **kwargs
) -> requests.Response:
    """
    安全的 HTTP 请求封装
    
    Args:
        url: 请求 URL
        method: HTTP 方法
        timeout: 超时时间（秒）
        headers: 自定义请求头（会与默认头合并）
        **kwargs: 其他 requests 参数
    
    Returns:
        Response 对象
    
    Raises:
        requests.RequestException: 请求失败时抛出
    """
    # 合并请求头
    final_headers = get_default_headers()
    if headers:
        final_headers.update(headers)
    
    response = requests.request(
        method=method,
        url=url,
        headers=final_headers,
        timeout=timeout,
        **kwargs
    )
    response.raise_for_status()
    return response


class RateLimiter:
    """
    简单的请求频率限制器
    
    Usage:
        limiter = RateLimiter(min_interval=1.0)
        for url in urls:
            limiter.wait()
            response = requests.get(url)
    """
    
    def __init__(self, min_interval: float = 1.0):
        """
        Args:
            min_interval: 最小请求间隔（秒）
        """
        self.min_interval = min_interval
        self.last_request_time = 0.0
    
    def wait(self):
        """等待到下一个可请求时间"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_interval:
            # 添加随机抖动
            sleep_time = self.min_interval - elapsed + random.uniform(0.1, 0.5)
            time.sleep(sleep_time)
        self.last_request_time = time.time()


# === 测试代码 ===
if __name__ == "__main__":
    print("=== 测试随机 User-Agent ===")
    for i in range(3):
        print(f"{i+1}. {get_random_user_agent()[:60]}...")
    
    print("\n=== 测试重试装饰器 ===")
    
    @retry_on_failure(max_retries=2, delay=0.5)
    def test_function():
        print("  尝试执行...")
        if random.random() < 0.7:
            raise Exception("模拟失败")
        return "成功!"
    
    try:
        result = test_function()
        print(f"  结果: {result}")
    except Exception as e:
        print(f"  最终失败: {e}")
