package com.mindnest.repository;

import com.mindnest.model.entity.KnowledgeItem;
import com.mindnest.model.entity.KnowledgeItem.KnowledgeType;
import com.mindnest.model.entity.KnowledgeItem.TaskStatus;
import org.springframework.data.neo4j.repository.Neo4jRepository;
import org.springframework.data.neo4j.repository.query.Query;
import org.springframework.stereotype.Repository;

import java.time.LocalDate;
import java.util.List;

@Repository
public interface KnowledgeRepository extends Neo4jRepository<KnowledgeItem, String> {

    // Active items only (soft-delete aware)
    List<KnowledgeItem> findByProjectIdAndDeletedAtIsNull(String projectId);

    List<KnowledgeItem> findByTypeAndDeletedAtIsNull(KnowledgeType type);

    List<KnowledgeItem> findByTypeAndStatusAndDeletedAtIsNull(KnowledgeType type, TaskStatus status);

    List<KnowledgeItem> findByProjectIdAndTypeAndDeletedAtIsNull(String projectId, KnowledgeType type);

    List<KnowledgeItem> findByProjectIdAndTypeAndStatusAndDeletedAtIsNull(String projectId, KnowledgeType type, TaskStatus status);

    List<KnowledgeItem> findByOwnerIdAndDeletedAtIsNull(String ownerId);

    List<KnowledgeItem> findByOwnerIdAndTypeAndDeletedAtIsNull(String ownerId, KnowledgeType type);

    // Legacy methods (include deleted items)
    List<KnowledgeItem> findByProjectId(String projectId);

    List<KnowledgeItem> findByType(KnowledgeType type);

    List<KnowledgeItem> findByTypeAndStatus(KnowledgeType type, TaskStatus status);

    List<KnowledgeItem> findByProjectIdAndType(String projectId, KnowledgeType type);

    List<KnowledgeItem> findByProjectIdAndTypeAndStatus(String projectId, KnowledgeType type, TaskStatus status);

    List<KnowledgeItem> findByOwnerId(String ownerId);

    List<KnowledgeItem> findByOwnerIdAndType(String ownerId, KnowledgeType type);

    @Query("MATCH (k:KnowledgeItem {id: $id})-[r*1..$depth]-(related:KnowledgeItem) RETURN DISTINCT related")
    List<KnowledgeItem> findRelated(String id, int depth);

    @Query("MATCH (k:KnowledgeItem) WHERE k.type = 'TASK' AND k.status IN ['TODO', 'IN_PROGRESS'] AND k.deadline <= date() AND k.deletedAt IS NULL RETURN k")
    List<KnowledgeItem> findOverdueTasks();

    @Query("MATCH (k:KnowledgeItem) WHERE k.type = 'TASK' AND k.projectId = $projectId AND k.deadline = $deadline AND k.deletedAt IS NULL RETURN k")
    List<KnowledgeItem> findTasksByDeadline(String projectId, LocalDate deadline);

    @Query("MATCH (k:KnowledgeItem) WHERE k.type = 'TASK' AND k.ownerId = $ownerId AND k.deadline = $deadline AND k.deletedAt IS NULL RETURN k")
    List<KnowledgeItem> findTasksByOwnerAndDeadline(String ownerId, LocalDate deadline);

    @Query("MATCH (k:KnowledgeItem) WHERE k.type = 'TASK' AND k.ownerId = $ownerId AND k.status IN ['TODO', 'IN_PROGRESS'] AND k.deletedAt IS NULL RETURN k ORDER BY k.deadline")
    List<KnowledgeItem> findActiveTasksByOwner(String ownerId);

    // Find tasks by assignee (person name in assignee field or content)
    @Query("MATCH (k:KnowledgeItem) WHERE k.type = 'TASK' AND k.projectId = $projectId AND k.status IN ['TODO', 'IN_PROGRESS'] AND k.deletedAt IS NULL AND (toLower(k.assignee) CONTAINS toLower($assignee) OR toLower(k.content) CONTAINS toLower($assignee)) RETURN k")
    List<KnowledgeItem> findActiveTasksByAssignee(String projectId, String assignee);

    // Find all items (any type) by owner (who created them)
    @Query("MATCH (k:KnowledgeItem) WHERE k.projectId = $projectId AND k.ownerId = $ownerId AND k.deletedAt IS NULL RETURN k ORDER BY k.createdAt DESC")
    List<KnowledgeItem> findByProjectIdAndOwnerIdAndDeletedAtIsNull(String projectId, String ownerId);

    // Find active tasks where user is either owner or assignee (for "my tasks" queries)
    @Query("MATCH (k:KnowledgeItem) WHERE k.type = 'TASK' AND k.projectId = $projectId AND k.status IN ['TODO', 'IN_PROGRESS'] AND k.deletedAt IS NULL AND (k.ownerId = $userId OR toLower(k.assignee) CONTAINS toLower($userName)) RETURN k ORDER BY k.deadline")
    List<KnowledgeItem> findActiveTasksForUser(String projectId, String userId, String userName);

    // Relation creation methods - each with proper Neo4j relationship type
    // SUPERSEDES: new item replaces old (for updates, deletes, task completion)
    @Query("MATCH (source:KnowledgeItem {id: $sourceId}), (target:KnowledgeItem {id: $targetId}) " +
           "CREATE (source)-[r:SUPERSEDES {description: $description, weight: $weight, createdAt: datetime()}]->(target) " +
           "RETURN source")
    KnowledgeItem createSupersedes(String sourceId, String targetId, String description, Double weight);

