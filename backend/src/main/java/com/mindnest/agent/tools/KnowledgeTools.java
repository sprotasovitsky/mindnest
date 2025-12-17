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

    // NOTE: System is IMMUTABLE - no UPDATE, no DELETE operations
    // All changes create NEW items with relations (SUPERSEDES, CONTRADICTS)

    /**
     * Create a new knowledge item.
     * No deduplication - LLM decides when to create SUPERSEDES relations.
     */
    public KnowledgeItem createKnowledge(String content, KnowledgeType type, String projectId, String ownerId) {
        log.info("Creating knowledge: type={}, project={}", type, projectId);

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

    // NOTE: No update methods - system is immutable
    // Updates are done via CREATE new item + SUPERSEDES relation to old

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

    // NOTE: No delete methods - system is immutable
    // DELETE operations create [DELETED] marker nodes with SUPERSEDES relations
    // This preserves full history and allows graph-based analysis

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
