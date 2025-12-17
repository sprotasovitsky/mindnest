package com.mindnest.agent.tools;

import com.mindnest.model.entity.KnowledgeItem;
import com.mindnest.model.entity.KnowledgeItem.KnowledgeType;
import com.mindnest.model.entity.KnowledgeRelation.RelationType;
import com.mindnest.repository.KnowledgeRepository;
import com.mindnest.repository.VectorRepository.SearchResult;
import com.mindnest.service.VectorSearchService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

/**
 * Tools for managing knowledge items (facts, decisions, notes, questions).
 */
@Component
@RequiredArgsConstructor
@Slf4j
public class KnowledgeTools {

    private final KnowledgeRepository knowledgeRepository;
    private final VectorSearchService vectorSearchService;

    @Value("${agent.thresholds.deduplication}")
    private double deduplicationThreshold;

    @Value("${agent.thresholds.update}")
    private double updateThreshold;

    @Value("${agent.thresholds.delete-auto}")
    private double deleteAutoThreshold;  // > this = delete without confirmation

    @Value("${agent.thresholds.delete-confirm}")
    private double deleteConfirmThreshold;  // > this = ask for confirmation

    /**
     * Create a new knowledge item (with deduplication)
     */
    public KnowledgeItem createKnowledge(String content, KnowledgeType type, String projectId, String ownerId) {
        log.info("Creating knowledge: type={}, project={}", type, projectId);

        // Check for duplicates - if very similar content exists, update instead of creating new
        List<SearchResult> existing = vectorSearchService.searchKnowledge(content, 3, projectId);
        for (SearchResult result : existing) {
            String existingContent = (String) result.payload().get("content");
            String existingType = (String) result.payload().get("type");

            // If same type and very similar content, skip creation
            if (existingType != null && existingType.equals(type.name()) && result.score() > deduplicationThreshold) {
                log.info("Skipping duplicate - existing item with similar content found: {}", result.id());
                return knowledgeRepository.findById(result.id()).orElse(null);
            }

            // If exact content match, skip
            if (existingContent != null && existingContent.equalsIgnoreCase(content)) {
                log.info("Skipping duplicate - exact content match found: {}", result.id());
                return knowledgeRepository.findById(result.id()).orElse(null);
            }
        }

        KnowledgeItem item = KnowledgeItem.builder()
                .content(content)
                .type(type)
                .projectId(projectId)
                .ownerId(ownerId)
                .createdAt(Instant.now())
                .updatedAt(Instant.now())
                .build();

        KnowledgeItem saved = knowledgeRepository.save(item);

        // Index for semantic search
        vectorSearchService.index(saved);

        log.info("Created knowledge item: {}", saved.getId());
        return saved;
    }

    /**
     * Get knowledge item by ID
     */
    public Optional<KnowledgeItem> getKnowledge(String id) {
        return knowledgeRepository.findById(id);
    }

    /**
     * Update knowledge content
     */
    public Optional<KnowledgeItem> updateKnowledge(String id, String newContent) {
        return knowledgeRepository.findById(id)
                .map(item -> {
                    item.setContent(newContent);
                    item.setUpdatedAt(Instant.now());
                    KnowledgeItem updated = knowledgeRepository.save(item);

                    // Re-index for semantic search
                    vectorSearchService.reindex(updated);

                    log.info("Updated knowledge item: {}", id);
                    return updated;
                });
    }

    /**
     * Find and update knowledge item by query
     */
    public Optional<KnowledgeItem> updateKnowledgeByQuery(String query, String newContent, String projectId) {
        log.info("Updating knowledge by query: '{}' in project: {}", query, projectId);

        // Search for matching items
        List<SearchResult> results = vectorSearchService.searchKnowledge(query, 5, projectId);

        if (results.isEmpty()) {
            log.warn("No items found to update for query: '{}'", query);
            return Optional.empty();
        }

        // Log search results for debugging
        log.info("Update search results for '{}': {}", query,
                results.stream()
                        .map(r -> String.format("'%s' (%.2f)", truncate((String)r.payload().get("content"), 30), r.score()))
                        .toList());

        // Find the best match by semantic similarity only
        // Embeddings handle morphology and language variations
        for (SearchResult result : results) {
            String content = (String) result.payload().get("content");
            if (content != null && result.score() > updateThreshold) {
                log.info("Found match for update: '{}' (score: {})", truncate(content, 50), result.score());
                return updateKnowledge(result.id(), newContent);
            }
        }

        log.warn("No matching item found for update query: '{}' (best score: {})",
                query, results.isEmpty() ? "none" : results.get(0).score());
        return Optional.empty();
    }

