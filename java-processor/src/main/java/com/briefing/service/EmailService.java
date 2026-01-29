package com.briefing.service;

import com.briefing.config.BriefingConfig;
import com.briefing.model.Article;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import jakarta.mail.MessagingException;
import jakarta.mail.internet.MimeMessage;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.MimeMessageHelper;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class EmailService {

    private final JavaMailSender mailSender;
    private final BriefingConfig config;

    /**
     * 发送技术日报邮件 (带足球数据)
     */
    public void sendBriefingEmail(List<Article> articles, JsonObject footballData) throws MessagingException {
        String today = LocalDate.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd"));
        String subject = "📰 技术日报 - " + today;
        String content = buildEmailContent(articles, footballData, today);

        MimeMessage message = mailSender.createMimeMessage();
        MimeMessageHelper helper = new MimeMessageHelper(message, true, "UTF-8");

        String recipient = config.getRecipientEmail();
        helper.setTo(recipient != null ? recipient : "");
        helper.setSubject(subject);
        helper.setText(content, false);

        mailSender.send(message);
        log.info("邮件发送成功: {} -> {}", subject, config.getRecipientEmail());
    }

    /**
     * 发送技术日报邮件 (无足球数据)
     */
    public void sendBriefingEmail(List<Article> articles) throws MessagingException {
        sendBriefingEmail(articles, null);
    }

    /**
     * 构建邮件内容 (Markdown 格式) - 按分类分组显示
     */
    private String buildEmailContent(List<Article> articles, JsonObject footballData, String today) {
        StringBuilder sb = new StringBuilder();

        sb.append("# 📰 技术日报 - ").append(today).append("\n\n");
        sb.append("---\n\n");

        // 按分类分组
        Map<String, List<Article>> grouped = articles.stream()
                .collect(Collectors.groupingBy(a -> a.getCategory() != null ? a.getCategory() : "其他"));

        // 分类显示顺序和图标（AI细分优先）
        String[][] categoryConfig = {
                { "AI应用", "🚀" },
                { "AI前沿", "🔬" },
                { "AI", "🤖" },
                { "Python", "🐍" },
                { "Java", "☕" },
                { "Go", "🔷" },
                { "架构", "🏗️" },
                { "前端", "🎨" },
                { "其他", "📌" }
        };

        int articleIndex = 1;
        for (String[] catConfig : categoryConfig) {
            String category = catConfig[0];
            String icon = catConfig[1];
            List<Article> categoryArticles = grouped.get(category);

            if (categoryArticles == null || categoryArticles.isEmpty()) {
                continue;
            }

            sb.append("## ").append(icon).append(" ").append(category).append("\n\n");

            for (Article article : categoryArticles) {
                sb.append(String.format("### %d. [%s](%s)\n",
                        articleIndex++, article.getTitle(), article.getUrl()));

                String highlight = article.getHighlight();
                String sourceLabel = getSourceLabel(article.getSource());
                if (highlight != null && !highlight.isEmpty()) {
                    sb.append("🏷️ **").append(highlight).append("** | ").append(sourceLabel).append("\n");
                } else {
                    sb.append(sourceLabel).append("\n");
                }

                sb.append("> ").append(article.getAiSummary() != null
                        ? article.getAiSummary()
                        : article.getDescription()).append("\n\n");
            }
            sb.append("---\n\n");
        }

        // 添加足球数据
        if (footballData != null) {
            sb.append(buildFootballSection(footballData));
        }

        sb.append("*由 AI Tech Briefing Agent 自动生成*\n");
        sb.append("*今日共推送 ").append(articles.size()).append(" 篇精选文章*\n");

        return sb.toString();
    }

    /**
     * 构建足球模块内容
     */
    private String buildFootballSection(JsonObject data) {
        StringBuilder sb = new StringBuilder();
        sb.append("## ⚽ 英超快报\n\n");

        // 最近比赛
        if (data.has("matches")) {
            JsonObject matchesObj = data.getAsJsonObject("matches");
            JsonArray matches = matchesObj.getAsJsonArray("matches");

            if (matches != null && !matches.isEmpty()) {
                sb.append("### 📅 最近比赛\n\n");
                int count = 0;
                for (var elem : matches) {
                    if (count >= 5)
                        break;
                    JsonObject match = elem.getAsJsonObject();
                    String status = match.get("status").getAsString();
                    if (!"FINISHED".equals(status))
                        continue;

                    String home = match.get("home_team").getAsString();
                    String away = match.get("away_team").getAsString();
                    int homeScore = match.get("home_score").getAsInt();
                    int awayScore = match.get("away_score").getAsInt();

                    if (homeScore > awayScore) {
                        sb.append(String.format("- **%s** %d - %d %s\n", home, homeScore, awayScore, away));
                    } else if (awayScore > homeScore) {
                        sb.append(String.format("- %s %d - %d **%s**\n", home, homeScore, awayScore, away));
                    } else {
                        sb.append(String.format("- %s %d - %d %s\n", home, homeScore, awayScore, away));
                    }
                    count++;
                }
                sb.append("\n");
            }
        }

        // 积分榜
        if (data.has("standings")) {
            JsonObject standings = data.getAsJsonObject("standings");
            JsonArray teams = standings.getAsJsonArray("teams");

            if (teams != null && !teams.isEmpty()) {
                sb.append("### 🏆 积分榜 Top 6\n\n");
                sb.append("| # | 球队 | 场 | 胜 | 平 | 负 | 积分 |\n");
                sb.append("|---|------|----|----|----|----|------|\n");

                int count = 0;
                for (var elem : teams) {
                    if (count >= 6)
                        break;
                    JsonObject team = elem.getAsJsonObject();
                    int pos = team.get("position").getAsInt();
                    String name = team.get("name").getAsString();
                    int played = team.get("played").getAsInt();
                    int won = team.get("won").getAsInt();
                    int draw = team.get("draw").getAsInt();
                    int lost = team.get("lost").getAsInt();
                    int points = team.get("points").getAsInt();

                    if (pos <= 4) {
                        sb.append(String.format("| **%d** | **%s** | %d | %d | %d | %d | **%d** |\n",
                                pos, name, played, won, draw, lost, points));
                    } else {
                        sb.append(String.format("| %d | %s | %d | %d | %d | %d | %d |\n",
                                pos, name, played, won, draw, lost, points));
                    }
                    count++;
                }
                sb.append("\n");
            }
        }

        sb.append("---\n\n");
        return sb.toString();
    }

    /**
     * 获取来源标签
     */
    private String getSourceLabel(String source) {
        return switch (source) {
            case "github" -> "📦 GitHub";
            case "github-ai" -> "🤖 GitHub AI";
            case "juejin" -> "📝 掘金";
            case "hackernews" -> "🔶 Hacker News";
            case "huggingface" -> "🤗 HuggingFace";
            case "arxiv" -> "📄 arXiv";
            case "futurepedia", "toolify" -> "🚀 AI工具";
            default -> "📄 " + source;
        };
    }
}
