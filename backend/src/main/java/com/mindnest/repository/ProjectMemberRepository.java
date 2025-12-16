package com.mindnest.repository;

import com.mindnest.model.entity.ProjectMember;
import com.mindnest.model.entity.ProjectMember.ProjectRole;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface ProjectMemberRepository extends JpaRepository<ProjectMember, UUID> {

    List<ProjectMember> findByUserId(UUID userId);

    List<ProjectMember> findByProjectId(UUID projectId);

    Optional<ProjectMember> findByProjectIdAndUserId(UUID projectId, UUID userId);

    boolean existsByProjectIdAndUserId(UUID projectId, UUID userId);

    void deleteByProjectIdAndUserId(UUID projectId, UUID userId);

    void deleteByProjectId(UUID projectId);

    @Query("SELECT pm.projectId FROM ProjectMember pm WHERE pm.userId = :userId")
    List<UUID> findProjectIdsByUserId(UUID userId);

    @Query("SELECT pm FROM ProjectMember pm WHERE pm.projectId = :projectId AND pm.role = :role")
    List<ProjectMember> findByProjectIdAndRole(UUID projectId, ProjectRole role);
}
