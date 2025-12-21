package com.mindnest.agent;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.google.cloud.vertexai.VertexAI;
import com.google.cloud.vertexai.api.GenerateContentResponse;
import com.google.cloud.vertexai.api.GenerationConfig;
import com.google.cloud.vertexai.generativeai.GenerativeModel;
import com.google.cloud.vertexai.generativeai.ResponseHandler;
import com.mindnest.config.PromptConfig;
import com.mindnest.model.entity.Message;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Detects user intent from message chunks using LLM.
 * Handles message decomposition and structured intent extraction.
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class IntentDetectionEngine {

    private final VertexAI vertexAI;
    private final ObjectMapper objectMapper;
    private final PromptConfig promptConfig;

    @Value("${vertex-ai.models.flash}")
    private String flashModel;

    /**
     * Decompose message into independent logical chunks using LLM.
     * Example: "Budget 50000 and buy milk" → ["Budget 50000", "buy milk"]
     */
    public List<String> decompose(String message) {
        try {
            GenerativeModel decomposeModel = new GenerativeModel.Builder()
                    .setModelName(flashModel)
                    .setVertexAi(vertexAI)
                    .setGenerationConfig(GenerationConfig.newBuilder()
                            .setMaxOutputTokens(1024)
                            .setTemperature(0.0f)
                            .build())
                    .build();

            String prompt = promptConfig.getDecompositionPrompt().formatted(message);
            GenerateContentResponse response = decomposeModel.generateContent(prompt);
            String jsonResponse = ResponseHandler.getText(response);

            log.debug("Decomposition raw response: {}", jsonResponse);

            return parseChunkArray(jsonResponse);

        } catch (Exception e) {
            log.error("Decomposition failed, treating as single chunk: {}", e.getMessage());
            return List.of(message);
        }
    }

    /**
     * Parse JSON array of strings from decomposition response.
     */
    private List<String> parseChunkArray(String jsonResponse) {
        try {
            String cleaned = cleanJsonResponse(jsonResponse);
            return objectMapper.readValue(cleaned, new TypeReference<List<String>>() {});
        } catch (Exception e) {
            log.error("Failed to parse chunk array: {}", e.getMessage());
            return List.of(jsonResponse);
        }
    }

    /**
     * Detect intent for a single chunk using LLM.
     */
    public ChunkIntent detectChunkIntent(String chunk, String contextSummary) {
        try {
            GenerativeModel intentModel = new GenerativeModel.Builder()
                    .setModelName(flashModel)
                    .setVertexAi(vertexAI)
                    .setGenerationConfig(GenerationConfig.newBuilder()
                            .setMaxOutputTokens(1024)
                            .setTemperature(0.0f)
                            .build())
                    .build();

            String prompt = promptConfig.getIntentDetectionPrompt().formatted(chunk, contextSummary);
            GenerateContentResponse response = intentModel.generateContent(prompt);
            String jsonResponse = ResponseHandler.getText(response);

            log.debug("Chunk intent raw response: {}", jsonResponse);

            return parseChunkIntent(jsonResponse);

        } catch (Exception e) {
            log.error("Chunk intent detection failed: {}", e.getMessage());
            return new ChunkIntent("CHAT", null, null, chunk, Map.of(), List.of(), null);
        }
    }

    /**
     * Parse chunk intent JSON response.
     */
    private ChunkIntent parseChunkIntent(String jsonResponse) {
        try {
            String cleaned = cleanJsonResponse(jsonResponse);
            JsonNode json = objectMapper.readTree(cleaned);

            String intent = json.has("intent") ? json.get("intent").asText("CHAT") : "CHAT";
            String type = json.has("type") && !json.get("type").isNull() ? json.get("type").asText() : null;
            String subtype = json.has("subtype") && !json.get("subtype").isNull() ? json.get("subtype").asText() : null;
            String content = json.has("content") && !json.get("content").isNull() ? json.get("content").asText() : "";
            String searchQuery = json.has("search_query") && !json.get("search_query").isNull()
                    ? json.get("search_query").asText() : null;

            // Parse properties
            Map<String, Object> properties = parseProperties(json);

            // Parse relations
            List<RelationIntent> relations = parseRelations(json);

            return new ChunkIntent(intent, type, subtype, content, properties, relations, searchQuery);

        } catch (Exception e) {
            log.error("Failed to parse chunk intent JSON: {}", e.getMessage());
            return new ChunkIntent("CHAT", null, null, "", Map.of(), List.of(), null);
        }
    }

    /**
     * Parse properties from JSON node.
     */
    private Map<String, Object> parseProperties(JsonNode json) {
        Map<String, Object> properties = new HashMap<>();
        if (json.has("properties") && json.get("properties").isObject()) {
            JsonNode props = json.get("properties");
            props.fieldNames().forEachRemaining(field -> {
                JsonNode value = props.get(field);
                if (!value.isNull()) {
                    if (value.isNumber()) {
                        properties.put(field, value.numberValue());
                    } else if (value.isBoolean()) {
                        properties.put(field, value.booleanValue());
                    } else if (value.isArray()) {
                        // Handle array values (e.g., selected_indices)
                        List<Object> arrayValues = new ArrayList<>();
                        for (JsonNode element : value) {
                            if (element.isNumber()) {
                                arrayValues.add(element.numberValue());
                            } else {
                                arrayValues.add(element.asText());
                            }
                        }
                        properties.put(field, arrayValues);
                    } else {
                        properties.put(field, value.asText());
                    }
                }
            });
        }
        return properties;
    }

    /**
     * Parse relations from JSON node.
     */
    private List<RelationIntent> parseRelations(JsonNode json) {
        List<RelationIntent> relations = new ArrayList<>();
        if (json.has("relations") && json.get("relations").isArray()) {
            for (JsonNode relNode : json.get("relations")) {
                String toQuery = relNode.has("to_query") ? relNode.get("to_query").asText() : null;
                String relType = relNode.has("type") ? relNode.get("type").asText() : null;
                if (toQuery != null && relType != null) {
                    relations.add(new RelationIntent(toQuery, relType));
                }
            }
        }
        return relations;
    }

    /**
     * Build summary of conversation context for intent detection.
     */
    public String buildContextSummary(List<Message> context) {
        if (context.isEmpty()) {
            return "No previous context";
        }

        StringBuilder sb = new StringBuilder();
        int count = 0;
        for (Message msg : context) {
            if (count >= 5) break;  // Last 5 messages max
            String role = msg.getRole() == Message.Role.user ? "User" : "Assistant";
            sb.append(role).append(": ").append(truncate(msg.getContent(), 100)).append("\n");
            count++;
        }
        return sb.toString();
    }

    /**
     * Clean JSON response by removing markdown code blocks.
     */
    private String cleanJsonResponse(String jsonResponse) {
        String cleaned = jsonResponse.trim();
        if (cleaned.startsWith("```json")) {
            cleaned = cleaned.substring(7);
        }
        if (cleaned.startsWith("```")) {
            cleaned = cleaned.substring(3);
        }
        if (cleaned.endsWith("```")) {
            cleaned = cleaned.substring(0, cleaned.length() - 3);
        }
        return cleaned.trim();
    }

    private String truncate(String text, int maxLen) {
        return text != null && text.length() > maxLen ? text.substring(0, maxLen) + "..." : text;
    }
}
