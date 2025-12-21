package com.mindnest.agent.handler;

import com.mindnest.agent.ChunkIntent;
import com.mindnest.agent.ChunkResult;
import com.mindnest.agent.ToolExecutor;
import com.mindnest.agent.UserContextBuilder;
import com.mindnest.service.GraphService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Handles SEARCH intent - searches knowledge base with graph expansion.
 */
@Component
@RequiredArgsConstructor
@Slf4j
public class SearchIntentHandler implements IntentHandler {

    private final ToolExecutor toolExecutor;
    private final GraphService graphService;
    private final UserContextBuilder userContextBuilder;

    @Override
    public String getIntentType() {
        return "SEARCH";
    }

    @Override
    public ChunkResult execute(ChunkIntent intent, String projectId, String userId) {
        String query = intent.searchQuery() != null ? intent.searchQuery() : intent.content();

        // Step 1: Semantic search to find seed nodes
        Map<String, Object> args = new HashMap<>();
        args.put("query", query);
        args.put("limit", 10);

        String tool = "TASK".equals(intent.type()) ? "search_tasks" : "search_knowledge";
        String searchResult = toolExecutor.execute(tool, args, projectId, null);

        // Step 2: Extract IDs from search results and expand graph
        List<String> seedIds = toolExecutor.getLastSearchIds();
        if (seedIds != null && !seedIds.isEmpty()) {
            // Expand graph with proper depth per relation type
            GraphService.GraphContext graphContext = graphService.expandGraph(seedIds, 50);

            // Build userId -> userName map for showing who added each item
            Map<String, String> userIdToName = userContextBuilder.buildUserIdToNameMap(projectId);

            // Serialize graph for LLM with user names
            String graphText = graphService.serializeForLLM(graphContext, userIdToName);
            log.debug("Expanded graph for search:\n{}", graphText);

            // Build user context for LLM
            String userContext = userContextBuilder.buildUserContext(userId, projectId);

            return ChunkResult.search(graphText + "\n\n" + userContext);
        }

        return ChunkResult.search(searchResult);
    }
}
