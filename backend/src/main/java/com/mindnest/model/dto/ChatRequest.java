package com.mindnest.model.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class ChatRequest {
    @NotBlank
    private String message;
    private String projectId;
    private String userId;  // Optional for MVP, will use default if not provided
}
