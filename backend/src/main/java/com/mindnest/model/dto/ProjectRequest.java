package com.mindnest.model.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class ProjectRequest {
    @NotBlank
    private String name;
    private String description;
}
