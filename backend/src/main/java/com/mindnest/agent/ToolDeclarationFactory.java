package com.mindnest.agent;

import com.google.cloud.vertexai.api.FunctionDeclaration;
import com.google.cloud.vertexai.api.Schema;
import com.google.cloud.vertexai.api.Tool;
import com.google.cloud.vertexai.api.Type;
import org.springframework.stereotype.Component;

import java.util.List;

/**
 * Factory for creating tool/function declarations for the AI agent.
 * Centralizes all tool definitions for easier maintenance.
 */
@Component
public class ToolDeclarationFactory {

    /**
     * Build complete Tool with all function declarations.
     */
    public Tool buildTools() {
        return Tool.newBuilder()
                .addFunctionDeclarations(buildCreateKnowledgeFunction())
                .addFunctionDeclarations(buildSearchKnowledgeFunction())
                .addFunctionDeclarations(buildCreateTaskFunction())
                .addFunctionDeclarations(buildGetTasksForTodayFunction())
                .addFunctionDeclarations(buildGetActiveTasksFunction())
                .addFunctionDeclarations(buildUpdateTaskStatusFunction())
                .addFunctionDeclarations(buildCompleteTaskByTitleFunction())
                .addFunctionDeclarations(buildCompleteAllTasksByAssigneeFunction())
                .addFunctionDeclarations(buildGetMyItemsFunction())
                .addFunctionDeclarations(buildSearchTasksFunction())
                .addFunctionDeclarations(buildDecomposeTaskFunction())
                .addFunctionDeclarations(buildCreateProjectFunction())
                .addFunctionDeclarations(buildListProjectsFunction())
                .addFunctionDeclarations(buildGetCurrentDateFunction())
                .addFunctionDeclarations(buildCreateRelationFunction())
                .addFunctionDeclarations(buildGetRelatedFunction())
                .addFunctionDeclarations(buildFindPathFunction())
                .build();
    }

    /**
     * Get list of all function declarations (without wrapping in Tool).
     */
    public List<FunctionDeclaration> getAllFunctionDeclarations() {
        return List.of(
                buildCreateKnowledgeFunction(),
                buildSearchKnowledgeFunction(),
                buildCreateTaskFunction(),
                buildGetTasksForTodayFunction(),
                buildGetActiveTasksFunction(),
                buildUpdateTaskStatusFunction(),
                buildCompleteTaskByTitleFunction(),
                buildCompleteAllTasksByAssigneeFunction(),
                buildGetMyItemsFunction(),
                buildSearchTasksFunction(),
                buildDecomposeTaskFunction(),
                buildCreateProjectFunction(),
                buildListProjectsFunction(),
                buildGetCurrentDateFunction(),
                buildCreateRelationFunction(),
                buildGetRelatedFunction(),
                buildFindPathFunction()
        );
    }

    // =========================================================================
    // Knowledge Functions
    // =========================================================================

    private FunctionDeclaration buildCreateKnowledgeFunction() {
        return FunctionDeclaration.newBuilder()
                .setName("create_knowledge")
                .setDescription("Save a piece of information, fact, decision, or note to the knowledge base")
                .setParameters(Schema.newBuilder()
                        .setType(Type.OBJECT)
                        .putProperties("content", Schema.newBuilder()
                                .setType(Type.STRING)
                                .setDescription("The content to save")
                                .build())
                        .putProperties("type", Schema.newBuilder()
                                .setType(Type.STRING)
                                .setDescription("Type of knowledge: FACT, DECISION, NOTE, or QUESTION")
                                .build())
                        .addRequired("content")
                        .build())
                .build();
    }

    private FunctionDeclaration buildSearchKnowledgeFunction() {
        return FunctionDeclaration.newBuilder()
                .setName("search_knowledge")
                .setDescription("Search the knowledge base for relevant information")
                .setParameters(Schema.newBuilder()
                        .setType(Type.OBJECT)
                        .putProperties("query", Schema.newBuilder()
                                .setType(Type.STRING)
                                .setDescription("Search query")
                                .build())
                        .putProperties("limit", Schema.newBuilder()
                                .setType(Type.INTEGER)
                                .setDescription("Maximum number of results (default 5)")
                                .build())
                        .addRequired("query")
                        .build())
                .build();
    }

    // =========================================================================
    // Task Functions
    // =========================================================================

