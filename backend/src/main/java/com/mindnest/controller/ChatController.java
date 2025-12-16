package com.mindnest.controller;

import com.mindnest.agent.AgentService;
import com.mindnest.agent.tools.ProjectTools;
import com.mindnest.model.dto.ChatRequest;
import com.mindnest.model.dto.ChatResponse;
import com.mindnest.security.SecurityUtils;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
@Slf4j
public class ChatController {

    private final AgentService agentService;
    private final ProjectTools projectTools;

    @PostMapping("/chat")
    public ResponseEntity<ChatResponse> chat(@Valid @RequestBody ChatRequest request) {
        UUID userId = SecurityUtils.getCurrentUserId();
        log.info("Chat request from user {}: {}", userId, request.getMessage());

        // Verify project access if projectId is provided
        if (request.getProjectId() != null) {
            try {
                UUID projectId = UUID.fromString(request.getProjectId());
                if (!projectTools.hasAccess(projectId, userId)) {
                    log.warn("User {} does not have access to project {}", userId, projectId);
                    return ResponseEntity.status(403).body(
                            ChatResponse.builder()
                                    .reply("You don't have access to this project.")
                                    .confidence(1.0)
                                    .build()
                    );
                }
            } catch (IllegalArgumentException e) {
                log.warn("Invalid project ID: {}", request.getProjectId());
            }
        }

        ChatResponse response = agentService.processMessage(
                request.getMessage(),
                request.getProjectId(),
                userId.toString()
        );

        return ResponseEntity.ok(response);
    }

    @GetMapping("/health")
    public ResponseEntity<String> health() {
        return ResponseEntity.ok("OK");
    }
}
