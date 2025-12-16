package com.mindnest.agent;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.mindnest.agent.tools.KnowledgeTools;
import com.mindnest.agent.tools.ProjectTools;
import com.mindnest.agent.tools.TaskTools;
import com.mindnest.agent.tools.TimeTools;
import com.mindnest.model.entity.KnowledgeItem;
import com.mindnest.model.entity.KnowledgeItem.KnowledgeType;
import com.mindnest.model.entity.KnowledgeItem.TaskStatus;
import com.mindnest.model.entity.Project;
import com.mindnest.repository.VectorRepository.SearchResult;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import java.util.stream.Collectors;

/**
 * Executes tool calls from the agent and formats results.
 */
@Component
@RequiredArgsConstructor
@Slf4j
public class ToolExecutor {

    private final KnowledgeTools knowledgeTools;
    private final TaskTools taskTools;
    private final ProjectTools projectTools;
    private final TimeTools timeTools;
    private final ObjectMapper objectMapper;

    // Thread-local storage for sources collected during execution
    private static final ThreadLocal<List<String>> sourcesThreadLocal = ThreadLocal.withInitial(ArrayList::new);

    /**
     * Clear sources before processing a new message
     */
    public void clearSources() {
        sourcesThreadLocal.get().clear();
    }

    /**
     * Get sources collected during execution
     */
    public List<String> getSources() {
        return new ArrayList<>(sourcesThreadLocal.get());
    }

    private void addSource(String source) {
        sourcesThreadLocal.get().add(source);
    }

    /**
     * Execute a tool call and return the result as a string.
     */
    public String execute(String functionName, Map<String, Object> args, String projectId, String userId) {
        log.info("Executing tool: {} with args: {}", functionName, args);

        try {
            return switch (functionName) {
                // Knowledge tools
                case "create_knowledge" -> executeCreateKnowledge(args, projectId, userId);
                case "search_knowledge" -> executeSearchKnowledge(args, projectId);
                case "delete_knowledge" -> executeDeleteKnowledge(args, projectId);
                case "get_knowledge" -> executeGetKnowledge(args);

                // Task tools
                case "create_task" -> executeCreateTask(args, projectId, userId);
                case "get_tasks_for_today" -> executeGetTasksForToday(userId);
                case "get_active_tasks" -> executeGetActiveTasks(userId);
                case "update_task_status" -> executeUpdateTaskStatus(args);
                case "complete_task_by_title" -> executeCompleteTaskByTitle(args, projectId);
                case "search_tasks" -> executeSearchTasks(args, projectId);
                case "decompose_task" -> executeDecomposeTask(args);

                // Project tools
                case "create_project" -> executeCreateProject(args, userId);
                case "list_projects" -> executeListProjects(userId);

                // Time tools
                case "get_current_date" -> executeGetCurrentDate();

                default -> "Unknown function: " + functionName;
            };
        } catch (Exception e) {
            log.error("Tool execution failed: {}", functionName, e);
            return "Error executing " + functionName + ": " + e.getMessage();
        }
    }

    // Knowledge tool implementations

    private String executeCreateKnowledge(Map<String, Object> args, String projectId, String userId) {
        String content = (String) args.get("content");
        String typeStr = (String) args.getOrDefault("type", "NOTE");
        KnowledgeType type = KnowledgeType.valueOf(typeStr.toUpperCase());

        KnowledgeItem item = knowledgeTools.createKnowledge(content, type, projectId, userId);
        return String.format("Created %s: '%s' (id: %s)",
                type.name().toLowerCase(),
                truncate(content, 50),
                item.getId());
    }

    private String executeSearchKnowledge(Map<String, Object> args, String projectId) {
        String query = (String) args.get("query");
        int limit = ((Number) args.getOrDefault("limit", 5)).intValue();

        List<SearchResult> results = knowledgeTools.searchKnowledge(query, projectId, limit);

        if (results.isEmpty()) {
            return "No knowledge found matching: " + query;
        }

        // Track sources for attribution
        for (SearchResult r : results) {
            String content = (String) r.payload().get("content");
            String type = (String) r.payload().get("type");
            addSource(String.format("[%s] %s", type, truncate(content, 100)));
        }

        return results.stream()
                .map(r -> String.format("- [%s] %s (relevance: %.0f%%)",
                        r.payload().get("type"),
                        r.payload().get("content"),
                        r.score() * 100))
                .collect(Collectors.joining("\n"));
    }

    private String executeGetKnowledge(Map<String, Object> args) {
        String id = (String) args.get("id");
        return knowledgeTools.getKnowledge(id)
                .map(item -> String.format("Type: %s\nContent: %s\nCreated: %s",
                        item.getType(), item.getContent(), item.getCreatedAt()))
                .orElse("Knowledge item not found: " + id);
    }

    private String executeDeleteKnowledge(Map<String, Object> args, String projectId) {
        String query = (String) args.get("query");

        int deleted = knowledgeTools.deleteKnowledgeByQuery(query, projectId);

        if (deleted > 0) {
            return String.format("Deleted %d item(s) matching '%s' from the knowledge base", deleted, query);
        } else {
            return "No items found matching '" + query + "' to delete";
        }
    }

    // Task tool implementations