    /**
     * Search knowledge semantically
     */
    public List<SearchResult> searchKnowledge(String query, String projectId, int limit) {
        log.debug("Searching knowledge: query='{}', project={}", query, projectId);
        return vectorSearchService.searchKnowledge(query, limit, projectId);
    }

    /**
     * Get all active knowledge for a project (excludes soft-deleted)
     */
    public List<KnowledgeItem> getKnowledgeByProject(String projectId) {
        return knowledgeRepository.findByProjectIdAndDeletedAtIsNull(projectId);
    }

    /**
     * Get active knowledge by type (excludes soft-deleted)
     */
    public List<KnowledgeItem> getKnowledgeByType(String projectId, KnowledgeType type) {
        return knowledgeRepository.findByProjectIdAndTypeAndDeletedAtIsNull(projectId, type);
    }

    /**
     * Soft-delete knowledge item by ID
     */
    public boolean deleteKnowledge(String id) {
        return knowledgeRepository.findById(id)
                .map(item -> {
                    item.setDeletedAt(Instant.now());
                    knowledgeRepository.save(item);
                    vectorSearchService.remove(id);  // Remove from vector search
                    log.info("Soft-deleted knowledge item: {}", id);
                    return true;
                })
                .orElse(false);
    }

    /**
     * Delete items by their IDs (used after confirmation)
     */
    public int deleteByIds(List<String> ids) {
        int deleted = 0;
        for (String id : ids) {
            if (deleteKnowledge(id)) {
                deleted++;
            }
        }
        return deleted;
    }

    /**
     * Find and delete knowledge items by query.
     * Uses semantic similarity with two thresholds:
     * - > deleteAutoThreshold (0.85): delete immediately without confirmation
     * - > deleteConfirmThreshold (0.65): needs confirmation, returns preview
     * - <= deleteConfirmThreshold: no match found
     */
    public DeleteResult deleteKnowledgeByQuery(String query, String projectId) {
        log.info("Deleting knowledge by query: '{}' in project: {}", query, projectId);

        // Search for matching items
        List<SearchResult> results = vectorSearchService.searchKnowledge(query, 10, projectId);

        if (results.isEmpty()) {
            log.warn("No items found to delete for query: '{}'", query);
            return DeleteResult.notFound(query);
        }

        // Log search results for debugging
        log.info("Delete search results for '{}': {}", query,
                results.stream()
                        .map(r -> String.format("'%s' (%.2f)", truncate((String)r.payload().get("content"), 30), r.score()))
                        .toList());

        // Get the best match
        SearchResult bestMatch = results.get(0);
        String content = (String) bestMatch.payload().get("content");

        if (content == null) {
            return DeleteResult.notFound(query);
        }

        double score = bestMatch.score();

        // High confidence: delete immediately
        if (score > deleteAutoThreshold) {
            String itemId = bestMatch.id();
            if (deleteKnowledge(itemId)) {
                log.info("Auto-deleted (score {}): {}", score, truncate(content, 50));
                return DeleteResult.deleted(itemId, content, score);
            }
        }

        // Medium confidence: needs confirmation
        if (score > deleteConfirmThreshold) {
            log.info("Needs confirmation (score {}): {}", score, truncate(content, 50));
            return DeleteResult.needsConfirmation(bestMatch.id(), content, score);
        }

        // Low confidence: no good match
        log.warn("Best match score {} is below threshold {} for query: '{}'",
                score, deleteConfirmThreshold, query);
        return DeleteResult.notFound(query);
    }

