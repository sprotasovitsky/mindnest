package com.mindnest.agent.tools;

import com.mindnest.model.entity.Project;
import com.mindnest.model.entity.ProjectMember;
import com.mindnest.model.entity.ProjectMember.ProjectRole;
import com.mindnest.repository.ProjectMemberRepository;
import com.mindnest.repository.ProjectRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

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
    private final ProjectMemberRepository projectMemberRepository;

    /**
     * Create a new project and add owner as member
     */
    @Transactional
    public Project createProject(String name, String description, UUID ownerId) {
        log.info("Creating project: '{}' for owner: {}", name, ownerId);

        Project project = Project.builder()
                .name(name)
                .description(description)
                .ownerId(ownerId)
                .build();

        Project saved = projectRepository.save(project);

        // Add owner as OWNER member
        ProjectMember ownerMember = ProjectMember.builder()
                .projectId(saved.getId())
                .userId(ownerId)
                .role(ProjectRole.OWNER)
                .build();
        projectMemberRepository.save(ownerMember);

        log.info("Created project: {} ({}) with owner membership", saved.getName(), saved.getId());
        return saved;
    }

    /**
     * Get all projects where user is a member (owner or member)
     */
    public List<Project> getProjects(UUID userId) {
        return projectRepository.findProjectsByMembership(userId);
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
     * Delete project and all members
     */
    @Transactional
    public boolean deleteProject(UUID projectId) {
        if (projectRepository.existsById(projectId)) {
            projectMemberRepository.deleteByProjectId(projectId);
            projectRepository.deleteById(projectId);
            log.info("Deleted project: {} and all members", projectId);
            return true;
        }
        return false;
    }

    /**
     * Add a member to a project
     */
    @Transactional
    public Optional<ProjectMember> addMember(UUID projectId, UUID userId, ProjectRole role) {
        // Check if project exists
        if (!projectRepository.existsById(projectId)) {
            log.warn("Cannot add member: project {} not found", projectId);
            return Optional.empty();
        }

        // Check if already a member
        if (projectMemberRepository.existsByProjectIdAndUserId(projectId, userId)) {
            log.info("User {} is already a member of project {}", userId, projectId);
            return projectMemberRepository.findByProjectIdAndUserId(projectId, userId);
        }

        ProjectMember member = ProjectMember.builder()
                .projectId(projectId)
                .userId(userId)
                .role(role)
                .build();

        ProjectMember saved = projectMemberRepository.save(member);
        log.info("Added user {} as {} to project {}", userId, role, projectId);
        return Optional.of(saved);
    }

    /**
     * Add a member by email
     */
    public Optional<ProjectMember> addMemberByEmail(UUID projectId, String email) {
        // This would need UserRepository to look up by email
        // For now, we'll use the direct userId method
        log.warn("addMemberByEmail not fully implemented - use addMember with userId");
        return Optional.empty();
    }

    /**
     * Remove a member from project
     */
    @Transactional
    public boolean removeMember(UUID projectId, UUID userId) {
        Optional<ProjectMember> member = projectMemberRepository.findByProjectIdAndUserId(projectId, userId);
        if (member.isPresent()) {
            // Cannot remove OWNER
            if (member.get().getRole() == ProjectRole.OWNER) {
                log.warn("Cannot remove owner from project {}", projectId);
                return false;
            }
            projectMemberRepository.deleteByProjectIdAndUserId(projectId, userId);
            log.info("Removed user {} from project {}", userId, projectId);
            return true;
        }
        return false;
    }

    /**
     * Get all members of a project
     */
    public List<ProjectMember> getMembers(UUID projectId) {
        return projectMemberRepository.findByProjectId(projectId);
    }

    /**
     * Check if user has access to project
     */
    public boolean hasAccess(UUID projectId, UUID userId) {
        return projectMemberRepository.existsByProjectIdAndUserId(projectId, userId);
    }

    /**
     * Check if user is owner of project
     */
    public boolean isOwner(UUID projectId, UUID userId) {
        return projectMemberRepository.findByProjectIdAndUserId(projectId, userId)
                .map(m -> m.getRole() == ProjectRole.OWNER)
                .orElse(false);
    }

    /**
     * Get member info
     */
    public Optional<ProjectMember> getMember(UUID projectId, UUID userId) {
        return projectMemberRepository.findByProjectIdAndUserId(projectId, userId);
    }
}
