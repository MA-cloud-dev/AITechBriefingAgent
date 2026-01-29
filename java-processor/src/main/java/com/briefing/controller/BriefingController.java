package com.briefing.controller;

import com.briefing.model.Article;
import com.briefing.scheduler.BriefingScheduler;
import com.briefing.service.RedisService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Slf4j
@RestController
@RequestMapping("/api/briefing")
@RequiredArgsConstructor
public class BriefingController {

    private final RedisService redisService;
    private final BriefingScheduler briefingScheduler;

    /**
     * 健康检查
     */
    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> health() {
        Map<String, Object> result = new HashMap<>();
        result.put("status", "UP");
        result.put("redis", redisService.ping() ? "connected" : "disconnected");
        return ResponseEntity.ok(result);
    }

    /**
     * 查看 Redis 中的文章
     */
    @GetMapping("/articles")
    public ResponseEntity<List<Article>> getArticles() {
        List<Article> articles = redisService.getTodayArticles();
        return ResponseEntity.ok(articles);
    }

    /**
     * 手动触发邮件发送
     */
    @GetMapping("/trigger")
    public ResponseEntity<Map<String, String>> trigger() {
        log.info("收到手动触发请求");

        try {
            briefingScheduler.processBriefing();
            return ResponseEntity.ok(Map.of("message", "处理完成，邮件已发送"));
        } catch (Exception e) {
            log.error("手动触发失败: {}", e.getMessage());
            return ResponseEntity.internalServerError()
                    .body(Map.of("error", e.getMessage()));
        }
    }
}
