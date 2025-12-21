package com.mindnest.agent.handler;

import com.mindnest.agent.ChunkIntent;
import com.mindnest.agent.ChunkResult;
import com.mindnest.agent.RelationIntent;
import com.mindnest.agent.ToolExecutor;
import com.mindnest.agent.UserContextBuilder;
import com.mindnest.agent.tools.TaskTools;
import com.mindnest.model.entity.KnowledgeItem;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Handles TASK intent - creates tasks or completes existing ones.
 * Includes clarification flow for ambiguous task completion.
 */
@Component
@RequiredArgsConstructor
@Slf4j
public class TaskIntentHandler implements IntentHandler {

    private final ToolExecutor toolExecutor;
    private final TaskTools taskTools;
    private final UserContextBuilder userContextBuilder;

    @Override
    public String getIntentType() {
        return "TASK";
    }

    @Override
    public ChunkResult execute(ChunkIntent intent, String projectId, String userId) {
        String status = intent.properties() != null
                ? (String) intent.properties().get("status")
                : "TODO";

        // If completing a task (status=DONE), handle clarification flow
        if ("DONE".equalsIgnoreCase(status)) {
            return handleTaskCompletion(intent, projectId, userId);
        }

        // Create new task
        return createNewTask(intent, projectId, userId);
    }

    /**
     * Create a new task with optional deadline and assignee.
     */
    private ChunkResult createNewTask(ChunkIntent intent, String projectId, String userId) {
        Map<String, Object> args = new HashMap<>();
        args.put("title", intent.content());

        if (intent.properties() != null) {
            if (intent.properties().containsKey("deadline")) {
                args.put("deadline", intent.properties().get("deadline").toString());
            }
            if (intent.properties().containsKey("assignee")) {
                args.put("assignee", intent.properties().get("assignee").toString());
            }
        }

        String result = toolExecutor.execute("create_task", args, projectId, userId);

        // Create relation to assignee if specified
        List<String> linkedTo = new ArrayList<>();
        for (RelationIntent rel : intent.relations()) {
            if ("ASSIGNED_TO".equals(rel.type())) {
                try {
                    String linkResult = createRelation(intent.content(), rel.toQuery(), rel.type(), projectId, userId);
                    if (linkResult != null) {
                        linkedTo.add(rel.toQuery());
                    }
                } catch (Exception e) {
                    log.warn("Failed to link task to assignee: {}", e.getMessage());
                }
            }
        }

        return new ChunkResult(true, null, "Task: " + intent.content(), linkedTo, null, false, List.of());
    }

    /**
     * Handle task completion with clarification flow.
     * If needs_clarification=true and multiple tasks: show numbered list
     * If complete_all=true: complete all user's tasks
     * If selected_indices present: complete specific tasks
     * Otherwise: use semantic search to find matching task
     */
    private ChunkResult handleTaskCompletion(ChunkIntent intent, String projectId, String userId) {
        Map<String, Object> props = intent.properties() != null ? intent.properties() : Map.of();

        // Check if this is a response to clarification: "all" or specific selection
        Boolean completeAll = props.get("complete_all") != null && Boolean.TRUE.equals(props.get("complete_all"));

        // Safely extract selected_indices (could be List<Integer> or List<Double> from JSON)
        List<Integer> selectedIndices = userContextBuilder.extractIntegerList(props.get("selected_indices"));

        // Safely extract pending_task_ids (could be List<String>)
        List<String> pendingTaskIds = userContextBuilder.extractStringList(props.get("pending_task_ids"));

        // Case 1: User said "all" after clarification
        if (completeAll) {
            return completeAllTasks(projectId, userId);
        }

        // Case 2: User selected specific tasks by indices (e.g., "1 and 3")
        if (selectedIndices != null && !selectedIndices.isEmpty() && pendingTaskIds != null && !pendingTaskIds.isEmpty()) {
            return completeSelectedTasks(selectedIndices, pendingTaskIds);
        }

        // Case 3: Check if needs clarification (ambiguous task completion)
        Boolean needsClarification = props.get("needs_clarification") != null
                && Boolean.TRUE.equals(props.get("needs_clarification"));

        if (needsClarification) {
            return requestTaskClarification(projectId, userId);
        }

        // Case 4: Specific task mentioned - use semantic search
        return completeSpecificTask(intent, projectId);
    }

