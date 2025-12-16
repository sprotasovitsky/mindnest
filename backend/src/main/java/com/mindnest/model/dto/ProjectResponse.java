package com.mindnest.model.dto;

import com.mindnest.model.entity.Project;
import lombok.Builder;
import lombok.Data;

import java.time.Instant;
import java.util.UUID;

@Data
@Builder
public class ProjectResponse {
    private UUID id;
    private String name;
    private String description;
    private Instant createdAt;
    private Instant updatedAt;

    public static ProjectResponse from(Project project) {
        return ProjectResponse.builder()
                .id(project.getId())
                .name(project.getName())
                .description(project.getDescription())
                .createdAt(project.getCreatedAt())
                .updatedAt(project.getUpdatedAt())
                .build();
    }
}
