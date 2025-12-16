package com.mindnest.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.regex.Pattern;

/**
 * Routes requests to appropriate Gemini model based on task complexity.
 *
 * Strategy:
 * - Flash (default): Simple queries, task management, basic retrieval
 * - Pro: Complex reasoning, multi-step planning, knowledge synthesis
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class ModelRouter {

    @Value("${vertex-ai.models.chat}")
    private String flashModel;

    @Value("${vertex-ai.models.chat-pro}")
    private String proModel;

    // Patterns that indicate complex tasks requiring Pro model (multilingual support)
    private static final List<Pattern> COMPLEX_PATTERNS = List.of(
            Pattern.compile("(?i)(объясни|explain|analyze|анализ|сравни|compare)"),
            Pattern.compile("(?i)(план|plan|стратегия|strategy|архитектур)"),
            Pattern.compile("(?i)(почему|why|как это работает|how does.+work)"),
            Pattern.compile("(?i)(преимущества и недостатки|pros and cons|trade-?off)"),
            Pattern.compile("(?i)(разбей на|decompose|break down|декомпозиц)"),
            Pattern.compile("(?i)(связь между|relationship|correlation|зависимост)")
    );

    // Patterns for simple tasks that can use Flash (multilingual support)
    private static final List<Pattern> SIMPLE_PATTERNS = List.of(
            Pattern.compile("(?i)(создай задачу|create task|добавь|add)"),
            Pattern.compile("(?i)(покажи|show|список|list|найди|find|search)"),
            Pattern.compile("(?i)(статус|status|сколько|how many|когда|when)"),
            Pattern.compile("(?i)(удали|delete|отмени|cancel|закрой|close)"),
            Pattern.compile("(?i)(напомни|remind|дедлайн|deadline)")
    );

    public enum TaskComplexity {
        SIMPLE,
        MEDIUM,
        COMPLEX
    }

    public String selectModel(String userMessage) {
        TaskComplexity complexity = assessComplexity(userMessage);
        String model = switch (complexity) {
            case SIMPLE, MEDIUM -> flashModel;
            case COMPLEX -> proModel;
        };

        log.debug("Selected model {} for complexity {}", model, complexity);
        return model;
    }

    public TaskComplexity assessComplexity(String message) {
        // Check for complex patterns first
        for (Pattern pattern : COMPLEX_PATTERNS) {
            if (pattern.matcher(message).find()) {
                log.debug("Complex pattern matched: {}", pattern.pattern());
                return TaskComplexity.COMPLEX;
            }
        }

        // Check for simple patterns
        for (Pattern pattern : SIMPLE_PATTERNS) {
            if (pattern.matcher(message).find()) {
                log.debug("Simple pattern matched: {}", pattern.pattern());
                return TaskComplexity.SIMPLE;
            }
        }

        // Check message length as additional signal
        if (message.length() > 500) {
            return TaskComplexity.COMPLEX;
        } else if (message.length() < 50) {
            return TaskComplexity.SIMPLE;
        }

        return TaskComplexity.MEDIUM;
    }

    public String getFlashModel() {
        return flashModel;
    }

    public String getProModel() {
        return proModel;
    }
}
