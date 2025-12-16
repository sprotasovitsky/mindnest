package com.mindnest.security;

import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;

import java.util.Optional;
import java.util.UUID;

public final class SecurityUtils {

    private SecurityUtils() {}

    public static Optional<UserPrincipal> getCurrentUser() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        if (authentication != null && authentication.getPrincipal() instanceof UserPrincipal principal) {
            return Optional.of(principal);
        }
        return Optional.empty();
    }

    public static UUID getCurrentUserId() {
        return getCurrentUser()
                .map(UserPrincipal::userId)
                .orElseThrow(() -> new IllegalStateException("No authenticated user"));
    }

    public static String getCurrentUserEmail() {
        return getCurrentUser()
                .map(UserPrincipal::email)
                .orElseThrow(() -> new IllegalStateException("No authenticated user"));
    }
}
