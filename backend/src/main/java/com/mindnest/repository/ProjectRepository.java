package com.mindnest.repository;

import com.mindnest.model.entity.Project;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface ProjectRepository extends JpaRepository<Project, UUID> {
    List<Project> findByOwnerId(UUID ownerId);

    @Query("SELECT p FROM Project p WHERE p.id IN :projectIds ORDER BY p.createdAt DESC")
    List<Project> findByIdIn(List<UUID> projectIds);

    @Query("SELECT p FROM Project p JOIN ProjectMember pm ON p.id = pm.projectId WHERE pm.userId = :userId ORDER BY p.createdAt DESC")
    List<Project> findProjectsByMembership(UUID userId);
}
