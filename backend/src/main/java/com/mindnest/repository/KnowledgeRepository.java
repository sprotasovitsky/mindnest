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

    @Query("MATCH (source:KnowledgeItem {id: $sourceId}), (target:KnowledgeItem {id: $targetId}) " +
           "CREATE (source)-[r:RELATES_TO {type: $relationType, description: $description, weight: $weight, createdAt: datetime()}]->(target) " +
           "RETURN source, collect(r), collect(target)")
    KnowledgeItem createRelation(String sourceId, String targetId, String relationType, String description, Double weight);

    @Query("MATCH (source:KnowledgeItem {id: $sourceId})-[r:RELATES_TO]->(target:KnowledgeItem {id: $targetId}) DELETE r")
    void deleteRelation(String sourceId, String targetId);

    @Query("MATCH (k:KnowledgeItem {id: $id})-[r:RELATES_TO]->(related:KnowledgeItem) RETURN related, r")
    List<KnowledgeItem> findDirectRelations(String id);

    @Query("MATCH (k:KnowledgeItem {id: $id})<-[r:RELATES_TO]-(related:KnowledgeItem) RETURN related, r")
    List<KnowledgeItem> findIncomingRelations(String id);

    @Query("MATCH path = (source:KnowledgeItem {id: $sourceId})-[:RELATES_TO*1..$maxDepth]-(target:KnowledgeItem {id: $targetId}) " +
           "RETURN path LIMIT 1")
    List<KnowledgeItem> findPath(String sourceId, String targetId, int maxDepth);

    @Query("MATCH (k:KnowledgeItem {id: $id}) " +
           "OPTIONAL MATCH (k)-[r:RELATES_TO]->(related:KnowledgeItem) " +
           "RETURN k, collect(r), collect(related)")
    KnowledgeItem findByIdWithRelations(String id);
}
