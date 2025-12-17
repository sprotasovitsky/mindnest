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

    @Value("classpath:prompts/decomposition-prompt.txt")
    private Resource decompositionPromptResource;

    @Value("classpath:prompts/search-response-prompt.txt")
    private Resource searchResponsePromptResource;

    @Value("classpath:prompts/action-response-prompt.txt")
    private Resource actionResponsePromptResource;

    private String systemPrompt;
    private String intentDetectionPrompt;
    private String decompositionPrompt;
    private String searchResponsePrompt;
    private String actionResponsePrompt;

    @PostConstruct
    public void loadPrompts() throws IOException {
        this.systemPrompt = loadResource(systemPromptResource, "system-prompt.txt");
        this.intentDetectionPrompt = loadResource(intentDetectionPromptResource, "intent-detection-prompt.txt");
        this.decompositionPrompt = loadResource(decompositionPromptResource, "decomposition-prompt.txt");
        this.searchResponsePrompt = loadResource(searchResponsePromptResource, "search-response-prompt.txt");
        this.actionResponsePrompt = loadResource(actionResponsePromptResource, "action-response-prompt.txt");
        log.info("Loaded prompts: system ({} chars), intent ({} chars), decomposition ({} chars), search-response ({} chars), action-response ({} chars)",
                systemPrompt.length(), intentDetectionPrompt.length(), decompositionPrompt.length(),
                searchResponsePrompt.length(), actionResponsePrompt.length());
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
