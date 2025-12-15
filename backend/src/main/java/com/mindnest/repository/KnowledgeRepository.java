package com.mindnest.repository;

import com.mindnest.model.entity.KnowledgeItem;
import com.mindnest.model.entity.KnowledgeItem.KnowledgeType;
import com.mindnest.model.entity.KnowledgeItem.TaskStatus;
import org.springframework.data.neo4j.repository.Neo4jRepository;
import org.springframework.data.neo4j.repository.query.Query;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface KnowledgeRepository extends Neo4jRepository<KnowledgeItem, String> {

    List<KnowledgeItem> findByProjectId(String projectId);

    List<KnowledgeItem> findByType(KnowledgeType type);

    List<KnowledgeItem> findByTypeAndStatus(KnowledgeType type, TaskStatus status);

    List<KnowledgeItem> findByProjectIdAndType(String projectId, KnowledgeType type);

    @Query("MATCH (k:KnowledgeItem {id: $id})-[r*1..$depth]-(related:KnowledgeItem) RETURN DISTINCT related")
    List<KnowledgeItem> findRelated(String id, int depth);

    @Query("MATCH (k:KnowledgeItem) WHERE k.type = 'TASK' AND k.status IN ['TODO', 'IN_PROGRESS'] AND k.deadline <= date() RETURN k")
    List<KnowledgeItem> findOverdueTasks();
}
