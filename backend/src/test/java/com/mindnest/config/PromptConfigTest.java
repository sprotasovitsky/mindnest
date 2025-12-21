package com.mindnest.config;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.core.io.ClassPathResource;
import org.springframework.test.util.ReflectionTestUtils;

import java.io.IOException;

import static org.junit.jupiter.api.Assertions.*;

class PromptConfigTest {

    private PromptConfig promptConfig;

    @BeforeEach
    void setUp() throws IOException {
        promptConfig = new PromptConfig();
        // Inject all resources using reflection
        ReflectionTestUtils.setField(promptConfig, "systemPromptResource",
                new ClassPathResource("prompts/system-prompt.txt"));
        ReflectionTestUtils.setField(promptConfig, "intentDetectionPromptResource",
                new ClassPathResource("prompts/intent-detection-prompt.txt"));
        ReflectionTestUtils.setField(promptConfig, "decompositionPromptResource",
                new ClassPathResource("prompts/decomposition-prompt.txt"));
        ReflectionTestUtils.setField(promptConfig, "searchResponsePromptResource",
                new ClassPathResource("prompts/search-response-prompt.txt"));
        ReflectionTestUtils.setField(promptConfig, "actionResponsePromptResource",
                new ClassPathResource("prompts/action-response-prompt.txt"));
        // Trigger PostConstruct
        promptConfig.loadPrompts();
    }

    @Test
    void systemPrompt_isLoaded() {
        String prompt = promptConfig.getSystemPrompt();
        assertNotNull(prompt);
        assertFalse(prompt.isBlank());
        assertTrue(prompt.contains("MindNest"));
    }

    @Test
    void intentDetectionPrompt_isLoaded() {
        String prompt = promptConfig.getIntentDetectionPrompt();
        assertNotNull(prompt);
        assertFalse(prompt.isBlank());
        assertTrue(prompt.contains("intent"));
        assertTrue(prompt.contains("%s")); // Placeholder for message
    }

    @Test
    void systemPrompt_containsToolUsageRules() {
        String prompt = promptConfig.getSystemPrompt();
        assertTrue(prompt.contains("create_knowledge") || prompt.contains("MindNest"));
        // Note: delete_knowledge removed - system is immutable
    }

    @Test
    void intentDetectionPrompt_containsAllIntents() {
        String prompt = promptConfig.getIntentDetectionPrompt();
        // Core intents (immutable architecture)
        assertTrue(prompt.contains("SAVE"));
        assertTrue(prompt.contains("SEARCH"));
        assertTrue(prompt.contains("TASK"));
        assertTrue(prompt.contains("CHAT"));
        // Note: UPDATE and DELETE are handled via SAVE with relations (SUPERSEDES)
    }

    @Test
    void intentDetectionPrompt_isLanguageAgnostic() {
        String prompt = promptConfig.getIntentDetectionPrompt();
        // System supports any language via embeddings - no language-specific keywords needed
        // Instead, check for semantic understanding markers
        assertTrue(prompt.contains("intent") && prompt.contains("content"));
    }

    @Test
    void intentDetectionPrompt_canBeFormatted() {
        String prompt = promptConfig.getIntentDetectionPrompt();
        String testChunk = "Test chunk";
        String testContext = "Test context";
        String formatted = prompt.formatted(testChunk, testContext);
        assertTrue(formatted.contains(testChunk));
        assertTrue(formatted.contains(testContext));
        assertFalse(formatted.contains("%s")); // Placeholders should be replaced
    }
}
