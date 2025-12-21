package com.mindnest.service;

import com.mindnest.model.entity.KnowledgeItem;
import com.mindnest.model.entity.KnowledgeRelation;
import com.mindnest.model.entity.KnowledgeRelation.RelationType;
import com.mindnest.repository.KnowledgeRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.*;

/**
 * Service for graph operations: expansion and serialization for LLM.
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class GraphService {

    private final KnowledgeRepository knowledgeRepository;

    // Relations that require full chain traversal
    private static final Set<RelationType> CHAIN_RELATIONS = Set.of(
            RelationType.SUPERSEDES,
            RelationType.CONTRADICTS,
            RelationType.DEPENDS_ON,
            RelationType.BLOCKS
    );

    // Relations that only need 1 level
    private static final Set<RelationType> SINGLE_LEVEL_RELATIONS = Set.of(
            RelationType.BELONGS_TO,
            RelationType.CONTAINS,
            RelationType.PART_OF,
            RelationType.ASSIGNED_TO,
            RelationType.CREATED_BY,
            RelationType.PAID_BY,
            RelationType.RELATES_TO,
            RelationType.SUPPORTS,
            RelationType.SIMILAR_TO,
            RelationType.MENTIONED_IN,
            RelationType.VOTED_FOR
    );

    /**
     * Expand graph from seed nodes, following relations with appropriate depth.
     * - Chain relations (SUPERSEDES, CONTRADICTS, DEPENDS_ON): follow to end
     * - Single level relations: only 1 hop
     *
     * @param seedIds IDs of nodes found by semantic search
     * @param maxNodes Maximum nodes to return (prevent explosion)
     * @return Expanded set of nodes with their relations
     */
    public GraphContext expandGraph(List<String> seedIds, int maxNodes) {
        log.debug("Expanding graph from {} seed nodes, max {}", seedIds.size(), maxNodes);

        Map<String, KnowledgeItem> nodes = new LinkedHashMap<>();
        Set<RelationEdge> edges = new HashSet<>();
        Set<String> visited = new HashSet<>();
        Queue<ExpansionTask> queue = new LinkedList<>();

        // Start with seed nodes
        for (String id : seedIds) {
            if (nodes.size() >= maxNodes) break;

            KnowledgeItem item = knowledgeRepository.findByIdWithRelations(id);
            if (item != null && item.getDeletedAt() == null) {
                nodes.put(id, item);
                // Queue expansion for all relation types
                queue.add(new ExpansionTask(id, null, 0));
            }
        }

        // BFS expansion
        while (!queue.isEmpty() && nodes.size() < maxNodes) {
            ExpansionTask task = queue.poll();
            if (visited.contains(task.nodeId + ":" + task.relationType)) continue;
            visited.add(task.nodeId + ":" + task.relationType);

            KnowledgeItem item = nodes.containsKey(task.nodeId)
                    ? nodes.get(task.nodeId)
                    : knowledgeRepository.findByIdWithRelations(task.nodeId);

            if (item == null || item.getDeletedAt() != null) continue;

            // Add to nodes if not present
            if (!nodes.containsKey(task.nodeId)) {
                nodes.put(task.nodeId, item);
            }

            // Process outgoing relations
            if (item.getRelations() != null) {
                for (KnowledgeRelation rel : item.getRelations()) {
                    if (rel.getTarget() == null) continue;

                    RelationType relType = rel.getType();
                    if (relType == null) continue;  // Skip relations with null type

                    String targetId = rel.getTarget().getId();

                    // Add edge
                    edges.add(new RelationEdge(task.nodeId, targetId, relType, false));

                    // Decide whether to expand further
                    if (CHAIN_RELATIONS.contains(relType)) {
                        // Follow chain relations to the end
                        if (!visited.contains(targetId + ":" + relType)) {
                            queue.add(new ExpansionTask(targetId, relType, task.depth + 1));
                        }
                    } else if (SINGLE_LEVEL_RELATIONS.contains(relType) && task.depth == 0) {
                        // Single level - only from seed nodes
                        if (!nodes.containsKey(targetId) && nodes.size() < maxNodes) {
                            KnowledgeItem target = knowledgeRepository.findById(targetId).orElse(null);
                            if (target != null && target.getDeletedAt() == null) {
                                nodes.put(targetId, target);
                            }
                        }
                    }
                }
            }

            // Also check incoming relations (for SUPERSEDES, CONTRADICTS)
            List<KnowledgeItem> incoming = knowledgeRepository.findIncomingRelations(task.nodeId);
            for (KnowledgeItem source : incoming) {
                if (source.getRelations() == null) continue;

                for (KnowledgeRelation rel : source.getRelations()) {
                    if (rel.getTarget() != null && rel.getTarget().getId().equals(task.nodeId)) {
                        RelationType relType = rel.getType();
                        if (relType == null) continue;  // Skip relations with null type

                        edges.add(new RelationEdge(source.getId(), task.nodeId, relType, true));

                        if (CHAIN_RELATIONS.contains(relType)) {
                            if (!visited.contains(source.getId() + ":" + relType)) {
                                queue.add(new ExpansionTask(source.getId(), relType, task.depth + 1));
                            }
                        }
                    }
                }
            }
        }

        log.debug("Expanded to {} nodes and {} edges", nodes.size(), edges.size());
        return new GraphContext(new ArrayList<>(nodes.values()), new ArrayList<>(edges));
    }

    /**
     * Serialize graph context to text format for LLM.
     */
    public String serializeForLLM(GraphContext context) {
        return serializeForLLM(context, Map.of());
    }

    /**
     * Serialize graph context to text format for LLM with user name mapping.
     * @param context The graph context
     * @param userIdToName Map of userId to userName for showing who created each item
     */
    public String serializeForLLM(GraphContext context, Map<String, String> userIdToName) {
        StringBuilder sb = new StringBuilder();
        sb.append("=== KNOWLEDGE GRAPH ===\n\n");

        Map<String, String> idToLabel = new HashMap<>();
        int counter = 1;

        // Assign short labels to nodes
        for (KnowledgeItem item : context.nodes()) {
            String label = "[N" + counter + "]";
            idToLabel.put(item.getId(), label);
            counter++;
        }

        // Build adjacency info
        Map<String, List<String>> outgoing = new HashMap<>();
        Map<String, List<String>> incoming = new HashMap<>();

        for (RelationEdge edge : context.edges()) {
            String sourceLabel = idToLabel.get(edge.sourceId());
            String targetLabel = idToLabel.get(edge.targetId());

            if (sourceLabel != null && targetLabel != null) {
                String outRel = String.format("→ %s → %s", edge.type(), targetLabel);
                String inRel = String.format("← %s ← %s", edge.type(), sourceLabel);

                outgoing.computeIfAbsent(edge.sourceId(), k -> new ArrayList<>()).add(outRel);
                incoming.computeIfAbsent(edge.targetId(), k -> new ArrayList<>()).add(inRel);
            }
        }

        // Output nodes with their relations
        for (KnowledgeItem item : context.nodes()) {
            String label = idToLabel.get(item.getId());
            String type = item.getType() != null ? item.getType().name() : "UNKNOWN";
            String content = truncate(item.getContent(), 100);

            // Build properties string
            StringBuilder props = new StringBuilder();
            if (item.getAmount() != null) {
                props.append("amount:").append(item.getAmount());
            }
            if (item.getStatus() != null) {
                if (props.length() > 0) props.append(", ");
                props.append("status:").append(item.getStatus());
            }
            if (item.getAssignee() != null) {
                if (props.length() > 0) props.append(", ");
                props.append("assignee:").append(item.getAssignee());
            }
            // Add createdBy (who added this item)
            if (item.getOwnerId() != null && userIdToName.containsKey(item.getOwnerId())) {
                if (props.length() > 0) props.append(", ");
                props.append("addedBy:").append(userIdToName.get(item.getOwnerId()));
            }

            String propsStr = props.length() > 0 ? " {" + props + "}" : "";

            sb.append(String.format("%s %s: \"%s\"%s\n", label, type, content, propsStr));

            // Incoming relations (things that affect this node)
            List<String> inRels = incoming.get(item.getId());
            if (inRels != null) {
                for (String rel : inRels) {
                    sb.append("  ").append(rel).append("\n");
                }
            }

            // Outgoing relations
            List<String> outRels = outgoing.get(item.getId());
            if (outRels != null) {
                for (String rel : outRels) {
                    sb.append("  ").append(rel).append("\n");
                }
            }

            sb.append("\n");
        }

        return sb.toString();
    }

    private String truncate(String text, int maxLen) {
        if (text == null) return "";
        return text.length() > maxLen ? text.substring(0, maxLen) + "..." : text;
    }

    // Helper records
    private record ExpansionTask(String nodeId, RelationType relationType, int depth) {}

    public record RelationEdge(String sourceId, String targetId, RelationType type, boolean isIncoming) {}

    public record GraphContext(List<KnowledgeItem> nodes, List<RelationEdge> edges) {}
}