    private String executeCreateTask(Map<String, Object> args, String projectId, String userId) {
        String title = (String) args.get("title");
        String description = (String) args.get("description");
        String deadlineStr = (String) args.get("deadline");

        LocalDate deadline = deadlineStr != null ? timeTools.parseDate(deadlineStr) : null;

        KnowledgeItem task = taskTools.createTask(title, description, deadline, projectId, userId);

        String deadlineInfo = deadline != null
                ? " (deadline: " + timeTools.formatDate(deadline) + ")"
                : "";
        return String.format("Created task: '%s'%s", title, deadlineInfo);
    }

    private String executeGetTasksForToday(String userId) {
        List<KnowledgeItem> tasks = taskTools.getTasksForToday(userId);

        if (tasks.isEmpty()) {
            return "No tasks for today.";
        }

        return "Tasks for today:\n" + tasks.stream()
                .map(t -> String.format("- [%s] %s", t.getStatus(), getTaskTitle(t)))
                .collect(Collectors.joining("\n"));
    }

    private String executeGetActiveTasks(String userId) {
        List<KnowledgeItem> tasks = taskTools.getActiveTasks(userId);

        if (tasks.isEmpty()) {
            return "No active tasks.";
        }

        return "Active tasks:\n" + tasks.stream()
                .map(t -> {
                    String deadline = t.getDeadline() != null
                            ? " (due: " + timeTools.formatDate(t.getDeadline()) + ")"
                            : "";
                    return String.format("- [%s] %s%s", t.getStatus(), getTaskTitle(t), deadline);
                })
                .collect(Collectors.joining("\n"));
    }

    private String executeUpdateTaskStatus(Map<String, Object> args) {
        String taskId = (String) args.get("task_id");
        String statusStr = (String) args.get("status");
        TaskStatus status = TaskStatus.valueOf(statusStr.toUpperCase());

        return taskTools.updateTaskStatus(taskId, status)
                .map(t -> String.format("Updated task '%s' to %s", getTaskTitle(t), status))
                .orElse("Task not found: " + taskId);
    }

    private String executeCompleteTaskByTitle(Map<String, Object> args, String projectId) {
        String title = (String) args.get("title");

        return taskTools.completeTaskByTitle(title, projectId)
                .map(t -> String.format("Marked task '%s' as completed", getTaskTitle(t)))
                .orElse("No matching task found for: " + title + ". Please check the task title.");
    }

    private String executeSearchTasks(Map<String, Object> args, String projectId) {
        String query = (String) args.get("query");
        int limit = ((Number) args.getOrDefault("limit", 5)).intValue();

        List<SearchResult> results = taskTools.searchTasks(query, projectId, limit);

        if (results.isEmpty()) {
            return "No tasks found matching: " + query;
        }

        // Track sources for attribution
        for (SearchResult r : results) {
            String content = (String) r.payload().get("content");
            addSource(String.format("[TASK] %s", truncate(content, 100)));
        }

        return results.stream()
                .map(r -> String.format("- %s (relevance: %.0f%%)",
                        r.payload().get("content"),
                        r.score() * 100))
                .collect(Collectors.joining("\n"));
    }

    @SuppressWarnings("unchecked")
    private String executeDecomposeTask(Map<String, Object> args) {
        String taskId = (String) args.get("task_id");
        List<String> subtasks = (List<String>) args.get("subtasks");

        if (subtasks == null || subtasks.isEmpty()) {
            return "No subtasks provided to decompose the task.";
        }

        List<KnowledgeItem> created = taskTools.decomposeTask(taskId, subtasks);

        if (created.isEmpty()) {
            return "Failed to decompose task. Task not found: " + taskId;
        }

        return String.format("Created %d subtasks:\n%s",
                created.size(),
                created.stream()
                        .map(t -> "- " + getTaskTitle(t))
                        .collect(Collectors.joining("\n")));
    }

    // Project tool implementations

    private String executeCreateProject(Map<String, Object> args, String userId) {
        String name = (String) args.get("name");
        String description = (String) args.get("description");

        Project project = projectTools.createProject(name, description, UUID.fromString(userId));
        return String.format("Created project: '%s' (id: %s)", project.getName(), project.getId());
    }

    private String executeListProjects(String userId) {
        List<Project> projects = projectTools.getProjects(UUID.fromString(userId));

        if (projects.isEmpty()) {
            return "No projects found. Create one with: create a project named 'My Project'";
        }

        return "Your projects:\n" + projects.stream()
                .map(p -> String.format("- %s: %s", p.getName(),
                        p.getDescription() != null ? p.getDescription() : "(no description)"))
                .collect(Collectors.joining("\n"));
    }

    // Time tool implementations

    private String executeGetCurrentDate() {
        Map<String, Object> info = timeTools.getCurrentDateTimeInfo();
        return String.format("Today is %s (%s)", info.get("formatted"), info.get("dayOfWeek"));
    }

    // Helpers

    private String getTaskTitle(KnowledgeItem task) {
        String content = task.getContent();
        int newlineIdx = content.indexOf('\n');
        return newlineIdx > 0 ? content.substring(0, newlineIdx) : truncate(content, 50);
    }

    private String truncate(String text, int maxLen) {
        return text.length() > maxLen ? text.substring(0, maxLen) + "..." : text;
    }
}
