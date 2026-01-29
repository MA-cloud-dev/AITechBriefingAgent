package com.briefing.service;

import com.briefing.config.BriefingConfig;
import com.briefing.model.Article;
import com.google.gson.Gson;
import com.google.gson.JsonObject;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.util.Collections;
import java.util.List;

@Slf4j
@Service
@RequiredArgsConstructor
public class RedisService {

    private final StringRedisTemplate redisTemplate;
    private final BriefingConfig config;
    private final Gson gson = new Gson();

    /**
     * 获取今天的 Redis Key
     */
    private String getTodayKey() {
        String today = LocalDate.now().toString();
        return config.getRedisKeyPrefix() + ":" + today;
    }

    /**
     * 获取今天的文章列表
     */
    public List<Article> getTodayArticles() {
        String key = getTodayKey();
        log.info("从 Redis 读取文章, Key: {}", key);

        List<String> rawList = redisTemplate.opsForList().range(key, 0, -1);
        if (rawList == null || rawList.isEmpty()) {
            log.warn("Redis 中没有找到今天的文章数据");
            return Collections.emptyList();
        }

        List<Article> articles = rawList.stream()
                .map(json -> gson.fromJson(json, Article.class))
                .toList();

        log.info("成功读取 {} 篇文章", articles.size());
        return articles;
    }

    /**
     * 获取足球数据
     */
    public JsonObject getFootballData() {
        String key = config.getRedisKeyPrefix() + ":football:" + LocalDate.now().toString();
        log.info("从 Redis 读取足球数据, Key: {}", key);

        String data = redisTemplate.opsForValue().get(key);
        if (data == null || data.isEmpty()) {
            log.info("Redis 中没有找到足球数据");
            return null;
        }

        log.info("成功读取足球数据");
        return gson.fromJson(data, JsonObject.class);
    }

    /**
     * 检查 Redis 连接
     */
    public boolean ping() {
        try {
            var factory = redisTemplate.getConnectionFactory();
            if (factory == null) {
                return false;
            }
            String result = factory.getConnection().ping();
            return "PONG".equals(result);
        } catch (Exception e) {
            log.error("Redis 连接失败: {}", e.getMessage());
            return false;
        }
    }
}
