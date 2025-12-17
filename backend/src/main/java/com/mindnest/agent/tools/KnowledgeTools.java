package com.mindnest.agent.tools;

import com.mindnest.model.entity.KnowledgeItem;
import com.mindnest.model.entity.KnowledgeItem.KnowledgeType;
import com.mindnest.model.entity.KnowledgeRelation.RelationType;
import com.mindnest.repository.KnowledgeRepository;
import com.mindnest.repository.VectorRepository.SearchResult;
import com.mindnest.service.VectorSearchService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
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

            // If same type and very similar content (>85% similarity), skip creation
            if (existingType != null && existingType.equals(type.name()) && result.score() > 0.85) {
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

        // Find the best match (contains query or high similarity)
        String queryLower = query.toLowerCase();
        for (SearchResult result : results) {
            String content = (String) result.payload().get("content");
            // Update if: content contains query keywords OR high semantic match (>0.7)
            // Note: cross-language queries have ~0.4 similarity, so they won't match anyway
            boolean containsQuery = content != null && content.toLowerCase().contains(queryLower);
            boolean highSemanticMatch = result.score() > 0.7;
            if (content != null && (containsQuery || highSemanticMatch)) {
                log.info("Found match for update: '{}' (score: {}, contains: {})",
                        truncate(content, 50), result.score(), containsQuery);
                String itemId = result.id();
                return updateKnowledge(itemId, newContent);
            }
        }

        log.warn("No matching item found for update query: '{}'", query);
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
     * Get all knowledge for a project
     */
    public List<KnowledgeItem> getKnowledgeByProject(String projectId) {
        return knowledgeRepository.findByProjectId(projectId);
    }

    /**
     * Get knowledge by type
     */
    public List<KnowledgeItem> getKnowledgeByType(String projectId, KnowledgeType type) {
        return knowledgeRepository.findByProjectIdAndType(projectId, type);
    }

    /**
     * Delete knowledge item
     */
    public boolean deleteKnowledge(String id) {
        if (knowledgeRepository.existsById(id)) {
            knowledgeRepository.deleteById(id);
            vectorSearchService.remove(id);
            log.info("Deleted knowledge item: {}", id);
            return true;
        }
        return false;
    }

    /**
     * Preview items that would be deleted by query (for confirmation)
     * Returns list of matching items without deleting them.
     */
    public List<DeletePreview> previewDelete(String query, String projectId) {
        log.info("Preview delete by query: '{}' in project: {}", query, projectId);

        List<SearchResult> results = vectorSearchService.searchKnowledge(query, 10, projectId);
        List<DeletePreview> previews = new ArrayList<>();

        for (SearchResult result : results) {
            String content = (String) result.payload().get("content");
            String type = (String) result.payload().get("type");

            // Include if similarity > 0.75 (very high threshold for safe deletion)
            if (content != null && result.score() > 0.75) {
                previews.add(new DeletePreview(result.id(), type, content, result.score()));
            }
        }

        log.info("Preview found {} items to delete for query: '{}'", previews.size(), query);
        return previews;
    }

    /**
     * Delete items by their IDs (used after preview confirmation)
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
     * Find and delete knowledge items by query
     * Uses semantic similarity + keyword matching for safe deletion
     */
    public int deleteKnowledgeByQuery(String query, String projectId) {
        log.info("Deleting knowledge by query: '{}' in project: {}", query, projectId);

        // Search for matching items
        List<SearchResult> results = vectorSearchService.searchKnowledge(query, 10, projectId);

        if (results.isEmpty()) {
            log.warn("No items found to delete for query: '{}'", query);
            return 0;
        }

        // Extract keywords from query for additional matching
        String[] queryKeywords = query.toLowerCase().split("\\s+");

        // Delete items with high semantic similarity OR keyword match
        int deleted = 0;
        for (SearchResult result : results) {
            String content = (String) result.payload().get("content");
            if (content == null) continue;

            // Check if content contains any query keyword (case-insensitive)
            String contentLower = content.toLowerCase();
            boolean hasKeywordMatch = false;
            for (String keyword : queryKeywords) {
                if (keyword.length() >= 4 && contentLower.contains(keyword)) {
                    hasKeywordMatch = true;
                    break;
                }
            }

            // Delete if: high similarity (>0.8) OR (moderate similarity >0.6 AND keyword match)
            boolean shouldDelete = result.score() > 0.8 || (result.score() > 0.6 && hasKeywordMatch);
            if (shouldDelete) {
                String itemId = result.id();
                if (knowledgeRepository.existsById(itemId)) {
                    knowledgeRepository.deleteById(itemId);
                    vectorSearchService.remove(itemId);
                    log.info("Deleted knowledge item: {} - '{}' (score: {})", itemId, truncate(content, 50), result.score());
                    deleted++;
                }
            }
        }

        log.info("Deleted {} items for query: '{}'", deleted, query);
        return deleted;
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
