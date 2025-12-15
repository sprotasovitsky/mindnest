package com.mindnest.model.entity;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.Builder;
import org.springframework.data.neo4j.core.schema.Id;
import org.springframework.data.neo4j.core.schema.Node;
import org.springframework.data.neo4j.core.schema.GeneratedValue;
import org.springframework.data.neo4j.core.support.UUIDStringGenerator;

import java.time.Instant;
import java.time.LocalDate;

@Node("KnowledgeItem")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class KnowledgeItem {

    @Id
    @GeneratedValue(UUIDStringGenerator.class)
    private String id;

    private KnowledgeType type;

    private String content;

    private TaskStatus status;  // for tasks

    private LocalDate deadline;  // for tasks

    private String ownerId;

    private String projectId;

    private Instant createdAt;

    private Instant updatedAt;

    public enum KnowledgeType {
        FACT,
        TASK,
        DECISION,
        NOTE,
        QUESTION
    }

    public enum TaskStatus {
        TODO,
        IN_PROGRESS,
        DONE,
        BLOCKED,
        CANCELLED
    }
}