    private FunctionDeclaration buildCreateTaskFunction() {
        return FunctionDeclaration.newBuilder()
                .setName("create_task")
                .setDescription("Create a new task with optional deadline and assignee")
                .setParameters(Schema.newBuilder()
                        .setType(Type.OBJECT)
                        .putProperties("title", Schema.newBuilder()
                                .setType(Type.STRING)
                                .setDescription("Task title")
                                .build())
                        .putProperties("description", Schema.newBuilder()
                                .setType(Type.STRING)
                                .setDescription("Task description (optional)")
                                .build())
                        .putProperties("deadline", Schema.newBuilder()
                                .setType(Type.STRING)
                                .setDescription("Deadline: 'today', 'tomorrow', 'friday', or date like '2024-12-20'")
                                .build())
                        .putProperties("assignee", Schema.newBuilder()
                                .setType(Type.STRING)
                                .setDescription("Person assigned to the task (name)")
                                .build())
                        .addRequired("title")
                        .build())
                .build();
    }

    private FunctionDeclaration buildGetTasksForTodayFunction() {
        return FunctionDeclaration.newBuilder()
                .setName("get_tasks_for_today")
                .setDescription("Get all tasks due today")
                .setParameters(Schema.newBuilder()
                        .setType(Type.OBJECT)
                        .build())
                .build();
    }

    private FunctionDeclaration buildGetActiveTasksFunction() {
        return FunctionDeclaration.newBuilder()
                .setName("get_active_tasks")
                .setDescription("Get all active (TODO or IN_PROGRESS) tasks")
                .setParameters(Schema.newBuilder()
                        .setType(Type.OBJECT)
                        .build())
                .build();
    }

    private FunctionDeclaration buildUpdateTaskStatusFunction() {
        return FunctionDeclaration.newBuilder()
                .setName("update_task_status")
                .setDescription("Update the status of a task")
                .setParameters(Schema.newBuilder()
                        .setType(Type.OBJECT)
                        .putProperties("task_id", Schema.newBuilder()
                                .setType(Type.STRING)
                                .setDescription("ID of the task to update")
                                .build())
                        .putProperties("status", Schema.newBuilder()
                                .setType(Type.STRING)
                                .setDescription("New status: TODO, IN_PROGRESS, DONE, BLOCKED, or CANCELLED")
                                .build())
                        .addRequired("task_id")
                        .addRequired("status")
                        .build())
                .build();
    }

    private FunctionDeclaration buildCompleteTaskByTitleFunction() {
        return FunctionDeclaration.newBuilder()
                .setName("complete_task_by_title")
                .setDescription("Mark a SINGLE task as completed by searching for it by title. Use this when user mentions a SPECIFIC task name.")
                .setParameters(Schema.newBuilder()
                        .setType(Type.OBJECT)
                        .putProperties("title", Schema.newBuilder()
                                .setType(Type.STRING)
                                .setDescription("Task title or keywords to find the task (e.g. 'buy alcohol', 'shopping')")
                                .build())
                        .addRequired("title")
                        .build())
                .build();
    }

    private FunctionDeclaration buildCompleteAllTasksByAssigneeFunction() {
        return FunctionDeclaration.newBuilder()
                .setName("complete_all_tasks_by_assignee")
                .setDescription("Mark ALL tasks assigned to a person as completed. Use this when user says 'my tasks are done', 'I finished all my tasks', 'done with my tasks'. This completes ALL tasks for the person, not just one.")
                .setParameters(Schema.newBuilder()
                        .setType(Type.OBJECT)
                        .putProperties("assignee", Schema.newBuilder()
                                .setType(Type.STRING)
                                .setDescription("Name of the person whose ALL tasks should be marked as done (e.g. 'Boris', 'Andrey')")
                                .build())
                        .addRequired("assignee")
                        .build())
                .build();
    }

    private FunctionDeclaration buildGetMyItemsFunction() {
        return FunctionDeclaration.newBuilder()
                .setName("get_my_items")
                .setDescription("Get all items created/added by the current user. Use when user asks 'my items', 'what did I add', 'show my contributions', 'list what I saved'.")
                .setParameters(Schema.newBuilder()
                        .setType(Type.OBJECT)
                        .build())
                .build();
    }

    private FunctionDeclaration buildSearchTasksFunction() {
        return FunctionDeclaration.newBuilder()
                .setName("search_tasks")
                .setDescription("Search tasks by content")
                .setParameters(Schema.newBuilder()
                        .setType(Type.OBJECT)
                        .putProperties("query", Schema.newBuilder()
                                .setType(Type.STRING)
                                .setDescription("Search query")
                                .build())
                        .putProperties("limit", Schema.newBuilder()
                                .setType(Type.INTEGER)
                                .setDescription("Maximum results (default 5)")
                                .build())
                        .addRequired("query")
                        .build())
                .build();
    }

    private FunctionDeclaration buildDecomposeTaskFunction() {
        return FunctionDeclaration.newBuilder()
                .setName("decompose_task")
                .setDescription("Break down a task into smaller subtasks")
                .setParameters(Schema.newBuilder()
                        .setType(Type.OBJECT)
                        .putProperties("task_id", Schema.newBuilder()
                                .setType(Type.STRING)
                                .setDescription("ID of the parent task to decompose")
                                .build())
                        .putProperties("subtasks", Schema.newBuilder()
                                .setType(Type.ARRAY)
                                .setItems(Schema.newBuilder()
                                        .setType(Type.STRING)
                                        .build())
                                .setDescription("List of subtask titles")
                                .build())
                        .addRequired("task_id")
                        .addRequired("subtasks")
                        .build())
                .build();
    }

