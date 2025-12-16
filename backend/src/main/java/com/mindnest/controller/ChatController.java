package com.mindnest.controller;

import com.mindnest.agent.AgentService;
import com.mindnest.model.dto.ChatRequest;
import com.mindnest.model.dto.ChatResponse;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
@Slf4j
public class ChatController {

    private final AgentService agentService;

    // Default user and project for MVP (before auth is implemented)
    private static final String DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000001";
    private static final String DEFAULT_PROJECT_ID = "00000000-0000-0000-0000-000000000001";

    @PostMapping("/chat")
    public ResponseEntity<ChatResponse> chat(@Valid @RequestBody ChatRequest request) {
        log.info("Received chat request: {}", request.getMessage());

        String userId = request.getUserId() != null ? request.getUserId() : DEFAULT_USER_ID;
        String projectId = request.getProjectId() != null ? request.getProjectId() : DEFAULT_PROJECT_ID;

        ChatResponse response = agentService.processMessage(
                request.getMessage(),
                projectId,
                userId
        );

        return ResponseEntity.ok(response);
    }

    @GetMapping("/health")
    public ResponseEntity<String> health() {
        return ResponseEntity.ok("OK");
    }
}
