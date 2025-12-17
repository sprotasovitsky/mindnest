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
        // Versioning
        SUPERSEDES,       // New version replaces old: v2 -[SUPERSEDES]-> v1
        CONTRADICTS,      // Cancels/refunds: return -[CONTRADICTS]-> purchase

        // Hierarchy
        BELONGS_TO,       // Category, project membership
        CONTAINS,         // Recipe contains ingredient, box contains item
        PART_OF,          // Sprint part of project

        // Assignment
        ASSIGNED_TO,      // Task -> Person
        CREATED_BY,       // Item -> Person (owner)
        PAID_BY,          // Expense -> Person

        // Dependencies
        DEPENDS_ON,       // Task depends on task
        BLOCKS,           // Inverse of DEPENDS_ON (computed)

        // Semantic
        RELATES_TO,       // Generic relation
        SUPPORTS,         // Evidence for decision
        SIMILAR_TO,       // Auto-linked by embeddings

        // Discussion
        MENTIONED_IN,     // Referenced in conversation
        VOTED_FOR,        // Person voted for option

        // Legacy (kept for backward compatibility)
        SUBTASK_OF,       // Subtask relationship (use PART_OF instead)
        REFERENCES,       // Citation/reference
        DERIVED_FROM      // Derived knowledge
    }
}
