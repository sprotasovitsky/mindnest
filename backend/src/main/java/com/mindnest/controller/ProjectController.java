package com.mindnest.controller;

import com.mindnest.agent.tools.ProjectTools;
import com.mindnest.model.dto.AddMemberRequest;
import com.mindnest.model.dto.MemberResponse;
import com.mindnest.model.dto.ProjectRequest;
import com.mindnest.model.dto.ProjectResponse;
import com.mindnest.model.entity.Project;
import com.mindnest.model.entity.ProjectMember;
import com.mindnest.model.entity.ProjectMember.ProjectRole;
import com.mindnest.model.entity.User;
import com.mindnest.repository.UserRepository;
import com.mindnest.security.SecurityUtils;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.net.URI;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/projects")
@RequiredArgsConstructor
@Slf4j
public class ProjectController {

    private final ProjectTools projectTools;
    private final UserRepository userRepository;

    @GetMapping
    public ResponseEntity<List<ProjectResponse>> listProjects() {
        UUID userId = SecurityUtils.getCurrentUserId();
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
    public ResponseEntity<ProjectResponse> createProject(@Valid @RequestBody ProjectRequest request) {
        UUID userId = SecurityUtils.getCurrentUserId();
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
        UUID userId = SecurityUtils.getCurrentUserId();
        log.info("Deleting project: {}", id);

        // Only owner can delete
        if (!projectTools.isOwner(id, userId)) {
            return ResponseEntity.status(403).build();
        }

        if (projectTools.deleteProject(id)) {
            return ResponseEntity.noContent().build();
        }
        return ResponseEntity.notFound().build();
    }

    // ========== Member Management ==========

    @GetMapping("/{id}/members")
    public ResponseEntity<List<MemberResponse>> getMembers(@PathVariable UUID id) {
        UUID userId = SecurityUtils.getCurrentUserId();
        log.info("Getting members for project: {}", id);

        // Check access
        if (!projectTools.hasAccess(id, userId)) {
            return ResponseEntity.status(403).build();
        }

        List<ProjectMember> members = projectTools.getMembers(id);

        // Get user info for all members
        List<UUID> userIds = members.stream()
                .map(ProjectMember::getUserId)
                .toList();
        Map<UUID, User> usersMap = userRepository.findAllById(userIds).stream()
                .collect(Collectors.toMap(User::getId, u -> u));

        List<MemberResponse> responses = members.stream()
                .map(m -> MemberResponse.from(m, usersMap.get(m.getUserId())))
                .toList();

        return ResponseEntity.ok(responses);
    }

    @PostMapping("/{id}/members")
    public ResponseEntity<?> addMember(
            @PathVariable UUID id,
            @Valid @RequestBody AddMemberRequest request) {
        UUID userId = SecurityUtils.getCurrentUserId();
        log.info("Adding member {} to project: {}", request.getEmail(), id);

        // Check if current user has access (only members can add members)
        if (!projectTools.hasAccess(id, userId)) {
            return ResponseEntity.status(403).build();
        }

        // Find user by email
        return userRepository.findByEmail(request.getEmail())
                .map(user -> {
                    return projectTools.addMember(id, user.getId(), ProjectRole.MEMBER)
                            .map(member -> {
                                MemberResponse response = MemberResponse.from(member, user);
                                return ResponseEntity.created(
                                        URI.create("/api/projects/" + id + "/members/" + member.getId())
                                ).body((Object) response);
                            })
                            .orElse(ResponseEntity.badRequest().body(
                                    Map.of("error", "Failed to add member")
                            ));
                })
                .orElse(ResponseEntity.badRequest().body(
                        Map.of("error", "User not found with email: " + request.getEmail())
                ));
    }

    @DeleteMapping("/{id}/members/{memberId}")
    public ResponseEntity<?> removeMember(
            @PathVariable UUID id,
            @PathVariable UUID memberId) {
        UUID userId = SecurityUtils.getCurrentUserId();
        log.info("Removing member {} from project: {}", memberId, id);

        // Only owner can remove members
        if (!projectTools.isOwner(id, userId)) {
            return ResponseEntity.status(403).body(
                    Map.of("error", "Only project owner can remove members")
            );
        }

        if (projectTools.removeMember(id, memberId)) {
            return ResponseEntity.noContent().build();
        }
        return ResponseEntity.notFound().build();
    }
}