    /**
     * Result of a delete operation
     */
    public record DeleteResult(
            Status status,
            String itemId,
            String content,
            double score,
            String query
    ) {
        public enum Status {
            DELETED,           // Item was deleted
            NEEDS_CONFIRMATION, // Item found but needs user confirmation
            NOT_FOUND          // No matching item found
        }

        public static DeleteResult deleted(String id, String content, double score) {
            return new DeleteResult(Status.DELETED, id, content, score, null);
        }

        public static DeleteResult needsConfirmation(String id, String content, double score) {
            return new DeleteResult(Status.NEEDS_CONFIRMATION, id, content, score, null);
        }

        public static DeleteResult notFound(String query) {
            return new DeleteResult(Status.NOT_FOUND, null, null, 0, query);
        }
    }

    /**
     * Preview items that would be deleted by query (for confirmation)
     */
    public List<DeletePreview> previewDelete(String query, String projectId) {
        log.info("Preview delete by query: '{}' in project: {}", query, projectId);

        List<SearchResult> results = vectorSearchService.searchKnowledge(query, 10, projectId);
        List<DeletePreview> previews = new ArrayList<>();

        for (SearchResult result : results) {
            String content = (String) result.payload().get("content");
            String type = (String) result.payload().get("type");

            if (content != null && result.score() > deleteConfirmThreshold) {
                previews.add(new DeletePreview(result.id(), type, content, result.score()));
            }
        }

        log.info("Preview found {} items to delete for query: '{}'", previews.size(), query);
        return previews;
    }

    /**
     * Preview record for delete confirmation
     */
    public record DeletePreview(String id, String type, String content, double score) {}

    private String truncate(String text, int maxLen) {
        return text != null && text.length() > maxLen ? text.substring(0, maxLen) + "..." : text;
    }

    /**
     * Create a relation between two knowledge items
     */
    public Optional<KnowledgeItem> createRelation(String sourceId, String targetId, RelationType relationType, String description) {
        log.info("Creating relation: {} -[{}]-> {}", sourceId, relationType, targetId);

        // Prevent self-loops
        if (sourceId.equals(targetId)) {
            log.warn("Cannot create self-referencing relation");
            return Optional.empty();
        }

        // Verify both items exist
        if (!knowledgeRepository.existsById(sourceId) || !knowledgeRepository.existsById(targetId)) {
            log.warn("Cannot create relation: one or both items don't exist");
            return Optional.empty();
        }

        KnowledgeItem result = knowledgeRepository.createRelation(
                sourceId,
                targetId,
                relationType.name(),
                description,
                1.0
        );
        return Optional.ofNullable(result);
    }

    /**
     * Delete a relation between two knowledge items
     */
    public void deleteRelation(String sourceId, String targetId) {
        log.info("Deleting relation: {} -> {}", sourceId, targetId);
        knowledgeRepository.deleteRelation(sourceId, targetId);
    }

    /**
     * Get related knowledge items (outgoing relations)
     */
    public List<KnowledgeItem> getRelatedKnowledge(String id) {
        return knowledgeRepository.findDirectRelations(id);
    }

    /**
     * Get incoming relations (items that relate to this one)
     */
    public List<KnowledgeItem> getIncomingRelations(String id) {
        return knowledgeRepository.findIncomingRelations(id);
    }

    /**
     * Get knowledge item with all its relations
     */
    public Optional<KnowledgeItem> getKnowledgeWithRelations(String id) {
        KnowledgeItem item = knowledgeRepository.findByIdWithRelations(id);
        return Optional.ofNullable(item);
    }

    /**
     * Find path between two knowledge items
     */
    public List<KnowledgeItem> findPath(String sourceId, String targetId, int maxDepth) {
        return knowledgeRepository.findPath(sourceId, targetId, maxDepth);
    }

    /**
     * Get all related items within a depth
     */
    public List<KnowledgeItem> getRelatedWithinDepth(String id, int depth) {
        return knowledgeRepository.findRelated(id, depth);
    }
}
