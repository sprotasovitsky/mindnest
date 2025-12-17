package com.mindnest.agent.tools;

import com.mindnest.model.entity.KnowledgeItem;
import com.mindnest.model.entity.KnowledgeItem.KnowledgeType;
import com.mindnest.model.entity.KnowledgeItem.TaskStatus;
import com.mindnest.model.entity.KnowledgeRelation.RelationType;
import com.mindnest.repository.KnowledgeRepository;
import com.mindnest.repository.VectorRepository.SearchResult;
import com.mindnest.service.VectorSearchService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.time.Instant;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

/**
 * Tools for managing tasks.
 */
@Component
@RequiredArgsConstructor
@Slf4j
public class TaskTools {

    private final KnowledgeRepository knowledgeRepository;
    private final VectorSearchService vectorSearchService;

    @Value("${agent.thresholds.task-search}")
    private double taskSearchThreshold;

    /**
     * Create a new task
     */
    public KnowledgeItem createTask(String title, String description, LocalDate deadline,
                                     String projectId, String ownerId) {
        log.info("Creating task: '{}', deadline={}, project={}", title, deadline, projectId);

        String content = description != null && !description.isBlank()
                ? title + "\n\n" + description
                : title;

        KnowledgeItem task = KnowledgeItem.builder()
                .content(content)
                .type(KnowledgeType.TASK)
                .status(TaskStatus.TODO)
                .deadline(deadline)
                .projectId(projectId)
                .ownerId(ownerId)
                .createdAt(Instant.now())
                .updatedAt(Instant.now())
                .build();

        KnowledgeItem saved = knowledgeRepository.save(task);

        // Index for semantic search
        vectorSearchService.index(saved);

        log.info("Created task: {} (deadline: {})", saved.getId(), deadline);
        return saved;
    }

    /**
     * Update task status
     */
    public Optional<KnowledgeItem> updateTaskStatus(String taskId, TaskStatus newStatus) {
        return knowledgeRepository.findById(taskId)
                .filter(item -> item.getType() == KnowledgeType.TASK)
                .map(task -> {
                    task.setStatus(newStatus);
                    task.setUpdatedAt(Instant.now());
                    KnowledgeItem updated = knowledgeRepository.save(task);
                    vectorSearchService.reindex(updated);
                    log.info("Updated task {} status to {}", taskId, newStatus);
                    return updated;
                });
    }

    /**
     * Get tasks for today for a specific user
     */
    public List<KnowledgeItem> getTasksForToday(String ownerId) {
        LocalDate today = LocalDate.now();
        log.debug("Getting tasks for today ({}) for user: {}", today, ownerId);
        return knowledgeRepository.findTasksByOwnerAndDeadline(ownerId, today);
    }

    /**
     * Get tasks by deadline
     */
    public List<KnowledgeItem> getTasksByDeadline(String projectId, LocalDate deadline) {
        return knowledgeRepository.findTasksByDeadline(projectId, deadline);
    }

    /**
     * Get all active tasks for user (TODO or IN_PROGRESS)
     */
    public List<KnowledgeItem> getActiveTasks(String ownerId) {
        return knowledgeRepository.findActiveTasksByOwner(ownerId);
    }

    /**
     * Get tasks by status (excludes soft-deleted)
     */
    public List<KnowledgeItem> getTasksByStatus(String projectId, TaskStatus status) {
        return knowledgeRepository.findByProjectIdAndTypeAndStatusAndDeletedAtIsNull(projectId, KnowledgeType.TASK, status);
    }

    /**
     * Get overdue tasks
     */
    public List<KnowledgeItem> getOverdueTasks() {
        return knowledgeRepository.findOverdueTasks();
    }

    /**
     * Search tasks semantically
     */
    public List<SearchResult> searchTasks(String query, String projectId, int limit) {
        return vectorSearchService.searchTasks(query, limit, projectId);
    }

    /**
     * Update task content/description
     */
    public Optional<KnowledgeItem> updateTaskContent(String taskId, String newContent) {
        return knowledgeRepository.findById(taskId)
                .filter(item -> item.getType() == KnowledgeType.TASK)
                .map(task -> {
                    task.setContent(newContent);
                    task.setUpdatedAt(Instant.now());
                    KnowledgeItem updated = knowledgeRepository.save(task);
                    vectorSearchService.reindex(updated);
                    log.info("Updated task {} content", taskId);
                    return updated;
                });
    }

    /**
     * Update task deadline
     */
    public Optional<KnowledgeItem> updateTaskDeadline(String taskId, LocalDate newDeadline) {
        return knowledgeRepository.findById(taskId)
                .filter(item -> item.getType() == KnowledgeType.TASK)
                .map(task -> {
                    task.setDeadline(newDeadline);
                    task.setUpdatedAt(Instant.now());
                    KnowledgeItem updated = knowledgeRepository.save(task);
                    vectorSearchService.reindex(updated);
                    log.info("Updated task {} deadline to {}", taskId, newDeadline);
                    return updated;
                });
    }

