package com.mindnest.repository;

import com.mindnest.model.entity.Conversation;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface ConversationRepository extends JpaRepository<Conversation, UUID> {

    List<Conversation> findByUserIdOrderByUpdatedAtDesc(UUID userId);

    List<Conversation> findByProjectIdOrderByUpdatedAtDesc(UUID projectId);

    List<Conversation> findByUserIdAndProjectIdOrderByUpdatedAtDesc(UUID userId, UUID projectId);

    @Query("SELECT c FROM Conversation c LEFT JOIN FETCH c.messages WHERE c.id = :id")
    Optional<Conversation> findByIdWithMessages(UUID id);

    @Query("SELECT c FROM Conversation c WHERE c.userId = :userId AND c.projectId = :projectId ORDER BY c.updatedAt DESC LIMIT 1")
    Optional<Conversation> findLatestByUserAndProject(UUID userId, UUID projectId);
}
