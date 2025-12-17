package com.mindnest.config;

import lombok.Getter;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.io.Resource;

import jakarta.annotation.PostConstruct;
import java.io.IOException;
import java.nio.charset.StandardCharsets;

/**
 * Configuration for AI prompts loaded from external files.
 * Prompts are stored in src/main/resources/prompts/ directory.
 */
@Configuration
@Slf4j
@Getter
public class PromptConfig {

    @Value("classpath:prompts/system-prompt.txt")
    private Resource systemPromptResource;

    @Value("classpath:prompts/intent-detection-prompt.txt")
    private Resource intentDetectionPromptResource;

    private String systemPrompt;
    private String intentDetectionPrompt;

    @PostConstruct
    public void loadPrompts() throws IOException {
        this.systemPrompt = loadResource(systemPromptResource, "system-prompt.txt");
        this.intentDetectionPrompt = loadResource(intentDetectionPromptResource, "intent-detection-prompt.txt");
        log.info("Loaded prompts: system-prompt ({} chars), intent-detection ({} chars)",
                systemPrompt.length(), intentDetectionPrompt.length());
    }

    private String loadResource(Resource resource, String name) throws IOException {
        try {
            return resource.getContentAsString(StandardCharsets.UTF_8);
        } catch (IOException e) {
            log.error("Failed to load prompt: {}", name, e);
            throw e;
        }
    }
}
