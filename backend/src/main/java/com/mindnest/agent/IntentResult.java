package com.mindnest.agent;

import java.util.List;

/**
 * Result of intent detection from user message.
 */
public record IntentResult(
    Intent intent,
    String toolToCall,
    List<String> entities,
    String contentToSave,
    List<TaskInfo> tasks,
    String updateQuery,      // For UPDATE: what to find
    String updateNewContent  // For UPDATE: replacement content
) {

    public enum Intent {
        SAVE,       // User provides information to store
        SEARCH,     // User asks a question or wants to find something
        UPDATE,     // User corrects existing information
        DELETE,     // User wants to remove something
        TASK,       // User wants to create a task
        COMPLETE,   // User marks task as done
        RELATION,   // User wants to link/connect knowledge items
        CHAT        // General conversation, no tool needed
    }

    /**
     * Task information extracted from intent
     */
    public record TaskInfo(
        String title,
        String deadline,
        String assignee
    ) {}

    /**
     * Check if this intent requires a tool call
     */
    public boolean requiresToolCall() {
        return intent != Intent.CHAT;
    }

    /**
     * Create a default CHAT intent (no action needed)
     */
    public static IntentResult chat() {
        return new IntentResult(Intent.CHAT, null, List.of(), null, List.of(), null, null);
    }
}
