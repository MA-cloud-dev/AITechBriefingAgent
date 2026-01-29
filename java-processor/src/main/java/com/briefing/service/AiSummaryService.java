package com.briefing.service;

import com.briefing.config.BriefingConfig;
import com.briefing.model.Article;
import com.google.gson.Gson;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParseException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import okhttp3.*;
import org.springframework.retry.annotation.Backoff;
import org.springframework.retry.annotation.Recover;
import org.springframework.retry.annotation.Retryable;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.util.Comparator;
import java.util.List;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@Slf4j
@Service
@RequiredArgsConstructor
public class AiSummaryService {

    private final BriefingConfig config;
    private final Gson gson = new Gson();

    // 统计指标
    private final AtomicInteger successCount = new AtomicInteger(0);
    private final AtomicInteger failureCount = new AtomicInteger(0);
    private final AtomicInteger retryCount = new AtomicInteger(0);

    // 增加超时时间，大模型响应可能较慢
    private final OkHttpClient httpClient = new OkHttpClient.Builder()
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(120, TimeUnit.SECONDS) // 增加到120秒
            .writeTimeout(30, TimeUnit.SECONDS)
            .build();

    /**
     * 处理文章：AI分类+摘要+亮点，然后按优先级排序并截取
     */
    public List<Article> processAndRankArticles(List<Article> articles) {
        log.info("开始处理 {} 篇文章 (AI分类+摘要)...", articles.size());

        // 重置统计
        successCount.set(0);
        failureCount.set(0);
        retryCount.set(0);

        // 创建可变列表副本
        List<Article> mutableArticles = new java.util.ArrayList<>(articles);

        for (int i = 0; i < mutableArticles.size(); i++) {
            Article article = mutableArticles.get(i);
            log.info("[{}/{}] 正在处理: {}", i + 1, mutableArticles.size(), article.getTitle());

            processArticle(article);

            // 避免请求过快，使用递增延迟
            try {
                Thread.sleep(500 + (i % 3) * 200); // 500-900ms 随机延迟
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }

        // 按优先级排序
        mutableArticles.sort(Comparator.comparingInt(Article::getPriorityScore).reversed());

        // 截取前 maxArticles 篇
        int maxArticles = config.getMaxArticles();
        List<Article> result = mutableArticles.size() > maxArticles
                ? new java.util.ArrayList<>(mutableArticles.subList(0, maxArticles))
                : mutableArticles;

        log.info("处理完成: 成功={}, 失败={}, 重试次数={}, 筛选出 {} 篇高优先级文章",
                successCount.get(), failureCount.get(), retryCount.get(), result.size());
        return result;
    }

    /**
     * 处理单篇文章
     */
    private void processArticle(Article article) {
        String prompt = buildPrompt(article);

        try {
            String response = callAiApiWithRetry(prompt, article.getTitle());
            parseAiResponse(article, response);
            calculatePriorityScore(article);
            successCount.incrementAndGet();
            log.info("  → 分类: {} | 优先级: {}", article.getCategory(), article.getPriorityScore());
        } catch (Exception e) {
            failureCount.incrementAndGet();
            log.error("处理失败 [{}]: {}", article.getTitle(), e.getMessage());
            // 降级处理：使用原始描述
            applyFallback(article);
        }
    }

    /**
     * 带重试的 AI API 调用
     * 最多重试3次，指数退避（1秒、2秒、4秒）
     */
    @Retryable(retryFor = { IOException.class,
            RuntimeException.class }, maxAttempts = 3, backoff = @Backoff(delay = 1000, multiplier = 2))
    public String callAiApiWithRetry(String prompt, String articleTitle) throws IOException {
        retryCount.incrementAndGet();
        log.debug("调用 AI API [{}]", articleTitle);
        return callSiliconFlowApi(prompt);
    }

    /**
     * 重试耗尽后的恢复方法
     */
    @Recover
    public String recoverFromAiFailure(Exception e, String prompt, String articleTitle) {
        log.warn("AI API 重试耗尽 [{}]: {}", articleTitle, e.getMessage());
        throw new RuntimeException("AI API 调用失败，已达最大重试次数", e);
    }

    /**
     * 降级处理：当AI处理完全失败时使用
     */
    private void applyFallback(Article article) {
        article.setAiSummary(article.getDescription());
        // 基于来源智能设置分类
        String source = article.getSource();
        if ("huggingface".equals(source) || "arxiv".equals(source)) {
            article.setCategory("AI前沿");
            article.setHighlight("技术论文");
        } else if ("github-ai".equals(source) || "futurepedia".equals(source) || "toolify".equals(source)) {
            article.setCategory("AI应用");
            article.setHighlight("AI工具");
        } else {
            article.setCategory("其他");
            article.setHighlight("技术资讯");
        }
        article.setPriorityScore(0);
    }

    private String buildPrompt(Article article) {
        String tagsStr = String.join("、", config.getInterestTags());
        return String.format("""
                请分析以下技术文章/项目，用中文输出以下信息：

                标题：%s
                来源：%s
                描述：%s

                分类说明：
                - AI应用：可以直接运行的AI工具、开源项目、产品
                - AI前沿：理论突破、论文、大厂(OpenAI/Google/Meta等)的技术进展
                - 其他分类：Python、Java、Go、架构、前端等

                请严格按以下格式输出（每行一个字段）：
                分类：[从这些选项中选一个: %s, 其他]
                亮点：[3-6个字的核心亮点标签，如"开箱即用"、"性能翻倍"、"GPT替代品"]
                摘要：[2-3句话总结核心内容，不超过80字]
                """,
                article.getTitle(),
                article.getSource(),
                article.getDescription(),
                tagsStr);
    }

    /**
     * 解析AI返回的结构化响应（增强版，更健壮的解析）
     */
    private void parseAiResponse(Article article, String response) {
        if (response == null || response.isBlank()) {
            throw new IllegalArgumentException("AI 响应为空");
        }

        // 解析分类 - 支持多种格式
        Pattern categoryPattern = Pattern.compile("分类[：:]\\s*(.+?)(?:\\n|$)");
        Matcher categoryMatcher = categoryPattern.matcher(response);
        if (categoryMatcher.find()) {
            String category = categoryMatcher.group(1).trim();
            // 清理可能的括号和额外字符
            category = category.replaceAll("[\\[\\]【】]", "").trim();
            article.setCategory(category);
        } else {
            article.setCategory("其他");
        }

        // 解析亮点
        Pattern highlightPattern = Pattern.compile("亮点[：:]\\s*(.+?)(?:\\n|$)");
        Matcher highlightMatcher = highlightPattern.matcher(response);
        if (highlightMatcher.find()) {
            String highlight = highlightMatcher.group(1).trim();
            highlight = highlight.replaceAll("[\\[\\]【】\"']", "").trim();
            // 限制长度
            if (highlight.length() > 20) {
                highlight = highlight.substring(0, 20);
            }
            article.setHighlight(highlight);
        } else {
            article.setHighlight("");
        }

        // 解析摘要
        Pattern summaryPattern = Pattern.compile("摘要[：:]\\s*(.+)", Pattern.DOTALL);
        Matcher summaryMatcher = summaryPattern.matcher(response);
        if (summaryMatcher.find()) {
            String summary = summaryMatcher.group(1).trim();
            // 限制长度
            if (summary.length() > 200) {
                summary = summary.substring(0, 200) + "...";
            }
            article.setAiSummary(summary);
        } else {
            article.setAiSummary(response.trim());
        }
    }

    /**
     * 根据兴趣标签计算优先级分数
     */
    private void calculatePriorityScore(Article article) {
        List<String> tags = config.getInterestTags();
        String category = article.getCategory();
        int score = 0;

        // 根据分类在兴趣列表中的位置计算分数
        for (int i = 0; i < tags.size(); i++) {
            if (category != null && category.toLowerCase().contains(tags.get(i).toLowerCase())) {
                // 越靠前优先级越高
                score = (tags.size() - i) * 10;
                break;
            }
        }

        // AI相关的额外加分
        String title = article.getTitle().toLowerCase();
        String desc = article.getDescription().toLowerCase();
        if (title.contains("ai") || title.contains("llm") || title.contains("gpt") ||
                title.contains("机器学习") || title.contains("深度学习") ||
                desc.contains("ai应用") || desc.contains("大模型")) {
            score += 15;
        }

        article.setPriorityScore(score);
    }

    private String callSiliconFlowApi(String prompt) throws IOException {
        JsonObject message = new JsonObject();
        message.addProperty("role", "user");
        message.addProperty("content", prompt);

        JsonArray messages = new JsonArray();
        messages.add(message);

        JsonObject requestBody = new JsonObject();
        requestBody.addProperty("model", config.getAi().getModel());
        requestBody.add("messages", messages);
        requestBody.addProperty("max_tokens", 300);
        requestBody.addProperty("temperature", 0.5);

        Request request = new Request.Builder()
                .url(config.getAi().getApiUrl())
                .addHeader("Authorization", "Bearer " + config.getAi().getApiKey())
                .addHeader("Content-Type", "application/json")
                .post(RequestBody.create(
                        gson.toJson(requestBody),
                        MediaType.parse("application/json")))
                .build();

        try (Response response = httpClient.newCall(request).execute()) {
            String responseBody = response.body() != null ? response.body().string() : "";

            if (!response.isSuccessful()) {
                // 针对不同错误码给出更明确的信息
                String errorMsg = switch (response.code()) {
                    case 401 -> "API Key 无效或已过期";
                    case 429 -> "请求频率超限，请稍后重试";
                    case 500, 502, 503 -> "AI 服务暂时不可用";
                    default -> "HTTP " + response.code();
                };
                throw new IOException("API 请求失败: " + errorMsg + " - " + responseBody);
            }

            try {
                JsonObject json = gson.fromJson(responseBody, JsonObject.class);
                return json.getAsJsonArray("choices")
                        .get(0).getAsJsonObject()
                        .getAsJsonObject("message")
                        .get("content").getAsString()
                        .trim();
            } catch (JsonParseException | NullPointerException e) {
                throw new IOException("解析 AI 响应失败: " + e.getMessage());
            }
        }
    }

    /**
     * 获取处理统计（可用于监控）
     */
    public String getStats() {
        return String.format("成功: %d, 失败: %d, 重试: %d",
                successCount.get(), failureCount.get(), retryCount.get());
    }
}
