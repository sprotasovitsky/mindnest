package com.mindnest.agent.handler;

import com.mindnest.agent.ChunkIntent;
import com.mindnest.agent.ChunkResult;
import org.springframework.stereotype.Component;

/**
 * Handles CHAT intent - general conversation without tool execution.
 */
@Component
public class ChatIntentHandler implements IntentHandler {

    @Override
    public String getIntentType() {
        return "CHAT";
    }

    @Override
    public ChunkResult execute(ChunkIntent intent, String projectId, String userId) {
        return ChunkResult.chat();
    }
}
