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
        // Inject resources using reflection
        ReflectionTestUtils.setField(promptConfig, "systemPromptResource",
                new ClassPathResource("prompts/system-prompt.txt"));
        ReflectionTestUtils.setField(promptConfig, "intentDetectionPromptResource",
                new ClassPathResource("prompts/intent-detection-prompt.txt"));
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
        assertTrue(prompt.contains("create_knowledge"));
        assertTrue(prompt.contains("search_knowledge"));
        assertTrue(prompt.contains("delete_knowledge"));
    }

    @Test
    void intentDetectionPrompt_containsAllIntents() {
        String prompt = promptConfig.getIntentDetectionPrompt();
        assertTrue(prompt.contains("SAVE"));
        assertTrue(prompt.contains("SEARCH"));
        assertTrue(prompt.contains("UPDATE"));
        assertTrue(prompt.contains("DELETE"));
        assertTrue(prompt.contains("TASK"));
        assertTrue(prompt.contains("COMPLETE"));
        assertTrue(prompt.contains("CHAT"));
    }

    @Test
    void intentDetectionPrompt_supportsRussian() {
        String prompt = promptConfig.getIntentDetectionPrompt();
        // Check for Russian keywords
        assertTrue(prompt.contains("сегодня") || prompt.contains("что") || prompt.contains("удали"));
    }

    @Test
    void intentDetectionPrompt_canBeFormatted() {
        String prompt = promptConfig.getIntentDetectionPrompt();
        String testMessage = "Test message";
        String formatted = prompt.formatted(testMessage);
        assertTrue(formatted.contains(testMessage));
        assertFalse(formatted.contains("%s")); // Placeholder should be replaced
    }
}