    /**
     * Complete all user's active tasks.
     */
    private ChunkResult completeAllTasks(String projectId, String userId) {
        String userName = userContextBuilder.getUserName(userId);
        List<KnowledgeItem> tasks = taskTools.getActiveTasksForUser(projectId, userId, userName);

        if (tasks.isEmpty()) {
            return new ChunkResult(true, null, "No active tasks found", List.of(), null, false, List.of());
        }

        List<KnowledgeItem> completed = taskTools.completeTasksByIds(
                tasks.stream().map(KnowledgeItem::getId).toList()
        );

        List<String> linkedTo = completed.stream()
                .map(t -> "completed: " + getTaskTitle(t))
                .toList();

        return new ChunkResult(true, null,
                "Completed " + completed.size() + " tasks",
                linkedTo, null, false, List.of());
    }

    /**
     * Complete tasks selected by indices.
     */
    private ChunkResult completeSelectedTasks(List<Integer> selectedIndices, List<String> pendingTaskIds) {
        List<String> idsToComplete = new ArrayList<>();
        for (Integer idx : selectedIndices) {
            if (idx >= 1 && idx <= pendingTaskIds.size()) {
                idsToComplete.add(pendingTaskIds.get(idx - 1)); // 1-based index
            }
        }

        if (idsToComplete.isEmpty()) {
            return new ChunkResult(true, null, "Invalid selection", List.of(), null, false, List.of());
        }

        List<KnowledgeItem> completed = taskTools.completeTasksByIds(idsToComplete);

        List<String> linkedTo = completed.stream()
                .map(t -> "completed: " + getTaskTitle(t))
                .toList();

        return new ChunkResult(true, null,
                "Completed " + completed.size() + " tasks",
                linkedTo, null, false, List.of());
    }

    /**
     * Request clarification when task completion is ambiguous.
     */
    private ChunkResult requestTaskClarification(String projectId, String userId) {
        String userName = userContextBuilder.getUserName(userId);
        List<KnowledgeItem> tasks = taskTools.getActiveTasksForUser(projectId, userId, userName);

        if (tasks.isEmpty()) {
            return new ChunkResult(true, null, "You have no active tasks", List.of(), null, false, List.of());
        }

        // Single task - complete without asking
        if (tasks.size() == 1) {
            KnowledgeItem task = tasks.get(0);
            taskTools.completeTasksByIds(List.of(task.getId()));
            return new ChunkResult(true, null, "Completed: " + getTaskTitle(task),
                    List.of("completed: " + getTaskTitle(task)), null, false, List.of());
        }

        // Multiple tasks - need clarification
        String clarificationMessage = buildTaskClarificationMessage(tasks);
        List<String> taskIds = tasks.stream()
                .map(KnowledgeItem::getId)
                .toList();

        return ChunkResult.clarification(clarificationMessage, taskIds);
    }

    /**
     * Complete a specific task using semantic search.
     */
    private ChunkResult completeSpecificTask(ChunkIntent intent, String projectId) {
        String targetQuery = intent.content();
        for (RelationIntent rel : intent.relations()) {
            if ("SUPERSEDES".equals(rel.type()) && rel.toQuery() != null) {
                targetQuery = rel.toQuery();
                break;
            }
        }

        Map<String, Object> args = new HashMap<>();
        args.put("title", targetQuery);
        String result = toolExecutor.execute("complete_task_by_title", args, projectId, null);

        log.info("Task completion result for '{}': {}", targetQuery, result);

        List<String> linkedTo = new ArrayList<>();
        if (result != null && result.contains("Completed task")) {
            linkedTo.add("completed: " + targetQuery);
        }
        return new ChunkResult(true, null, "Completed: " + targetQuery, linkedTo, null, false, List.of());
    }

    /**
     * Build clarification message with numbered task list.
     */
    private String buildTaskClarificationMessage(List<KnowledgeItem> tasks) {
        StringBuilder sb = new StringBuilder();
        sb.append("You have ").append(tasks.size()).append(" active tasks:\n");
        for (int i = 0; i < tasks.size(); i++) {
            String title = getTaskTitle(tasks.get(i));
            sb.append("[").append(i + 1).append("] ").append(title).append("\n");
        }
        sb.append("\nWhich ones are complete? (enter numbers like '1 and 3', or 'all' for all)");
        return sb.toString();
    }

    /**
     * Get task title (first line of content).
     */
    private String getTaskTitle(KnowledgeItem task) {
        String content = task.getContent();
        if (content == null) return "Untitled";
        int newlineIdx = content.indexOf('\n');
        return newlineIdx > 0 ? content.substring(0, newlineIdx) : content;
    }

    /**
     * Create a relation between items using semantic search.
     */
    private String createRelation(String sourceContent, String targetQuery, String relationType,
                                   String projectId, String userId) {
        Map<String, Object> args = new HashMap<>();
        args.put("source_query", sourceContent);
        args.put("target_query", targetQuery);
        args.put("relation_type", relationType);
        return toolExecutor.execute("create_relation", args, projectId, userId);
    }
}
