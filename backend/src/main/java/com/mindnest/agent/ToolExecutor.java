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
import com.mindnest.model.entity.KnowledgeRelation.RelationType;
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
    // Thread-local storage for IDs from last search (for graph expansion)
    private static final ThreadLocal<List<String>> lastSearchIdsThreadLocal = ThreadLocal.withInitial(ArrayList::new);

    /**
     * Clear sources before processing a new message
     */
    public void clearSources() {
        sourcesThreadLocal.get().clear();
        lastSearchIdsThreadLocal.get().clear();
    }

    /**
     * Get sources collected during execution
     */
    public List<String> getSources() {
        return new ArrayList<>(sourcesThreadLocal.get());
    }

    /**
     * Get IDs from last search (for graph expansion)
     */
    public List<String> getLastSearchIds() {
        return new ArrayList<>(lastSearchIdsThreadLocal.get());
    }

    private void addSource(String source) {
        sourcesThreadLocal.get().add(source);
    }

    private void setLastSearchIds(List<String> ids) {
        lastSearchIdsThreadLocal.get().clear();
        lastSearchIdsThreadLocal.get().addAll(ids);
    }

    /**
     * Execute a tool call and return the result as a string.
     */
    public String execute(String functionName, Map<String, Object> args, String projectId, String userId) {
        log.info("Executing tool: {} with args: {}", functionName, args);

        try {
            return switch (functionName) {
                // Knowledge tools (immutable: no update, no delete)
                case "create_knowledge" -> executeCreateKnowledge(args, projectId, userId);
                case "search_knowledge" -> executeSearchKnowledge(args, projectId);
                case "get_knowledge" -> executeGetKnowledge(args);

                // Task tools
                case "create_task" -> executeCreateTask(args, projectId, userId);
                case "get_tasks_for_today" -> executeGetTasksForToday(userId);
                case "get_active_tasks" -> executeGetActiveTasks(userId);
                case "update_task_status" -> executeUpdateTaskStatus(args);
                case "complete_task_by_title" -> executeCompleteTaskByTitle(args, projectId);
                case "complete_all_tasks_by_assignee" -> executeCompleteAllTasksByAssignee(args, projectId);
                case "complete_tasks_by_ids" -> executeCompleteTasksByIds(args);
                case "search_tasks" -> executeSearchTasks(args, projectId);
                case "get_my_items" -> executeGetMyItems(args, projectId, userId);
                case "decompose_task" -> executeDecomposeTask(args);

                // Project tools
                case "create_project" -> executeCreateProject(args, userId);
                case "list_projects" -> executeListProjects(userId);

                // Time tools
                case "get_current_date" -> executeGetCurrentDate();

                // Graph relation tools
                case "create_relation" -> executeCreateRelation(args, projectId);
                case "create_relation_by_id" -> executeCreateRelationById(args);
                case "get_related" -> executeGetRelated(args, projectId);
                case "find_path" -> executeFindPath(args, projectId);

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

        // Extract optional properties
        java.math.BigDecimal amount = null;
        Object amountObj = args.get("amount");
        if (amountObj != null) {
            if (amountObj instanceof Number) {
                amount = java.math.BigDecimal.valueOf(((Number) amountObj).doubleValue());
            } else if (amountObj instanceof String) {
                try {
                    amount = new java.math.BigDecimal((String) amountObj);
                } catch (NumberFormatException e) {
                    log.warn("Invalid amount format: {}", amountObj);
                }
            }
        }

        String currency = (String) args.get("currency");
        String assignee = (String) args.get("assignee");

        KnowledgeItem item = knowledgeTools.createKnowledge(content, type, projectId, userId, amount, currency, assignee);
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
            setLastSearchIds(List.of());
            return "No knowledge found matching: " + query;
        }

        // Save IDs for graph expansion
        setLastSearchIds(results.stream().map(SearchResult::id).toList());

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

    // NOTE: No update/delete methods - system is immutable
    // All changes create NEW items with relations (SUPERSEDES, CONTRADICTS) via AgentService

    // Task tool implementations

    private String executeCreateTask(Map<String, Object> args, String projectId, String userId) {
        String title = (String) args.get("title");
        String description = (String) args.get("description");
        String deadlineStr = (String) args.get("deadline");
        String assignee = (String) args.get("assignee");

        LocalDate deadline = deadlineStr != null ? timeTools.parseDate(deadlineStr) : null;

        // Include assignee in task content for searchability, but also save to separate field
        String taskTitle = title;
        if (assignee != null && !assignee.isBlank()) {
            taskTitle = title + " [assigned to: " + assignee + "]";
        }

        KnowledgeItem task = taskTools.createTask(taskTitle, description, deadline, projectId, userId, assignee);

        String deadlineInfo = deadline != null
                ? " (deadline: " + timeTools.formatDate(deadline) + ")"
                : "";
        String assigneeInfo = assignee != null && !assignee.isBlank()
                ? " (assigned to: " + assignee + ")"
                : "";
        return String.format("Created task: '%s'%s%s", title, assigneeInfo, deadlineInfo);
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

    private String executeGetActiveTasksByProject(String projectId) {
        // Get both TODO and IN_PROGRESS tasks for the project
        List<KnowledgeItem> todoTasks = taskTools.getTasksByStatus(projectId, TaskStatus.TODO);
        List<KnowledgeItem> inProgressTasks = taskTools.getTasksByStatus(projectId, TaskStatus.IN_PROGRESS);

        List<KnowledgeItem> tasks = new ArrayList<>();
        tasks.addAll(todoTasks);
        tasks.addAll(inProgressTasks);

        if (tasks.isEmpty()) {
            return "No active tasks in this project.";
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

    private String executeCompleteAllTasksByAssignee(Map<String, Object> args, String projectId) {
        String assignee = (String) args.get("assignee");

        List<KnowledgeItem> completed = taskTools.completeAllTasksByAssignee(assignee, projectId);

        if (completed.isEmpty()) {
            return "No active tasks found for: " + assignee;
        }

        StringBuilder result = new StringBuilder();
        result.append(String.format("Completed %d tasks for %s:\n", completed.size(), assignee));
        for (KnowledgeItem task : completed) {
            result.append("- ").append(getTaskTitle(task)).append("\n");
        }
        return result.toString().trim();
    }

    @SuppressWarnings("unchecked")
    private String executeCompleteTasksByIds(Map<String, Object> args) {
        List<String> taskIds = (List<String>) args.get("task_ids");

        if (taskIds == null || taskIds.isEmpty()) {
            return "No task IDs provided";
        }

        List<KnowledgeItem> completed = taskTools.completeTasksByIds(taskIds);

        if (completed.isEmpty()) {
            return "No tasks found with the provided IDs";
        }

        StringBuilder result = new StringBuilder();
        result.append(String.format("Completed %d tasks:\n", completed.size()));
        for (KnowledgeItem task : completed) {
            result.append("- ").append(getTaskTitle(task)).append("\n");
        }
        return result.toString().trim();
    }

    private String executeGetMyItems(Map<String, Object> args, String projectId, String userId) {
        if (userId == null) {
            return "Cannot get your items: user not identified";
        }

        List<KnowledgeItem> items = knowledgeTools.getItemsByOwner(projectId, userId);

        if (items.isEmpty()) {
            return "You haven't added any items yet.";
        }

        StringBuilder result = new StringBuilder();
        result.append(String.format("Your items (%d):\n", items.size()));
        for (KnowledgeItem item : items) {
            String type = item.getType() != null ? item.getType().name() : "UNKNOWN";
            result.append(String.format("- [%s] %s\n", type, truncate(item.getContent(), 60)));
        }
        return result.toString().trim();
    }

    private String executeSearchTasks(Map<String, Object> args, String projectId) {
        String query = (String) args.get("query");
        int limit = ((Number) args.getOrDefault("limit", 5)).intValue();

        // Handle empty/null query - return all active tasks
        if (query == null || query.isBlank()) {
            return executeGetActiveTasksByProject(projectId);
        }

        List<SearchResult> results = taskTools.searchTasks(query, projectId, limit);

        if (results.isEmpty()) {
            setLastSearchIds(List.of());
            return "No tasks found matching: " + query;
        }

        // Save IDs for graph expansion
        setLastSearchIds(results.stream().map(SearchResult::id).toList());

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

    // Graph relation tool implementations

    private String executeCreateRelation(Map<String, Object> args, String projectId) {
        String sourceQuery = (String) args.get("source_query");
        String targetQuery = (String) args.get("target_query");
        String relationTypeStr = (String) args.get("relation_type");
        String description = (String) args.get("description");

        // Find source item
        List<SearchResult> sourceResults = knowledgeTools.searchKnowledge(sourceQuery, projectId, 1);
        if (sourceResults.isEmpty()) {
            return "Cannot create relation: source item not found for query '" + sourceQuery + "'";
        }
        String sourceId = sourceResults.get(0).id();
        String sourceContent = (String) sourceResults.get(0).payload().get("content");

        // Find target item
        List<SearchResult> targetResults = knowledgeTools.searchKnowledge(targetQuery, projectId, 1);
        if (targetResults.isEmpty()) {
            return "Cannot create relation: target item not found for query '" + targetQuery + "'";
        }
        String targetId = targetResults.get(0).id();
        String targetContent = (String) targetResults.get(0).payload().get("content");

        // Check for self-reference
        if (sourceId.equals(targetId)) {
            return "Cannot create relation: both queries found the same item. Please use more specific queries.";
        }

        // Parse relation type
        RelationType relationType;
        try {
            relationType = RelationType.valueOf(relationTypeStr.toUpperCase());
        } catch (IllegalArgumentException e) {
            return "Invalid relation type: " + relationTypeStr + ". Valid types: SUPERSEDES, CONTRADICTS, BELONGS_TO, ASSIGNED_TO, DEPENDS_ON, RELATES_TO, SUPPORTS, SIMILAR_TO";
        }

        // Create relation
        return knowledgeTools.createRelation(sourceId, targetId, relationType, description)
                .map(item -> String.format("Created relation: '%s' -[%s]-> '%s'",
                        truncate(sourceContent, 30), relationType, truncate(targetContent, 30)))
                .orElse("Failed to create relation between the items");
    }

    /**
     * Create relation directly by IDs (used when we already have the IDs)
     */
    private String executeCreateRelationById(Map<String, Object> args) {
        String sourceId = (String) args.get("source_id");
        String targetId = (String) args.get("target_id");
        String relationTypeStr = (String) args.get("relation_type");
        String description = (String) args.get("description");

        if (sourceId == null || targetId == null) {
            return "Cannot create relation: source_id and target_id are required";
        }

        // Parse relation type
        RelationType relationType;
        try {
            relationType = RelationType.valueOf(relationTypeStr.toUpperCase());
        } catch (IllegalArgumentException e) {
            return "Invalid relation type: " + relationTypeStr;
        }

        // Create relation
        return knowledgeTools.createRelation(sourceId, targetId, relationType, description)
                .map(item -> String.format("Created relation: %s -[%s]-> %s", sourceId, relationType, targetId))
                .orElse("Failed to create relation between the items");
    }

    private String executeGetRelated(Map<String, Object> args, String projectId) {
        String query = (String) args.get("query");
        int depth = ((Number) args.getOrDefault("depth", 1)).intValue();
        depth = Math.max(1, Math.min(3, depth)); // Clamp between 1 and 3

        // Find the item
        List<SearchResult> results = knowledgeTools.searchKnowledge(query, projectId, 1);
        if (results.isEmpty()) {
            return "Item not found for query: '" + query + "'";
        }
        String itemId = results.get(0).id();
        String itemContent = (String) results.get(0).payload().get("content");

        // Get related items
        List<KnowledgeItem> related = knowledgeTools.getRelatedWithinDepth(itemId, depth);

        if (related.isEmpty()) {
            return "No related items found for '" + truncate(itemContent, 40) + "'";
        }

        // Build result
        StringBuilder result = new StringBuilder();
        result.append(String.format("Items related to '%s' (depth %d):\n", truncate(itemContent, 40), depth));

        for (KnowledgeItem item : related) {
            result.append(String.format("- [%s] %s\n", item.getType(), truncate(item.getContent(), 60)));
        }

        return result.toString().trim();
    }

    private String executeFindPath(Map<String, Object> args, String projectId) {
        String sourceQuery = (String) args.get("source_query");
        String targetQuery = (String) args.get("target_query");

        // Find source item
        List<SearchResult> sourceResults = knowledgeTools.searchKnowledge(sourceQuery, projectId, 1);
        if (sourceResults.isEmpty()) {
            return "Cannot find path: source item not found for query '" + sourceQuery + "'";
        }
        String sourceId = sourceResults.get(0).id();
        String sourceContent = (String) sourceResults.get(0).payload().get("content");

        // Find target item
        List<SearchResult> targetResults = knowledgeTools.searchKnowledge(targetQuery, projectId, 1);
        if (targetResults.isEmpty()) {
            return "Cannot find path: target item not found for query '" + targetQuery + "'";
        }
        String targetId = targetResults.get(0).id();
        String targetContent = (String) targetResults.get(0).payload().get("content");

        // Find path
        List<KnowledgeItem> path = knowledgeTools.findPath(sourceId, targetId, 5);

        if (path.isEmpty()) {
            return String.format("No path found between '%s' and '%s'",
                    truncate(sourceContent, 30), truncate(targetContent, 30));
        }

        // Build result
        StringBuilder result = new StringBuilder();
        result.append(String.format("Path from '%s' to '%s':\n", truncate(sourceContent, 30), truncate(targetContent, 30)));

        for (int i = 0; i < path.size(); i++) {
            KnowledgeItem item = path.get(i);
            String prefix = i == 0 ? "START" : (i == path.size() - 1 ? "END" : String.valueOf(i));
            result.append(String.format("%s. [%s] %s\n", prefix, item.getType(), truncate(item.getContent(), 50)));
        }

        return result.toString().trim();
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
