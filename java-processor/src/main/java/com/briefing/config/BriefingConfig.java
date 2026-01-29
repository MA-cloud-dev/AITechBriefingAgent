package com.briefing.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

import lombok.Data;
import java.util.List;

@Data
@Configuration
@ConfigurationProperties(prefix = "briefing")
public class BriefingConfig {

    private Ai ai = new Ai();
    private String recipientEmail;
    private String redisKeyPrefix;
    private int maxArticles = 10;
    private List<String> interestTags;

    @Data
    public static class Ai {
        private String apiKey;
        private String apiUrl;
        private String model;
    }
}
