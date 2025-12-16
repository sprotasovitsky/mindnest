package com.mindnest.agent.tools;

import com.mindnest.model.entity.KnowledgeItem;
import com.mindnest.model.entity.KnowledgeItem.KnowledgeType;
import com.mindnest.model.entity.KnowledgeItem.TaskStatus;
import com.mindnest.repository.KnowledgeRepository;
import com.mindnest.repository.VectorRepository.SearchResult;
import com.mindnest.service.VectorSearchService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import java.time.Instant;
import java.time.LocalDate;
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
     * Create a new knowledge item
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
}
