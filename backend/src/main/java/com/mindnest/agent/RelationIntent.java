package com.mindnest.agent;

/**
 * Intent to create a relation between knowledge items.
 * Extracted during intent detection when user mentions links.
 */
public record RelationIntent(
        String toQuery,          // Search query to find target
        String type              // SUPERSEDES, CONTRADICTS, BELONGS_TO, etc.
) {}