    // =========================================================================
    // Project Functions
    // =========================================================================

    private FunctionDeclaration buildCreateProjectFunction() {
        return FunctionDeclaration.newBuilder()
                .setName("create_project")
                .setDescription("Create a new project")
                .setParameters(Schema.newBuilder()
                        .setType(Type.OBJECT)
                        .putProperties("name", Schema.newBuilder()
                                .setType(Type.STRING)
                                .setDescription("Project name")
                                .build())
                        .putProperties("description", Schema.newBuilder()
                                .setType(Type.STRING)
                                .setDescription("Project description (optional)")
                                .build())
                        .addRequired("name")
                        .build())
                .build();
    }

    private FunctionDeclaration buildListProjectsFunction() {
        return FunctionDeclaration.newBuilder()
                .setName("list_projects")
                .setDescription("List all user's projects")
                .setParameters(Schema.newBuilder()
                        .setType(Type.OBJECT)
                        .build())
                .build();
    }

    // =========================================================================
    // Utility Functions
    // =========================================================================

    private FunctionDeclaration buildGetCurrentDateFunction() {
        return FunctionDeclaration.newBuilder()
                .setName("get_current_date")
                .setDescription("Get the current date")
                .setParameters(Schema.newBuilder()
                        .setType(Type.OBJECT)
                        .build())
                .build();
    }

    // =========================================================================
    // Relation Functions
    // =========================================================================

    private FunctionDeclaration buildCreateRelationFunction() {
        return FunctionDeclaration.newBuilder()
                .setName("create_relation")
                .setDescription("Create a relation/link between two knowledge items. Use when user says 'X is related to Y', 'X depends on Y', 'connect X and Y'. Relation types: RELATES_TO (general), DEPENDS_ON (dependency), SUPPORTS (evidence), CONTRADICTS (conflict), REFERENCES, DERIVED_FROM, SIMILAR_TO")
                .setParameters(Schema.newBuilder()
                        .setType(Type.OBJECT)
                        .putProperties("source_query", Schema.newBuilder()
                                .setType(Type.STRING)
                                .setDescription("Search query to find the SOURCE item (the item that has the relation)")
                                .build())
                        .putProperties("target_query", Schema.newBuilder()
                                .setType(Type.STRING)
                                .setDescription("Search query to find the TARGET item (the item being related to)")
                                .build())
                        .putProperties("relation_type", Schema.newBuilder()
                                .setType(Type.STRING)
                                .setDescription("Type of relation: RELATES_TO, DEPENDS_ON, SUPPORTS, CONTRADICTS, REFERENCES, DERIVED_FROM, SIMILAR_TO")
                                .build())
                        .putProperties("description", Schema.newBuilder()
                                .setType(Type.STRING)
                                .setDescription("Optional description of the relation")
                                .build())
                        .addRequired("source_query")
                        .addRequired("target_query")
                        .addRequired("relation_type")
                        .build())
                .build();
    }

    private FunctionDeclaration buildGetRelatedFunction() {
        return FunctionDeclaration.newBuilder()
                .setName("get_related")
                .setDescription("Get all items related to a knowledge item. Use when user asks 'what is related to X', 'show connections for X', 'what depends on X'")
                .setParameters(Schema.newBuilder()
                        .setType(Type.OBJECT)
                        .putProperties("query", Schema.newBuilder()
                                .setType(Type.STRING)
                                .setDescription("Search query to find the item")
                                .build())
                        .putProperties("depth", Schema.newBuilder()
                                .setType(Type.INTEGER)
                                .setDescription("How many levels of relations to traverse (default 1, max 3)")
                                .build())
                        .addRequired("query")
                        .build())
                .build();
    }

    private FunctionDeclaration buildFindPathFunction() {
        return FunctionDeclaration.newBuilder()
                .setName("find_path")
                .setDescription("Find the path/connection between two knowledge items. Use when user asks 'how is X connected to Y', 'what's the relation between X and Y'")
                .setParameters(Schema.newBuilder()
                        .setType(Type.OBJECT)
                        .putProperties("source_query", Schema.newBuilder()
                                .setType(Type.STRING)
                                .setDescription("Search query to find the first item")
                                .build())
                        .putProperties("target_query", Schema.newBuilder()
                                .setType(Type.STRING)
                                .setDescription("Search query to find the second item")
                                .build())
                        .addRequired("source_query")
                        .addRequired("target_query")
                        .build())
                .build();
    }
}