    /**
     * Delete task
     */
    public boolean deleteTask(String taskId) {
        Optional<KnowledgeItem> task = knowledgeRepository.findById(taskId);
        if (task.isPresent() && task.get().getType() == KnowledgeType.TASK) {
            knowledgeRepository.deleteById(taskId);
            vectorSearchService.remove(taskId);
            log.info("Deleted task: {}", taskId);
            return true;
        }
        return false;
    }

    /**
     * Get task by ID
     */
    public Optional<KnowledgeItem> getTask(String taskId) {
        return knowledgeRepository.findById(taskId)
                .filter(item -> item.getType() == KnowledgeType.TASK);
    }

    /**
     * Find and complete task by title/content match.
     * Uses semantic search - embeddings handle morphology and language variations.
     */
    public Optional<KnowledgeItem> completeTaskByTitle(String titleQuery, String projectId) {
        log.info("Completing task by title: '{}' in project: {}", titleQuery, projectId);

        // Use semantic search to find matching task
        List<SearchResult> results = vectorSearchService.searchTasks(titleQuery, 5, projectId);

        log.info("Task search results for '{}': {}", titleQuery,
                results.stream()
                        .map(r -> String.format("'%s' (%.2f)", truncate((String)r.payload().get("content"), 30), r.score()))
                        .toList());

        // Find first matching task that's not done
        for (SearchResult result : results) {
            if (result.score() > taskSearchThreshold) {
                Optional<KnowledgeItem> foundTask = knowledgeRepository.findById(result.id());
                if (foundTask.isPresent() &&
                    foundTask.get().getStatus() != TaskStatus.DONE &&
                    foundTask.get().getStatus() != TaskStatus.CANCELLED) {

                    KnowledgeItem task = foundTask.get();
                    task.setStatus(TaskStatus.DONE);
                    task.setUpdatedAt(Instant.now());
                    KnowledgeItem updated = knowledgeRepository.save(task);
                    vectorSearchService.reindex(updated);
                    log.info("Completed task: {} - '{}' (score: {})",
                            updated.getId(), getTaskTitle(updated), result.score());
                    return Optional.of(updated);
                }
            }
        }

        log.warn("No matching task found for: '{}' (best score: {})",
                titleQuery, results.isEmpty() ? "none" : results.get(0).score());
        return Optional.empty();
    }

    private String truncate(String text, int maxLen) {
        return text != null && text.length() > maxLen ? text.substring(0, maxLen) + "..." : text;
    }

    private String getTaskTitle(KnowledgeItem task) {
        String content = task.getContent();
        int newlineIdx = content.indexOf('\n');
        return newlineIdx > 0 ? content.substring(0, newlineIdx) : content;
    }

    /**
     * Decompose a task into subtasks
     */
    public List<KnowledgeItem> decomposeTask(String parentTaskId, List<String> subtaskTitles) {
        Optional<KnowledgeItem> parentOpt = getTask(parentTaskId);
        if (parentOpt.isEmpty()) {
            log.warn("Parent task not found: {}", parentTaskId);
            return List.of();
        }

        KnowledgeItem parent = parentOpt.get();
        List<KnowledgeItem> subtasks = new ArrayList<>();

        for (String title : subtaskTitles) {
            // Create subtask
            KnowledgeItem subtask = KnowledgeItem.builder()
                    .content(title)
                    .type(KnowledgeType.TASK)
                    .status(TaskStatus.TODO)
                    .deadline(parent.getDeadline())
                    .projectId(parent.getProjectId())
                    .ownerId(parent.getOwnerId())
                    .createdAt(Instant.now())
                    .updatedAt(Instant.now())
                    .build();

            KnowledgeItem saved = knowledgeRepository.save(subtask);
            vectorSearchService.index(saved);

            // Create SUBTASK_OF relation to parent
            knowledgeRepository.createRelation(
                    saved.getId(),
                    parentTaskId,
                    RelationType.SUBTASK_OF.name(),
                    "Subtask of parent task",
                    1.0
            );

            subtasks.add(saved);
            log.info("Created subtask: {} for parent: {}", saved.getId(), parentTaskId);
        }

        return subtasks;
    }

    /**
     * Get subtasks of a parent task
     */
    public List<KnowledgeItem> getSubtasks(String parentTaskId) {
        return knowledgeRepository.findIncomingRelations(parentTaskId).stream()
                .filter(item -> item.getType() == KnowledgeType.TASK)
                .toList();
    }
}
