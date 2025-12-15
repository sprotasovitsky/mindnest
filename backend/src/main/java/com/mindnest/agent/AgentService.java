package com.mindnest.agent;

import com.mindnest.model.dto.ChatResponse;
import com.mindnest.service.LlmService;
import com.mindnest.service.ModelRouter;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.util.List;

@Service
@RequiredArgsConstructor
@Slf4j
public class AgentService {

    private final LlmService llmService;
    private final ModelRouter modelRouter;

    private static final String SYSTEM_PROMPT = """
            Ты — MindNest, персональный AI-ассистент для управления знаниями и задачами.

            Твоя роль:
            - Ты секретарь-помощник, который помогает структурировать информацию
            - Ты запоминаешь всё, что тебе говорят, и можешь найти это позже
            - Ты помогаешь управлять задачами и проектами
            - Ты отвечаешь кратко и по делу

            Правила:
            - Если пользователь сообщает факт или информацию — подтверди что запомнил
            - Если пользователь спрашивает — отвечай на основе контекста
            - Если не знаешь ответа — честно скажи об этом
            - Используй markdown для форматирования когда уместно
            - Отвечай на том языке, на котором спрашивают

            Сейчас ты находишься в режиме MVP без доступа к базе знаний.
            Пока просто веди диалог и помогай пользователю.
            """;

    public ChatResponse processMessage(String message, String projectId) {
        log.info("Processing message for project: {}", projectId);

        try {
            // Select appropriate model
            String model = modelRouter.selectModel(message);
            ModelRouter.TaskComplexity complexity = modelRouter.assessComplexity(message);

            // Generate response
            String response = llmService.generateWithSystemPrompt(SYSTEM_PROMPT, message, model);

            // Calculate confidence based on complexity and response
            double confidence = calculateConfidence(complexity, response);

            return ChatResponse.builder()
                    .reply(response)
                    .sources(List.of()) // TODO: Add sources when knowledge base is integrated
                    .confidence(confidence)
                    .build();

        } catch (IOException e) {
            log.error("Error calling LLM: ", e);
            return ChatResponse.builder()
                    .reply("Извини, произошла ошибка при обработке запроса. Попробуй ещё раз.")
                    .sources(List.of())
                    .confidence(0.0)
                    .build();
        }
    }

    private double calculateConfidence(ModelRouter.TaskComplexity complexity, String response) {
        // Base confidence by complexity
        double base = switch (complexity) {
            case SIMPLE -> 0.95;
            case MEDIUM -> 0.85;
            case COMPLEX -> 0.75;
        };

        // Adjust based on response characteristics
        if (response.contains("не уверен") || response.contains("возможно") ||
                response.contains("not sure") || response.contains("maybe")) {
            base -= 0.1;
        }

        if (response.contains("не знаю") || response.contains("don't know")) {
            base -= 0.2;
        }

        return Math.max(0.1, Math.min(1.0, base));
    }
}
