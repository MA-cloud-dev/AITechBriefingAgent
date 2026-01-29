# 🤖 AI Tech Briefing Agent

**智能技术资讯聚合系统** - 自动爬取多数据源技术资讯，AI 智能分类摘要，每日邮件推送技术日报

## 📋 项目简介

AI Tech Briefing Agent 是一个全自动的技术日报生成系统，它会：

1. **🕷️ 多源爬取**：从 GitHub Trending、掘金热榜、Hacker News、AI 论文（HuggingFace/arXiv）等多个技术社区获取最新资讯
2. **🤖 AI 处理**：使用 LLM（SiliconFlow API）对文章进行智能分类、摘要提取和亮点标注
3. **📊 优先级排序**：根据用户兴趣标签对文章进行优先级评分和排序
4. **📧 邮件推送**：生成精美的 Markdown 格式技术日报，通过邮件发送

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Tech Briefing Agent                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────┐      ┌─────────┐      ┌──────────────┐ │
│  │  Python Crawler │ ───▶ │  Redis  │ ───▶ │ Java Processor│ │
│  │                 │      │         │      │               │ │
│  │ • GitHub        │      │ 数据缓存 │      │ • AI 分类摘要 │ │
│  │ • 掘金          │      │ 24h过期  │      │ • 优先级排序  │ │
│  │ • HackerNews    │      │         │      │ • 邮件推送    │ │
│  │ • AI 论文       │      └─────────┘      │               │ │
│  │ • 足球数据      │                        └──────────────┘ │
│  └─────────────────┘                                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 🛠️ 技术栈

| 模块 | 技术 |
|------|------|
| 爬虫 | Python 3.10+, requests, BeautifulSoup, lxml |
| 缓存 | Redis |
| 后端 | Java 17, Spring Boot 3.2, Spring Retry |
| AI | SiliconFlow API (Qwen/Qwen2.5-7B-Instruct) |
| 邮件 | Spring Mail (Gmail SMTP) |

## 📁 项目结构

```
AITechBriefingAgent/
├── python-crawler/              # Python 爬虫模块
│   ├── crawlers/                # 各数据源爬虫
│   │   ├── github_crawler.py    # GitHub Trending
│   │   ├── juejin_crawler.py    # 掘金热榜
│   │   ├── hackernews_crawler.py# Hacker News
│   │   ├── ai_papers_crawler.py # AI 论文 (HF/arXiv)
│   │   ├── producthunt_crawler.py # AI 工具聚合
│   │   ├── football_crawler.py  # 足球数据 (彩蛋)
│   │   └── utils.py             # 通用工具 (重试/UA/限流)
│   ├── config.py                # 配置管理
│   ├── redis_client.py          # Redis 客户端
│   ├── main.py                  # 爬虫入口
│   └── requirements.txt         # Python 依赖
│
├── java-processor/              # Java 处理模块
│   ├── src/main/java/com/briefing/
│   │   ├── BriefingApplication.java  # 主应用
│   │   ├── config/              # 配置类
│   │   ├── controller/          # REST API
│   │   ├── service/             # 业务逻辑
│   │   │   ├── AiSummaryService.java  # AI 处理 (含重试)
│   │   │   ├── EmailService.java      # 邮件发送
│   │   │   └── RedisService.java      # Redis 读取
│   │   ├── scheduler/           # 定时任务
│   │   └── model/               # 数据模型
│   ├── src/main/resources/
│   │   └── application.yml      # Spring 配置
│   └── pom.xml                  # Maven 配置
│
├── .env.example                 # 环境变量模板
├── .gitignore                   # Git 忽略规则
└── README.md                    # 项目说明
```

## 🚀 快速开始

### 1. 环境准备

- Python 3.10+
- Java 17+
- Redis 6+
- Maven 3.8+

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入真实值
```

需要配置的变量：

| 变量 | 说明 |
|------|------|
| `AI_API_KEY` | SiliconFlow API Key |
| `MAIL_USERNAME` | Gmail 邮箱地址 |
| `MAIL_PASSWORD` | Gmail 应用专用密码 |
| `RECIPIENT_EMAIL` | 日报接收邮箱 |
| `FOOTBALL_API_KEY` | football-data.org API Key (可选) |

### 3. 安装依赖

```bash
# Python 依赖
cd python-crawler
pip install -r requirements.txt

# Java 依赖
cd java-processor
mvn install
```

### 4. 运行爬虫

```bash
cd python-crawler

# 测试 Redis 连接
python main.py --test

# 运行完整爬虫
python main.py

# 查看已爬取的文章
python main.py --show
```

### 5. 启动 Java 处理服务

```bash
cd java-processor
mvn spring-boot:run
```

### 6. 触发日报生成

```bash
# 手动触发
curl http://localhost:8080/api/briefing/trigger

# 或等待定时任务 (每天 10:05 自动执行)
```

## 📡 API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/briefing/health` | GET | 健康检查 |
| `/api/briefing/articles` | GET | 查看今日文章 |
| `/api/briefing/trigger` | GET | 手动触发日报 |

## 🔧 特性

### 安全性
- ✅ 敏感信息通过环境变量管理
- ✅ `.env` 文件已在 `.gitignore` 中排除

### 可靠性
- ✅ Python 爬虫内置重试装饰器 (3次重试，指数退避)
- ✅ Java AI 调用使用 Spring Retry (3次重试)
- ✅ 智能降级：AI 失败时基于来源自动分类

### 反爬策略
- ✅ 随机 User-Agent 池
- ✅ 请求频率限制
- ✅ 随机延迟抖动

## 📊 数据源

| 来源 | 分类 | 说明 |
|------|------|------|
| GitHub Trending | 技术项目 | 每日热门开源项目 |
| 掘金热榜 | 中文技术 | 国内技术社区热文 |
| Hacker News | 国际技术 | 硅谷技术圈动态 |
| HuggingFace Papers | AI 前沿 | 每日精选 AI 论文 |
| arXiv | AI 前沿 | AI/ML 最新论文 |
| Futurepedia/Toolify | AI 应用 | 热门 AI 工具 |
| GitHub AI Topics | AI 应用 | AI 相关开源项目 |

## 📝 日报示例

```markdown
# 📰 技术日报 - 2026-01-29

---

## 🚀 AI应用

### 1. [awesome-ai-tools](https://github.com/xxx)
🏷️ **开箱即用** | 📦 GitHub
> 一个收集最新 AI 工具的资源库，持续更新中...

## 🔬 AI前沿

### 2. [Transformer 架构新突破](https://huggingface.co/papers/xxx)
🏷️ **性能翻倍** | 🤗 HuggingFace
> 研究者提出新的注意力机制，在多项基准测试中超越现有方法...

---

## ⚽ 英超快报
...
```

## 📄 License

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！
