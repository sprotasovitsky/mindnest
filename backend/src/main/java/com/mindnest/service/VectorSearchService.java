package com.mindnest.service;

import com.mindnest.model.entity.KnowledgeItem;
import com.mindnest.repository.VectorRepository;
import com.mindnest.repository.VectorRepository.SearchResult;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.Comparator;
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

    @Value("${agent.recency.max-boost}")
    private double maxRecencyBoost;

    @Value("${agent.recency.decay-days}")
    private double recencyDecayDays;

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
            if (item.getCreatedAt() != null) {
                metadata.put("createdAt", String.valueOf(item.getCreatedAt().toEpochMilli()));
            }
            // Add amount and currency for expense calculations
            if (item.getAmount() != null) {
                metadata.put("amount", item.getAmount().toString());
            }
            if (item.getCurrency() != null) {
                metadata.put("currency", item.getCurrency());
            }
            // Add assignee for task filtering
            if (item.getAssignee() != null) {
                metadata.put("assignee", item.getAssignee());
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
     * Search for all knowledge types including tasks.
     * Applies recency boost to prioritize recent items when similarity is close.
     */
    public List<SearchResult> searchKnowledge(String query, int limit, String projectId) {
        // Search for all types: FACT, DECISION, NOTE, TASK, QUESTION
        try {
            List<Float> queryEmbedding = embeddingService.embed(query);

            // Get all results - no type filtering
            List<SearchResult> allResults = vectorRepository.search(queryEmbedding, limit * 2, projectId, null);

            // Apply recency boost and re-sort
            List<SearchResult> boostedResults = allResults.stream()
                    .map(this::applyRecencyBoost)
                    .sorted(Comparator.comparingDouble(SearchResult::score).reversed())
                    .limit(limit)
                    .toList();

            log.debug("Search '{}' returned {} results (with recency boost)", truncate(query, 30), boostedResults.size());
            return boostedResults;
        } catch (IOException e) {
            log.error("Knowledge search failed", e);
            throw new RuntimeException("Search failed", e);
        }
    }

    /**
     * Apply recency boost to a search result.
     * Items created recently get up to maxRecencyBoost (configurable).
     * The boost decays linearly over recencyDecayDays (configurable).
     */
    private SearchResult applyRecencyBoost(SearchResult result) {
        String createdAtStr = (String) result.payload().get("createdAt");
        if (createdAtStr == null) {
            return result; // No timestamp, no boost
        }

        try {
            long createdAtMillis = Long.parseLong(createdAtStr);
            Instant createdAt = Instant.ofEpochMilli(createdAtMillis);
            long ageInDays = ChronoUnit.DAYS.between(createdAt, Instant.now());

            // Recency boost: decays linearly over configured days
            double recencyBoost = Math.max(0, (recencyDecayDays - ageInDays) / recencyDecayDays * maxRecencyBoost);

            double boostedScore = result.score() * (1 + recencyBoost);

            // Create new result with boosted score
            return new SearchResult(result.id(), (float) boostedScore, result.payload());
        } catch (NumberFormatException e) {
            log.warn("Invalid createdAt timestamp: {}", createdAtStr);
            return result;
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