    // CONTRADICTS: items cancel out (refunds cancel purchases)
    @Query("MATCH (source:KnowledgeItem {id: $sourceId}), (target:KnowledgeItem {id: $targetId}) " +
           "CREATE (source)-[r:CONTRADICTS {description: $description, weight: $weight, createdAt: datetime()}]->(target) " +
           "RETURN source")
    KnowledgeItem createContradicts(String sourceId, String targetId, String description, Double weight);

    // BELONGS_TO: item belongs to category/group
    @Query("MATCH (source:KnowledgeItem {id: $sourceId}), (target:KnowledgeItem {id: $targetId}) " +
           "CREATE (source)-[r:BELONGS_TO {description: $description, weight: $weight, createdAt: datetime()}]->(target) " +
           "RETURN source")
    KnowledgeItem createBelongsTo(String sourceId, String targetId, String description, Double weight);

    // ASSIGNED_TO: task assigned to person
    @Query("MATCH (source:KnowledgeItem {id: $sourceId}), (target:KnowledgeItem {id: $targetId}) " +
           "CREATE (source)-[r:ASSIGNED_TO {description: $description, weight: $weight, createdAt: datetime()}]->(target) " +
           "RETURN source")
    KnowledgeItem createAssignedTo(String sourceId, String targetId, String description, Double weight);

    // DEPENDS_ON: item depends on another
    @Query("MATCH (source:KnowledgeItem {id: $sourceId}), (target:KnowledgeItem {id: $targetId}) " +
           "CREATE (source)-[r:DEPENDS_ON {description: $description, weight: $weight, createdAt: datetime()}]->(target) " +
           "RETURN source")
    KnowledgeItem createDependsOn(String sourceId, String targetId, String description, Double weight);

    // RELATES_TO: general relation (default)
    @Query("MATCH (source:KnowledgeItem {id: $sourceId}), (target:KnowledgeItem {id: $targetId}) " +
           "CREATE (source)-[r:RELATES_TO {description: $description, weight: $weight, createdAt: datetime()}]->(target) " +
           "RETURN source")
    KnowledgeItem createRelatesTo(String sourceId, String targetId, String description, Double weight);

    // SUPPORTS: item supports/reinforces another
    @Query("MATCH (source:KnowledgeItem {id: $sourceId}), (target:KnowledgeItem {id: $targetId}) " +
           "CREATE (source)-[r:SUPPORTS {description: $description, weight: $weight, createdAt: datetime()}]->(target) " +
           "RETURN source")
    KnowledgeItem createSupports(String sourceId, String targetId, String description, Double weight);

    // SIMILAR_TO: items are similar
    @Query("MATCH (source:KnowledgeItem {id: $sourceId}), (target:KnowledgeItem {id: $targetId}) " +
           "CREATE (source)-[r:SIMILAR_TO {description: $description, weight: $weight, createdAt: datetime()}]->(target) " +
           "RETURN source")
    KnowledgeItem createSimilarTo(String sourceId, String targetId, String description, Double weight);

    // SUBTASK_OF: subtask of parent task (legacy, prefer PART_OF)
    @Query("MATCH (source:KnowledgeItem {id: $sourceId}), (target:KnowledgeItem {id: $targetId}) " +
           "CREATE (source)-[r:SUBTASK_OF {description: $description, weight: $weight, createdAt: datetime()}]->(target) " +
           "RETURN source")
    KnowledgeItem createSubtaskOf(String sourceId, String targetId, String description, Double weight);

    // PART_OF: item is part of another (sprint part of project, etc.)
    @Query("MATCH (source:KnowledgeItem {id: $sourceId}), (target:KnowledgeItem {id: $targetId}) " +
           "CREATE (source)-[r:PART_OF {description: $description, weight: $weight, createdAt: datetime()}]->(target) " +
           "RETURN source")
    KnowledgeItem createPartOf(String sourceId, String targetId, String description, Double weight);

    // CONTAINS: parent contains child (recipe contains ingredient)
    @Query("MATCH (source:KnowledgeItem {id: $sourceId}), (target:KnowledgeItem {id: $targetId}) " +
           "CREATE (source)-[r:CONTAINS {description: $description, weight: $weight, createdAt: datetime()}]->(target) " +
           "RETURN source")
    KnowledgeItem createContains(String sourceId, String targetId, String description, Double weight);

    // Delete relations (all types)
    @Query("MATCH (source:KnowledgeItem {id: $sourceId})-[r]->(target:KnowledgeItem {id: $targetId}) DELETE r")
    void deleteRelation(String sourceId, String targetId);

    // Find relations (all types)
    @Query("MATCH (k:KnowledgeItem {id: $id})-[r]->(related:KnowledgeItem) RETURN related, r")
    List<KnowledgeItem> findDirectRelations(String id);

    @Query("MATCH (k:KnowledgeItem {id: $id})<-[r]-(related:KnowledgeItem) RETURN related, r")
    List<KnowledgeItem> findIncomingRelations(String id);

    @Query("MATCH path = (source:KnowledgeItem {id: $sourceId})-[*1..$maxDepth]-(target:KnowledgeItem {id: $targetId}) " +
           "RETURN path LIMIT 1")
    List<KnowledgeItem> findPath(String sourceId, String targetId, int maxDepth);

    @Query("MATCH (k:KnowledgeItem {id: $id}) " +
           "OPTIONAL MATCH (k)-[r]->(related:KnowledgeItem) " +
           "RETURN k, collect(r), collect(related)")
    KnowledgeItem findByIdWithRelations(String id);

    // Check if task already has a [DONE] marker (someone already SUPERSEDES it with status=DONE)
    @Query("MATCH (done:KnowledgeItem)-[:SUPERSEDES]->(task:KnowledgeItem {id: $taskId}) " +
           "WHERE done.status = 'DONE' " +
           "RETURN count(done) > 0")
    boolean hasCompletionMarker(String taskId);
}
