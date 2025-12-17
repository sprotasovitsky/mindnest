package com.mindnest.model.entity;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.Builder;
import org.springframework.data.neo4j.core.schema.Id;
import org.springframework.data.neo4j.core.schema.Node;
import org.springframework.data.neo4j.core.schema.GeneratedValue;
import org.springframework.data.neo4j.core.schema.Relationship;
import org.springframework.data.neo4j.core.support.UUIDStringGenerator;

import java.math.BigDecimal;
import java.time.Instant;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

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

    private String subtype;  // For KNOWLEDGE: "fact", "note", "decision", "recipe", etc.

    private String content;

    private TaskStatus status;  // for tasks

    private LocalDate deadline;  // for tasks

    private String assignee;  // Person name/id for tasks

    private BigDecimal amount;  // For EXPENSE type

    private String currency;  // "RUB", "USD", "EUR", etc.

    private Instant eventDate;  // For EVENT type

    private String ownerId;

    private String projectId;

    private Instant createdAt;

    private Instant updatedAt;

    private Instant deletedAt;  // Soft-delete: null = active, non-null = deleted

    @Relationship(type = "RELATES_TO", direction = Relationship.Direction.OUTGOING)
    @Builder.Default
    private List<KnowledgeRelation> relations = new ArrayList<>();

    public enum KnowledgeType {
        // Core types
        KNOWLEDGE,    // Generic: facts, notes, decisions, recipes, etc. (use subtype for specifics)
        TASK,         // With status lifecycle
        EXPENSE,      // With amount for calculations
        PERSON,       // Can be assignee, payer, voter
        PROJECT,      // Container
        EVENT,        // With date/time
        CATEGORY,     // For grouping

        // Legacy types (kept for backward compatibility)
        FACT,
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
