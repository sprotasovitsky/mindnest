package com.mindnest.service;

import com.google.cloud.aiplatform.v1.EndpointName;
import com.google.cloud.aiplatform.v1.PredictResponse;
import com.google.cloud.aiplatform.v1.PredictionServiceClient;
import com.google.cloud.aiplatform.v1.PredictionServiceSettings;
import com.google.protobuf.util.JsonFormat;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

@Service
@Slf4j
public class EmbeddingService {

    @Value("${vertex-ai.project-id}")
    private String projectId;

    @Value("${vertex-ai.location}")
    private String location;

    @Value("${vertex-ai.models.embedding}")
    private String embeddingModel;

    private PredictionServiceClient predictionClient;
    private EndpointName endpointName;

    @PostConstruct
    public void init() throws IOException {
        String endpoint = String.format("%s-aiplatform.googleapis.com:443", location);
        PredictionServiceSettings settings = PredictionServiceSettings.newBuilder()
                .setEndpoint(endpoint)
                .build();
        predictionClient = PredictionServiceClient.create(settings);

        // Endpoint for text embedding models
        endpointName = EndpointName.ofProjectLocationPublisherModelName(
                projectId, location, "google", embeddingModel);

        log.info("EmbeddingService initialized with model: {}", embeddingModel);
    }

    @PreDestroy
    public void shutdown() {
        if (predictionClient != null) {
            predictionClient.close();
        }
    }

    public List<Float> embed(String text) throws IOException {
        log.debug("Embedding text: {} chars", text.length());

        // Build the request
        com.google.protobuf.Value.Builder instanceBuilder = com.google.protobuf.Value.newBuilder();
        JsonFormat.parser().merge(
                String.format("{\"content\": \"%s\"}", escapeJson(text)),
                instanceBuilder
        );

        List<com.google.protobuf.Value> instances = List.of(instanceBuilder.build());

        PredictResponse response = predictionClient.predict(endpointName, instances, com.google.protobuf.Value.getDefaultInstance());

        // Extract embedding from response
        List<Float> embedding = new ArrayList<>();
        if (response.getPredictionsCount() > 0) {
            com.google.protobuf.Value prediction = response.getPredictions(0);
            com.google.protobuf.Value embeddingsValue = prediction.getStructValue()
                    .getFieldsOrThrow("embeddings")
                    .getStructValue()
                    .getFieldsOrThrow("values");

            for (com.google.protobuf.Value v : embeddingsValue.getListValue().getValuesList()) {
                embedding.add((float) v.getNumberValue());
            }
        }

        log.debug("Generated embedding with {} dimensions", embedding.size());
        return embedding;
    }

    public List<List<Float>> embedBatch(List<String> texts) throws IOException {
        log.debug("Embedding batch of {} texts", texts.size());

        List<com.google.protobuf.Value> instances = new ArrayList<>();
        for (String text : texts) {
            com.google.protobuf.Value.Builder instanceBuilder = com.google.protobuf.Value.newBuilder();
            JsonFormat.parser().merge(
                    String.format("{\"content\": \"%s\"}", escapeJson(text)),
                    instanceBuilder
            );
            instances.add(instanceBuilder.build());
        }

        PredictResponse response = predictionClient.predict(endpointName, instances, com.google.protobuf.Value.getDefaultInstance());

        List<List<Float>> embeddings = new ArrayList<>();
        for (com.google.protobuf.Value prediction : response.getPredictionsList()) {
            List<Float> embedding = new ArrayList<>();
            com.google.protobuf.Value embeddingsValue = prediction.getStructValue()
                    .getFieldsOrThrow("embeddings")
                    .getStructValue()
                    .getFieldsOrThrow("values");

            for (com.google.protobuf.Value v : embeddingsValue.getListValue().getValuesList()) {
                embedding.add((float) v.getNumberValue());
            }
            embeddings.add(embedding);
        }

        log.debug("Generated {} embeddings", embeddings.size());
        return embeddings;
    }

    private String escapeJson(String text) {
        return text
                .replace("\\", "\\\\")
                .replace("\"", "\\\"")
                .replace("\n", "\\n")
                .replace("\r", "\\r")
                .replace("\t", "\\t");
    }
}
