package com.mindnest.service;

import com.google.cloud.vertexai.VertexAI;
import com.google.cloud.vertexai.api.GenerateContentResponse;
import com.google.cloud.vertexai.api.GenerationConfig;
import com.google.cloud.vertexai.generativeai.ChatSession;
import com.google.cloud.vertexai.generativeai.ContentMaker;
import com.google.cloud.vertexai.generativeai.GenerativeModel;
import com.google.cloud.vertexai.generativeai.ResponseHandler;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.IOException;

@Service
@RequiredArgsConstructor
@Slf4j
public class LlmService {

    private final VertexAI vertexAI;

    @Value("${vertex-ai.models.chat}")
    private String defaultModel;

    @Value("${vertex-ai.models.chat-pro}")
    private String proModel;

    public String generateResponse(String prompt) throws IOException {
        return generateResponse(prompt, defaultModel);
    }

    public String generateResponsePro(String prompt) throws IOException {
        return generateResponse(prompt, proModel);
    }

    public String generateResponse(String prompt, String modelName) throws IOException {
        log.debug("Generating response with model: {}", modelName);

        GenerativeModel model = new GenerativeModel.Builder()
                .setModelName(modelName)
                .setVertexAi(vertexAI)
                .setGenerationConfig(GenerationConfig.newBuilder()
                        .setMaxOutputTokens(2048)
                        .setTemperature(0.7f)
                        .setTopP(0.95f)
                        .build())
                .build();

        GenerateContentResponse response = model.generateContent(prompt);
        String text = ResponseHandler.getText(response);

        log.debug("Generated response: {} chars", text.length());
        return text;
    }

    public String generateWithSystemPrompt(String systemPrompt, String userMessage) throws IOException {
        return generateWithSystemPrompt(systemPrompt, userMessage, defaultModel);
    }

    public String generateWithSystemPrompt(String systemPrompt, String userMessage, String modelName) throws IOException {
        log.debug("Generating with system prompt, model: {}", modelName);

        // Combine system prompt with user message
        String fullPrompt = String.format("""
                System: %s

                User: %s

                Assistant:""", systemPrompt, userMessage);

        GenerativeModel model = new GenerativeModel.Builder()
                .setModelName(modelName)
                .setVertexAi(vertexAI)
                .setGenerationConfig(GenerationConfig.newBuilder()
                        .setMaxOutputTokens(2048)
                        .setTemperature(0.7f)
                        .setTopP(0.95f)
                        .build())
                .build();

        GenerateContentResponse response = model.generateContent(fullPrompt);
        String text = ResponseHandler.getText(response);

        log.debug("Generated response: {} chars", text.length());
        return text;
    }

    public String chat(String userMessage, String modelName) throws IOException {
        log.debug("Chat with model: {}", modelName);

        GenerativeModel model = new GenerativeModel.Builder()
                .setModelName(modelName)
                .setVertexAi(vertexAI)
                .setGenerationConfig(GenerationConfig.newBuilder()
                        .setMaxOutputTokens(2048)
                        .setTemperature(0.7f)
                        .setTopP(0.95f)
                        .build())
                .build();

        ChatSession chatSession = model.startChat();
        GenerateContentResponse response = chatSession.sendMessage(userMessage);
        String text = ResponseHandler.getText(response);

        log.debug("Chat response: {} chars", text.length());
        return text;
    }
}
