package com.mindnest.config;

import io.qdrant.client.QdrantClient;
import io.qdrant.client.QdrantGrpcClient;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
@Slf4j
public class QdrantConfig {

    @Value("${qdrant.host}")
    private String host;

    @Value("${qdrant.port}")
    private int port;

    @Value("${qdrant.collection}")
    private String collectionName;

    @Bean
    public QdrantClient qdrantClient() {
        log.info("Connecting to Qdrant at {}:{}", host, port);
        return new QdrantClient(
                QdrantGrpcClient.newBuilder(host, port, false).build()
        );
    }

    @Bean
    public String qdrantCollectionName() {
        return collectionName;
    }
}
