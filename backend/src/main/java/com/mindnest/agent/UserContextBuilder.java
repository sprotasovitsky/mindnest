package com.mindnest.agent;

import com.mindnest.agent.tools.ProjectTools;
import com.mindnest.model.entity.Message;
import com.mindnest.model.entity.ProjectMember;
import com.mindnest.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.*;

/**
 * Builds user context for LLM responses and handles context extraction.
 * Manages user information, project members, and pending clarifications.
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class UserContextBuilder {

    private final UserRepository userRepository;
    private final ProjectTools projectTools;

    /**
     * Build user context string for LLM: current user + all project members.
     */
    public String buildUserContext(String userId, String projectId) {
        StringBuilder context = new StringBuilder();

        try {
            // Get current user name
            String currentUserName = getUserName(userId);
            context.append("Current user: ").append(currentUserName).append("\n");

            // Get all project members with their names
            if (projectId != null) {
                List<ProjectMember> members = projectTools.getMembers(UUID.fromString(projectId));
                if (!members.isEmpty()) {
                    context.append("Project members: ");
                    List<String> memberNames = new ArrayList<>();
                    for (ProjectMember member : members) {
                        var memberUser = userRepository.findById(member.getUserId());
                        if (memberUser.isPresent()) {
                            String name = memberUser.get().getName();
                            String role = member.getRole().name().toLowerCase();
                            memberNames.add(name + " (" + role + ")");
                        }
                    }
                    context.append(String.join(", ", memberNames));
                }
            }
        } catch (Exception e) {
            log.warn("Failed to build user context: {}", e.getMessage());
        }

        return context.toString();
    }

    /**
     * Build a map of userId -> userName for all project members.
     * Used to show who added each item in the knowledge graph.
     */
    public Map<String, String> buildUserIdToNameMap(String projectId) {
        Map<String, String> userIdToName = new HashMap<>();
        try {
            if (projectId != null) {
                List<ProjectMember> members = projectTools.getMembers(UUID.fromString(projectId));
                for (ProjectMember member : members) {
                    var memberUser = userRepository.findById(member.getUserId());
                    if (memberUser.isPresent()) {
                        userIdToName.put(member.getUserId().toString(), memberUser.get().getName());
                    }
                }
            }
        } catch (Exception e) {
            log.warn("Failed to build userId to name map: {}", e.getMessage());
        }
        return userIdToName;
    }

    /**
     * Get user name from userId.
     */
    public String getUserName(String userId) {
        if (userId == null) return "Unknown";
        try {
            return userRepository.findById(UUID.fromString(userId))
                    .map(u -> u.getName())
                    .orElse("Unknown");
        } catch (Exception e) {
            log.warn("Failed to get user name: {}", e.getMessage());
            return "Unknown";
        }
    }

    /**
     * Extract pending task IDs from the last assistant message's metadata.
     * Used for handling user's response to task clarification.
     */
    @SuppressWarnings("unchecked")
    public List<String> getPendingTaskIdsFromContext(List<Message> context) {
        log.debug("Looking for pendingTaskIds in {} context messages", context.size());
        // Find the most recent assistant message with clarification metadata
        for (Message msg : context) {
            log.debug("Message role={}, hasMetadata={}, metadata={}",
                    msg.getRole(), msg.getMetadata() != null,
                    msg.getMetadata() != null ? msg.getMetadata().keySet() : "null");
            if (msg.getRole() == Message.Role.assistant && msg.getMetadata() != null) {
                Object pendingIds = msg.getMetadata().get("pendingTaskIds");
                log.debug("Found pendingIds: {}, type: {}", pendingIds,
                        pendingIds != null ? pendingIds.getClass().getName() : "null");
                if (pendingIds instanceof List) {
                    List<String> ids = (List<String>) pendingIds;
                    log.info("Extracted {} pending task IDs from context", ids.size());
                    return ids;
                }
            }
        }
        log.debug("No pendingTaskIds found in context");
        return List.of();
    }

    /**
     * Extract pending task IDs from clarification results.
     */
    public List<String> extractPendingTaskIds(List<ChunkResult> results) {
        for (ChunkResult result : results) {
            if (result.needsClarification() && result.pendingTaskIds() != null && !result.pendingTaskIds().isEmpty()) {
                return result.pendingTaskIds();
            }
        }
        return List.of();
    }

    /**
     * Safely extract a list of integers from an object (handles JSON parsing quirks).
     */
    public List<Integer> extractIntegerList(Object obj) {
        if (obj == null) return List.of();
        if (obj instanceof List) {
            List<?> list = (List<?>) obj;
            return list.stream()
                    .map(item -> {
                        if (item instanceof Number) return ((Number) item).intValue();
                        if (item instanceof String) {
                            try {
                                return Integer.parseInt((String) item);
                            } catch (NumberFormatException e) {
                                return null;
                            }
                        }
                        return null;
                    })
                    .filter(i -> i != null)
                    .toList();
        }
        return List.of();
    }

    /**
     * Safely extract a list of strings from an object.
     */
    public List<String> extractStringList(Object obj) {
        if (obj == null) return List.of();
        if (obj instanceof List) {
            List<?> list = (List<?>) obj;
            return list.stream()
                    .map(item -> item != null ? item.toString() : null)
                    .filter(s -> s != null)
                    .toList();
        }
        return List.of();
    }
}
