package com.mindnest.agent;

import com.google.cloud.vertexai.VertexAI;
import com.google.cloud.vertexai.api.GenerateContentResponse;
import com.google.cloud.vertexai.api.GenerationConfig;
import com.google.cloud.vertexai.generativeai.GenerativeModel;
import com.google.cloud.vertexai.generativeai.ResponseHandler;
import com.mindnest.config.PromptConfig;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * Generates natural language responses using LLM.
 * Handles search results, action summaries, and chat responses.
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class ResponseGenerator {

    private final VertexAI vertexAI;
    private final PromptConfig promptConfig;

    @Value("${vertex-ai.models.flash}")
    private String flashModel;

    /**
     * Generate combined response from all chunk results.
     * Handles clarification, search results, actions, and chat.
     */
    public String generateCombinedResponse(List<ChunkResult> results, String originalMessage, String context) {
        try {
            // Check for clarification results first - return directly without LLM
            for (ChunkResult result : results) {
                if (result.needsClarification()) {
                    return result.description();  // Return clarification message as-is
                }
            }

            // Build summary of what was done
            StringBuilder actionSummary = new StringBuilder();
            StringBuilder searchResults = new StringBuilder();

            for (ChunkResult result : results) {
                if (result.searchResults() != null) {
                    searchResults.append(result.searchResults()).append("\n");
                } else if (result.description() != null && !"chat".equals(result.description())) {
                    actionSummary.append("- ").append(result.description());
                    if (!result.linkedTo().isEmpty()) {
                        actionSummary.append(" (linked to: ").append(String.join(", ", result.linkedTo())).append(")");
                    }
                    actionSummary.append("\n");
                }
            }

            // If there are search results, use LLM to generate response with calculations
            if (searchResults.length() > 0) {
                return generateSearchResponse(searchResults.toString(), originalMessage);
            }

            // If there are actions, use LLM to generate natural response
            if (actionSummary.length() > 0) {
                return generateActionResponse(actionSummary.toString(), originalMessage);
            }

            // Chat response
            return generateChatResponse(originalMessage, context);

        } catch (Exception e) {
            log.error("Failed to generate combined response: {}", e.getMessage());
            return "Done.";
        }
    }

    /**
     * Generate response for search results, including calculations if needed.
     */
    public String generateSearchResponse(String searchResults, String originalQuestion) {
        try {
            GenerativeModel responseModel = new GenerativeModel.Builder()
                    .setModelName(flashModel)
                    .setVertexAi(vertexAI)
                    .setGenerationConfig(GenerationConfig.newBuilder()
                            .setMaxOutputTokens(1024)
                            .setTemperature(0.3f)
                            .build())
                    .build();

            String prompt = promptConfig.getSearchResponsePrompt()
                    .formatted(searchResults, originalQuestion);

            GenerateContentResponse response = responseModel.generateContent(prompt);
            return ResponseHandler.getText(response);

        } catch (Exception e) {
            log.error("Failed to generate search response: {}", e.getMessage());
            return searchResults;
        }
    }

    /**
     * Generate natural response for actions taken.
     */
    public String generateActionResponse(String actionSummary, String originalMessage) {
        try {
            GenerativeModel responseModel = new GenerativeModel.Builder()
                    .setModelName(flashModel)
                    .setVertexAi(vertexAI)
                    .setGenerationConfig(GenerationConfig.newBuilder()
                            .setMaxOutputTokens(512)
                            .setTemperature(0.3f)
                            .build())
                    .build();

            String prompt = promptConfig.getActionResponsePrompt()
                    .formatted(actionSummary, originalMessage);

            GenerateContentResponse response = responseModel.generateContent(prompt);
            return ResponseHandler.getText(response);

        } catch (Exception e) {
            log.error("Failed to generate action response: {}", e.getMessage());
            return "Saved.";
        }
    }

    /**
     * Generate chat response (no tools needed).
     */
    public String generateChatResponse(String message, String context) {
        try {
            GenerativeModel chatModel = new GenerativeModel.Builder()
                    .setModelName(flashModel)
                    .setVertexAi(vertexAI)
                    .setGenerationConfig(GenerationConfig.newBuilder()
                            .setMaxOutputTokens(512)
                            .setTemperature(0.7f)
                            .build())
                    .build();

            String prompt = promptConfig.getSystemPrompt() + "\n\nContext:\n" + context +
                    "\n\nUser message: " + message + "\n\nRespond briefly:";

            GenerateContentResponse response = chatModel.generateContent(prompt);
            return ResponseHandler.getText(response);

        } catch (Exception e) {
            log.error("Failed to generate chat response: {}", e.getMessage());
            return "I understand.";
        }
    }

    /**
     * Calculate confidence score based on response content.
     */
    public double calculateConfidence(String response) {
        double base = 0.85;

        if (response.contains("not sure") || response.contains("maybe") ||
                response.contains("perhaps") || response.contains("possibly")) {
            base -= 0.1;
        }

        if (response.contains("don't know") || response.contains("I'm not certain") ||
                response.contains("cannot answer") || response.contains("no results")) {
            base -= 0.2;
        }

        return Math.max(0.1, Math.min(1.0, base));
    }
}
