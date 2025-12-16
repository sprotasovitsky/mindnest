package com.mindnest.service;

import com.mindnest.model.entity.Conversation;
import com.mindnest.model.entity.Message;
import com.mindnest.repository.ConversationRepository;
import com.mindnest.repository.MessageRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

@Service
@RequiredArgsConstructor
@Slf4j
public class ConversationService {

    private final ConversationRepository conversationRepository;
    private final MessageRepository messageRepository;

    private static final int MAX_CONTEXT_MESSAGES = 20;

    @Transactional
    public Conversation getOrCreateConversation(UUID userId, UUID projectId) {
        return conversationRepository.findLatestByUserAndProject(userId, projectId)
                .orElseGet(() -> {
                    log.info("Creating new conversation for user {} in project {}", userId, projectId);
                    Conversation conversation = Conversation.builder()
                            .userId(userId)
                            .projectId(projectId)
                            .build();
                    return conversationRepository.save(conversation);
                });
    }

    @Transactional
    public Conversation createNewConversation(UUID userId, UUID projectId) {
        log.info("Creating new conversation for user {} in project {}", userId, projectId);
        Conversation conversation = Conversation.builder()
                .userId(userId)
                .projectId(projectId)
                .build();
        return conversationRepository.save(conversation);
    }

    @Transactional
    public Message addMessage(UUID conversationId, Message.Role role, String content, Map<String, Object> metadata) {
        Conversation conversation = conversationRepository.findById(conversationId)
                .orElseThrow(() -> new IllegalArgumentException("Conversation not found: " + conversationId));

        Message message = Message.builder()
                .conversation(conversation)
                .role(role)
                .content(content)
                .metadata(metadata)
                .build();

        return messageRepository.save(message);
    }

    @Transactional(readOnly = true)
    public List<Message> getRecentMessages(UUID conversationId, int limit) {
        return messageRepository.findRecentMessages(
                conversationId,
                PageRequest.of(0, limit)
        );
    }

    @Transactional(readOnly = true)
    public List<Message> getConversationHistory(UUID conversationId) {
        return messageRepository.findByConversationIdOrderByCreatedAtAsc(conversationId);
    }

    @Transactional(readOnly = true)
    public Optional<Conversation> getConversationWithMessages(UUID conversationId) {
        return conversationRepository.findByIdWithMessages(conversationId);
    }

    @Transactional(readOnly = true)
    public List<Conversation> getUserConversations(UUID userId) {
        return conversationRepository.findByUserIdOrderByUpdatedAtDesc(userId);
    }

    @Transactional(readOnly = true)
    public List<Conversation> getProjectConversations(UUID userId, UUID projectId) {
        return conversationRepository.findByUserIdAndProjectIdOrderByUpdatedAtDesc(userId, projectId);
    }

    /**
     * Get context messages for the agent (most recent messages that fit within context window)
     */
    @Transactional(readOnly = true)
    public List<Message> getContextMessages(UUID conversationId) {
        return getRecentMessages(conversationId, MAX_CONTEXT_MESSAGES);
    }

    @Transactional
    public void deleteConversation(UUID conversationId) {
        log.info("Deleting conversation: {}", conversationId);
        conversationRepository.deleteById(conversationId);
    }
}
