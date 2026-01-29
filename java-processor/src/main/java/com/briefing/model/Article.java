package com.briefing.model;

import lombok.Data;
import java.util.Map;

@Data
public class Article {
    private String id;
    private String title;
    private String url;
    private String source; // "github", "juejin", "hackernews"
    private String description;
    private Map<String, Object> extra;
    private String crawlTime;

    // AI 生成的字段
    private String aiSummary; // AI摘要
    private String category; // AI分类：AI/Python/Java/Go/架构/前端/其他
    private String highlight; // 一句话亮点
    private int priorityScore; // 优先级分数 (用于排序)
}
