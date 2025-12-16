package com.mindnest.model.dto;

import com.mindnest.model.entity.ProjectMember;
import com.mindnest.model.entity.User;
import lombok.Builder;
import lombok.Data;

import java.time.Instant;
import java.util.UUID;

@Data
@Builder
public class MemberResponse {
    private UUID id;
    private UUID userId;
    private String email;
    private String name;
    private String role;
    private Instant joinedAt;

    public static MemberResponse from(ProjectMember member, User user) {
        return MemberResponse.builder()
                .id(member.getId())
                .userId(member.getUserId())
                .email(user != null ? user.getEmail() : null)
                .name(user != null ? user.getName() : null)
                .role(member.getRole().name())
                .joinedAt(member.getJoinedAt())
                .build();
    }
}
