package com.mindnest.security;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.time.Instant;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;

@Component
@Slf4j
public class RateLimitingFilter extends OncePerRequestFilter {

    // Rate limit: 60 requests per minute per user/IP
    private static final int REQUESTS_PER_MINUTE = 60;
    private static final long WINDOW_SIZE_MS = 60_000;

    // Simple token bucket implementation
    private final Map<String, RateLimitBucket> buckets = new ConcurrentHashMap<>();

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain filterChain) throws ServletException, IOException {

        // Skip rate limiting for auth endpoints to allow login attempts
        String path = request.getRequestURI();
        if (path.startsWith("/api/auth/") || path.startsWith("/actuator/")) {
            filterChain.doFilter(request, response);
            return;
        }

        String key = resolveKey(request);
        RateLimitBucket bucket = buckets.computeIfAbsent(key, k -> new RateLimitBucket());

        if (bucket.tryConsume()) {
            // Add rate limit headers
            response.setHeader("X-Rate-Limit-Remaining", String.valueOf(bucket.getRemaining()));
            filterChain.doFilter(request, response);
        } else {
            log.warn("Rate limit exceeded for: {}", key);
            response.setStatus(HttpStatus.TOO_MANY_REQUESTS.value());
            response.setContentType("application/json");
            response.getWriter().write("{\"error\": \"Rate limit exceeded. Please try again later.\"}");
        }
    }

    private String resolveKey(HttpServletRequest request) {
        // Try to get user ID from auth token
        String authHeader = request.getHeader("Authorization");
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            // Use part of token as key
            return "token:" + authHeader.substring(7, Math.min(authHeader.length(), 50));
        }

        // Fall back to IP address
        String ip = request.getHeader("X-Forwarded-For");
        if (ip == null || ip.isEmpty()) {
            ip = request.getRemoteAddr();
        }
        return "ip:" + ip;
    }

    private static class RateLimitBucket {
        private final AtomicInteger count = new AtomicInteger(0);
        private volatile long windowStart = Instant.now().toEpochMilli();

        public synchronized boolean tryConsume() {
            long now = Instant.now().toEpochMilli();

            // Reset window if expired
            if (now - windowStart > WINDOW_SIZE_MS) {
                windowStart = now;
                count.set(0);
            }

            if (count.get() < REQUESTS_PER_MINUTE) {
                count.incrementAndGet();
                return true;
            }

            return false;
        }

        public int getRemaining() {
            return Math.max(0, REQUESTS_PER_MINUTE - count.get());
        }
    }
}
