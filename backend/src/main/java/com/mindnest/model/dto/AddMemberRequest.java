package com.mindnest.model.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class AddMemberRequest {
    @NotBlank(message = "Email is required")
    @Email(message = "Valid email is required")
    private String email;
}
