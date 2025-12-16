package com.mindnest.service;

import com.mindnest.model.entity.KnowledgeItem;
import com.mindnest.repository.VectorRepository;
import com.mindnest.repository.VectorRepository.SearchResult;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Service that combines embeddings with vector storage for semantic search.
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class VectorSearchService {

    private final EmbeddingService embeddingService;
    private final VectorRepository vectorRepository;

    /**
     * Index a knowledge item for semantic search
     */
    public void index(KnowledgeItem item) {
        try {
            log.debug("Indexing knowledge item: {}", item.getId());

            // Generate embedding for the content
            List<Float> embedding = embeddingService.embed(item.getContent());

            // Build metadata
            Map<String, String> metadata = new HashMap<>();
            metadata.put("projectId", item.getProjectId());
            metadata.put("type", item.getType().name());
            metadata.put("content", truncate(item.getContent(), 1000)); // Store truncated content for retrieval

            if (item.getOwnerId() != null) {
                metadata.put("ownerId", item.getOwnerId());
            }
            if (item.getStatus() != null) {
                metadata.put("status", item.getStatus().name());
            }

            // Store in vector database
            vectorRepository.upsert(item.getId(), embedding, metadata);

            log.info("Indexed knowledge item: {} (type: {})", item.getId(), item.getType());
        } catch (IOException e) {
            log.error("Failed to index knowledge item: {}", item.getId(), e);
            throw new RuntimeException("Indexing failed", e);
        }
    }

    /**
     * Search for similar knowledge items
     */
    public List<SearchResult> search(String query, int limit) {
        return search(query, limit, null, null);
    }

    /**
     * Search for similar knowledge items with filters
     */
    public List<SearchResult> search(String query, int limit, String projectId, KnowledgeItem.KnowledgeType type) {
        try {
            log.debug("Searching for: '{}' (limit: {}, project: {}, type: {})",
                    truncate(query, 50), limit, projectId, type);

            // Generate embedding for the query
            List<Float> queryEmbedding = embeddingService.embed(query);

            // Search in vector database
            String typeFilter = type != null ? type.name() : null;
            List<SearchResult> results = vectorRepository.search(queryEmbedding, limit, projectId, typeFilter);

            log.info("Found {} results for query: '{}'", results.size(), truncate(query, 50));
            return results;
        } catch (IOException e) {
            log.error("Search failed for query: '{}'", query, e);
            throw new RuntimeException("Search failed", e);
        }
    }

    /**
     * Search for tasks specifically
     */
    public List<SearchResult> searchTasks(String query, int limit, String projectId) {
        return search(query, limit, projectId, KnowledgeItem.KnowledgeType.TASK);
    }

    /**
     * Search for facts/decisions (knowledge)
     */
    public List<SearchResult> searchKnowledge(String query, int limit, String projectId) {
        // Search for FACT, DECISION, NOTE types
        try {
            List<Float> queryEmbedding = embeddingService.embed(query);

            // Get results without type filter, then filter manually for multiple types
            List<SearchResult> allResults = vectorRepository.search(queryEmbedding, limit * 3, projectId, null);

            return allResults.stream()
                    .filter(r -> {
                        String type = r.payload().get("type");
                        return "FACT".equals(type) || "DECISION".equals(type) || "NOTE".equals(type);
                    })
                    .limit(limit)
                    .toList();
        } catch (IOException e) {
            log.error("Knowledge search failed", e);
            throw new RuntimeException("Search failed", e);
        }
    }

    /**
     * Remove a knowledge item from the index
     */
    public void remove(String itemId) {
        log.debug("Removing from index: {}", itemId);
        vectorRepository.delete(itemId);
        log.info("Removed from index: {}", itemId);
    }

    /**
     * Re-index a knowledge item (update)
     */
    public void reindex(KnowledgeItem item) {
        log.debug("Re-indexing knowledge item: {}", item.getId());
        index(item); // Upsert will handle the update
    }

    private String truncate(String text, int maxLength) {
        if (text == null) return "";
        return text.length() > maxLength ? text.substring(0, maxLength) + "..." : text;
    }
}
