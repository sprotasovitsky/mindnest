package com.mindnest.controller;

import com.mindnest.agent.tools.ProjectTools;
import com.mindnest.model.dto.ProjectRequest;
import com.mindnest.model.dto.ProjectResponse;
import com.mindnest.model.entity.Project;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.net.URI;
import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/projects")
@RequiredArgsConstructor
@Slf4j
public class ProjectController {

    private final ProjectTools projectTools;

    // Default user for MVP (before auth is implemented)
    private static final UUID DEFAULT_USER_ID = UUID.fromString("00000000-0000-0000-0000-000000000001");

    @GetMapping
    public ResponseEntity<List<ProjectResponse>> listProjects(
            @RequestHeader(value = "X-User-Id", required = false) String userIdHeader) {

        UUID userId = parseUserId(userIdHeader);
        log.info("Listing projects for user: {}", userId);

        List<ProjectResponse> projects = projectTools.getProjects(userId).stream()
                .map(ProjectResponse::from)
                .toList();

        return ResponseEntity.ok(projects);
    }

    @GetMapping("/{id}")
    public ResponseEntity<ProjectResponse> getProject(@PathVariable UUID id) {
        log.info("Getting project: {}", id);

        return projectTools.getProject(id)
                .map(ProjectResponse::from)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    @PostMapping
    public ResponseEntity<ProjectResponse> createProject(
            @Valid @RequestBody ProjectRequest request,
            @RequestHeader(value = "X-User-Id", required = false) String userIdHeader) {

        UUID userId = parseUserId(userIdHeader);
        log.info("Creating project '{}' for user: {}", request.getName(), userId);

        Project project = projectTools.createProject(
                request.getName(),
                request.getDescription(),
                userId
        );

        ProjectResponse response = ProjectResponse.from(project);
        return ResponseEntity
                .created(URI.create("/api/projects/" + project.getId()))
                .body(response);
    }

    @PutMapping("/{id}")
    public ResponseEntity<ProjectResponse> updateProject(
            @PathVariable UUID id,
            @Valid @RequestBody ProjectRequest request) {

        log.info("Updating project: {}", id);

        return projectTools.updateProject(id, request.getName(), request.getDescription())
                .map(ProjectResponse::from)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteProject(@PathVariable UUID id) {
        log.info("Deleting project: {}", id);

        if (projectTools.deleteProject(id)) {
            return ResponseEntity.noContent().build();
        }
        return ResponseEntity.notFound().build();
    }

    private UUID parseUserId(String userIdHeader) {
        if (userIdHeader != null && !userIdHeader.isBlank()) {
            try {
                return UUID.fromString(userIdHeader);
            } catch (IllegalArgumentException e) {
                log.warn("Invalid user ID header: {}", userIdHeader);
            }
        }
        return DEFAULT_USER_ID;
    }
}
