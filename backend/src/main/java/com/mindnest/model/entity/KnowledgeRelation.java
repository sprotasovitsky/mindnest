package com.mindnest.model.entity;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.Builder;
import org.springframework.data.neo4j.core.schema.RelationshipId;
import org.springframework.data.neo4j.core.schema.RelationshipProperties;
import org.springframework.data.neo4j.core.schema.TargetNode;

import java.time.Instant;

@RelationshipProperties
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class KnowledgeRelation {

    @RelationshipId
    private Long id;

    private RelationType type;

    private String description;

    private Double weight;

    private Instant createdAt;

    @TargetNode
    private KnowledgeItem target;

    public enum RelationType {
        RELATES_TO,       // Generic relation
        DEPENDS_ON,       // Task dependency
        SUBTASK_OF,       // Subtask relationship
        SUPPORTS,         // Evidence/support relation
        CONTRADICTS,      // Conflicting information
        REFERENCES,       // Citation/reference
        DERIVED_FROM,     // Derived knowledge
        SIMILAR_TO        // Semantic similarity
    }
}
