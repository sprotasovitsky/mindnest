package com.mindnest.model.dto;

import lombok.Builder;
import lombok.Data;

import java.util.List;

@Data
@Builder
public class ChatResponse {
    private String reply;
    private List<String> sources;
    private Double confidence;
}
