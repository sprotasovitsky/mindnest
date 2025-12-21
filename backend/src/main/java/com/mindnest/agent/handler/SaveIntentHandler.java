package com.mindnest.agent.handler;

import com.mindnest.agent.ChunkIntent;
import com.mindnest.agent.ChunkResult;
import com.mindnest.agent.RelationIntent;
import com.mindnest.agent.ToolExecutor;
import com.mindnest.agent.tools.KnowledgeTools;
import com.mindnest.model.entity.KnowledgeRelation;
import com.mindnest.repository.VectorRepository.SearchResult;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Handles SAVE intent - creates knowledge/expense items with relations.
 */
@Component
@RequiredArgsConstructor
@Slf4j
public class SaveIntentHandler implements IntentHandler {

    private final ToolExecutor toolExecutor;
    private final KnowledgeTools knowledgeTools;

    // Minimum similarity score for creating SUPERSEDES/CONTRADICTS relations
    // Higher threshold prevents linking unrelated items
    @Value("${agent.thresholds.update:0.6}")
    private double relationThreshold;

    @Override
    public String getIntentType() {
        return "SAVE";
    }

    @Override
    public ChunkResult execute(ChunkIntent intent, String projectId, String userId) {
        // IMPORTANT: Find relation targets BEFORE creating new item
        // Otherwise vector search will find the newly created item instead of the original
        Map<String, String> preFoundTargets = findRelationTargets(intent, projectId);

        // Build arguments for create_knowledge
        Map<String, Object> args = new HashMap<>();
        args.put("content", intent.content());
        args.put("type", determineKnowledgeType(intent));

        // Add extracted properties (amount, currency, assignee)
        if (intent.properties() != null) {
            if (intent.properties().containsKey("amount")) {
                args.put("amount", intent.properties().get("amount"));
            }
            if (intent.properties().containsKey("currency")) {
                args.put("currency", intent.properties().get("currency"));
            }
            if (intent.properties().containsKey("assignee")) {
                args.put("assignee", intent.properties().get("assignee"));
            }
        }

        // Execute tool
        String result = toolExecutor.execute("create_knowledge", args, projectId, userId);

        // Extract created item ID from result
        String createdItemId = extractIdFromResult(result);

        // Create relations using pre-found target IDs
        List<String> linkedTo = createRelations(intent, createdItemId, preFoundTargets);

        return new ChunkResult(true, createdItemId, intent.content(), linkedTo, null, false, List.of());
    }

    /**
     * Find relation targets BEFORE creating new item.
     * Only includes targets with similarity score above threshold.
     */
    private Map<String, String> findRelationTargets(ChunkIntent intent, String projectId) {
        Map<String, String> preFoundTargets = new HashMap<>();
        for (RelationIntent rel : intent.relations()) {
            try {
                List<SearchResult> searchResults = knowledgeTools.searchKnowledge(rel.toQuery(), projectId, 1);
                if (!searchResults.isEmpty()) {
                    SearchResult result = searchResults.get(0);
                    // Only create relation if similarity is above threshold
                    if (result.score() >= relationThreshold) {
                        preFoundTargets.put(rel.toQuery(), result.id());
                        log.debug("Pre-found target for '{}': {} (score: {})",
                                rel.toQuery(), result.id(), result.score());
                    } else {
                        log.info("Skipping relation to '{}': score {} below threshold {}",
                                rel.toQuery(), result.score(), relationThreshold);
                    }
                }
            } catch (Exception e) {
                log.warn("Failed to pre-find target '{}': {}", rel.toQuery(), e.getMessage());
            }
        }
        return preFoundTargets;
    }

    /**
     * Determine knowledge type based on intent type.
     */
    private String determineKnowledgeType(ChunkIntent intent) {
        return switch (intent.type() != null ? intent.type().toUpperCase() : "KNOWLEDGE") {
            case "EXPENSE" -> "FACT";  // Expenses stored as FACT
            case "KNOWLEDGE" -> intent.subtype() != null ? intent.subtype().toUpperCase() : "NOTE";
            case "TASK" -> "TASK";
            default -> "NOTE";
        };
    }

    /**
     * Extract item ID from tool execution result.
     * Result format: "Created note: '...' (id: UUID)"
     */
    private String extractIdFromResult(String result) {
        if (result == null) return null;
        int idStart = result.indexOf("(id: ");
        if (idStart < 0) return null;
        int idEnd = result.indexOf(")", idStart);
        if (idEnd < 0) return null;
        return result.substring(idStart + 5, idEnd);
    }

    /**
     * Create relations using pre-found target IDs.
     */
    private List<String> createRelations(ChunkIntent intent, String createdItemId, Map<String, String> preFoundTargets) {
        List<String> linkedTo = new ArrayList<>();
        for (RelationIntent rel : intent.relations()) {
            try {
                String targetId = preFoundTargets.get(rel.toQuery());
                if (targetId != null && createdItemId != null) {
                    var relResult = knowledgeTools.createRelation(
                            createdItemId,
                            targetId,
                            KnowledgeRelation.RelationType.valueOf(rel.type()),
                            null
                    );
                    if (relResult.isPresent()) {
                        linkedTo.add(rel.toQuery() + " (" + rel.type() + ")");
                        log.info("Created {} relation: {} -> {}", rel.type(), createdItemId, targetId);
                    }
                } else {
                    log.warn("Could not create relation: targetId={}, createdItemId={}", targetId, createdItemId);
                }
            } catch (Exception e) {
                log.warn("Failed to create relation to '{}': {}", rel.toQuery(), e.getMessage());
            }
        }
        return linkedTo;
    }
}
