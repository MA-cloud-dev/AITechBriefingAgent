package com.briefing.scheduler;

import com.briefing.model.Article;
import com.briefing.service.AiSummaryService;
import com.briefing.service.EmailService;
import com.briefing.service.RedisService;
import com.google.gson.JsonObject;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.util.List;

@Slf4j
@Component
@RequiredArgsConstructor
public class BriefingScheduler {

    private final RedisService redisService;
    private final AiSummaryService aiSummaryService;
    private final EmailService emailService;

    /**
     * 每天 10:05 执行
     * Cron: 秒 分 时 日 月 周
     */
    @Scheduled(cron = "0 5 10 * * ?")
    public void executeDailyBriefing() {
        log.info("========== 开始执行每日技术日报任务 ==========");
        processBriefing();
        log.info("========== 每日技术日报任务完成 ==========");
    }

    /**
     * 手动触发接口调用的核心处理逻辑
     */
    public void processBriefing() {
        try {
            // 1. 从 Redis 读取文章
            List<Article> articles = redisService.getTodayArticles();
            if (articles.isEmpty()) {
                log.warn("没有找到今天的文章数据，跳过处理");
                return;
            }

            // 2. AI处理：分类+摘要+排序+筛选
            List<Article> rankedArticles = aiSummaryService.processAndRankArticles(articles);

            // 3. 读取足球数据
            JsonObject footballData = redisService.getFootballData();
            if (footballData != null) {
                log.info("已读取足球数据，将添加到邮件中");
            }

            // 4. 发送邮件（带足球数据）
            emailService.sendBriefingEmail(rankedArticles, footballData);

            log.info("处理完成: 从 {} 篇中筛选出 {} 篇发送", articles.size(), rankedArticles.size());

        } catch (Exception e) {
            log.error("处理失败: {}", e.getMessage(), e);
        }
    }
}
