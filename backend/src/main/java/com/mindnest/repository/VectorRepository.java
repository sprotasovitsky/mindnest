package com.mindnest.repository;

import io.qdrant.client.QdrantClient;
import io.qdrant.client.grpc.Collections;
import io.qdrant.client.grpc.Points;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Repository;

import jakarta.annotation.PostConstruct;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ExecutionException;
import java.util.stream.Collectors;

import static io.qdrant.client.PointIdFactory.id;
import static io.qdrant.client.ValueFactory.value;
import static io.qdrant.client.VectorsFactory.vectors;
import static io.qdrant.client.WithPayloadSelectorFactory.enable;
import static io.qdrant.client.ConditionFactory.matchKeyword;

@Repository
@RequiredArgsConstructor
@Slf4j
public class VectorRepository {

    private static final int VECTOR_SIZE = 768; // text-embedding-004 dimension

    private final QdrantClient qdrantClient;

    @Qualifier("qdrantCollectionName")
    private final String collectionName;

    @PostConstruct
    public void init() {
        try {
            ensureCollectionExists();
        } catch (Exception e) {
            log.error("Failed to initialize Qdrant collection", e);
        }
    }

    private void ensureCollectionExists() throws ExecutionException, InterruptedException {
        // Check if collection exists by listing all collections
        var collections = qdrantClient.listCollectionsAsync().get();
        boolean exists = collections.stream()
                .anyMatch(name -> name.equals(collectionName));

        if (!exists) {
            log.info("Creating Qdrant collection: {}", collectionName);
            qdrantClient.createCollectionAsync(
                    collectionName,
                    Collections.VectorParams.newBuilder()
                            .setSize(VECTOR_SIZE)
                            .setDistance(Collections.Distance.Cosine)
                            .build()
            ).get();
            log.info("Collection {} created successfully", collectionName);
        } else {
            log.info("Qdrant collection {} already exists", collectionName);
        }
    }

    /**
     * Store a vector with associated metadata
     */
    public void upsert(String id, List<Float> vector, Map<String, String> metadata) {
        try {
            Points.PointStruct.Builder pointBuilder = Points.PointStruct.newBuilder()
                    .setId(id(UUID.fromString(id)))
                    .setVectors(vectors(vector));

            // Add metadata as payload
            metadata.forEach((key, val) ->
                    pointBuilder.putPayload(key, value(val)));

            qdrantClient.upsertAsync(
                    collectionName,
                    List.of(pointBuilder.build())
            ).get();

            log.debug("Upserted vector for id: {}", id);
        } catch (Exception e) {
            log.error("Failed to upsert vector for id: {}", id, e);
            throw new RuntimeException("Vector upsert failed", e);
        }
    }

    /**
     * Search for similar vectors
     */
    public List<SearchResult> search(List<Float> queryVector, int limit) {
        return search(queryVector, limit, null, null);
    }

    /**
     * Search for similar vectors with optional filters
     */
    public List<SearchResult> search(List<Float> queryVector, int limit, String projectId, String type) {
        try {
            Points.SearchPoints.Builder searchBuilder = Points.SearchPoints.newBuilder()
                    .setCollectionName(collectionName)
                    .addAllVector(queryVector)
                    .setLimit(limit)
                    .setWithPayload(enable(true));

            // Add filters if provided
            if (projectId != null || type != null) {
                Points.Filter.Builder filterBuilder = Points.Filter.newBuilder();
                if (projectId != null) {
                    filterBuilder.addMust(matchKeyword("projectId", projectId));
                }
                if (type != null) {
                    filterBuilder.addMust(matchKeyword("type", type));
                }
                searchBuilder.setFilter(filterBuilder.build());
            }

            List<Points.ScoredPoint> results = qdrantClient.searchAsync(searchBuilder.build()).get();

            return results.stream()
                    .map(this::toSearchResult)
                    .collect(Collectors.toList());

        } catch (Exception e) {
            log.error("Vector search failed", e);
            throw new RuntimeException("Vector search failed", e);
        }
    }

    /**
     * Delete a vector by ID
     */
    public void delete(String id) {
        try {
            qdrantClient.deleteAsync(
                    collectionName,
                    List.of(id(UUID.fromString(id)))
            ).get();
            log.debug("Deleted vector for id: {}", id);
        } catch (Exception e) {
            log.error("Failed to delete vector for id: {}", id, e);
            throw new RuntimeException("Vector delete failed", e);
        }
    }

    private SearchResult toSearchResult(Points.ScoredPoint point) {
        String pointId = point.getId().getUuid();
        float score = point.getScore();

        Map<String, String> payload = point.getPayloadMap().entrySet().stream()
                .collect(Collectors.toMap(
                        Map.Entry::getKey,
                        e -> e.getValue().getStringValue()
                ));

        return new SearchResult(pointId, score, payload);
    }

    public record SearchResult(
            String id,
            float score,
            Map<String, String> payload
    ) {}
}
