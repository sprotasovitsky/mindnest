package com.mindnest.agent.tools;

import com.mindnest.model.entity.Project;
import com.mindnest.repository.ProjectRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

/**
 * Tools for managing projects.
 */
@Component
@RequiredArgsConstructor
@Slf4j
public class ProjectTools {

    private final ProjectRepository projectRepository;

    /**
     * Create a new project
     */
    public Project createProject(String name, String description, UUID ownerId) {
        log.info("Creating project: '{}' for owner: {}", name, ownerId);

        Project project = Project.builder()
                .name(name)
                .description(description)
                .ownerId(ownerId)
                .build();

        Project saved = projectRepository.save(project);
        log.info("Created project: {} ({})", saved.getName(), saved.getId());
        return saved;
    }

    /**
     * Get all projects for a user
     */
    public List<Project> getProjects(UUID ownerId) {
        return projectRepository.findByOwnerId(ownerId);
    }

    /**
     * Get project by ID
     */
    public Optional<Project> getProject(UUID projectId) {
        return projectRepository.findById(projectId);
    }

    /**
     * Update project
     */
    public Optional<Project> updateProject(UUID projectId, String name, String description) {
        return projectRepository.findById(projectId)
                .map(project -> {
                    if (name != null && !name.isBlank()) {
                        project.setName(name);
                    }
                    if (description != null) {
                        project.setDescription(description);
                    }
                    Project updated = projectRepository.save(project);
                    log.info("Updated project: {}", projectId);
                    return updated;
                });
    }

    /**
     * Delete project
     */
    public boolean deleteProject(UUID projectId) {
        if (projectRepository.existsById(projectId)) {
            projectRepository.deleteById(projectId);
            log.info("Deleted project: {}", projectId);
            return true;
        }
        return false;
    }
}
