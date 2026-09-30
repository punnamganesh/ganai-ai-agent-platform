
'use client';

import { useState, useRef, useEffect } from 'react';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  agentName?: string;
  timestamp?: Date;
}

interface Conversation {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  agent_name: string;
}

const genId = () => Math.random().toString(36).substring(2, 9);

const TypingIndicator = () => (
  <div className="flex items-start gap-3 mb-4">
    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white text-sm font-bold shadow-md">
      AI
    </div>

    <div className="bg-gray-200 dark:bg-gray-700 rounded-2xl rounded-tl-none px-4 py-3 shadow-sm">
      <div className="flex space-x-1">
        <span className="w-2 h-2 bg-gray-500 dark:bg-gray-300 rounded-full animate-bounce [animation-delay:-0.3s]" />
        <span className="w-2 h-2 bg-gray-500 dark:bg-gray-300 rounded-full animate-bounce [animation-delay:-0.15s]" />
        <span className="w-2 h-2 bg-gray-500 dark:bg-gray-300 rounded-full animate-bounce" />
      </div>
    </div>
  </div>
);

const formatTime = (date: Date) => {
  return date.toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  });
};

const formatConversationDate = (dateString: string) => {
  const date = new Date(dateString);

  return date.toLocaleDateString([], {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
};

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const [conversationId, setConversationId] = useState<number | null>(
    null
  );

  const [conversations, setConversations] = useState<Conversation[]>([]);

  const [loadingConversation, setLoadingConversation] = useState(false);
  const [deletingConversationId, setDeletingConversationId] =
    useState<number | null>(null);

  const [streamingContent, setStreamingContent] = useState('');
  const [streamingAgent, setStreamingAgent] = useState('');

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // =========================================================
  // Load conversation list
  // =========================================================

  const loadConversations = async () => {
    try {
      const response = await fetch(
        'http://localhost:8000/api/conversations'
      );

      if (!response.ok) {
        throw new Error('Failed to load conversations');
      }

      const data = await response.json();

      if (data.success) {
        setConversations(data.conversations);
      }
    } catch (error) {
      console.error(
        'Failed to load conversations:',
        error
      );
    }
  };

  // =========================================================
  // Load a specific conversation
  // =========================================================

  const loadConversation = async (id: number) => {
    if (loading || loadingConversation) {
      return;
    }

    try {
      setLoadingConversation(true);

      const response = await fetch(
        `http://localhost:8000/api/conversations/${id}`
      );

      if (!response.ok) {
        throw new Error(
          `Failed to load conversation ${id}`
        );
      }

      const data = await response.json();

      if (!data.success || !data.conversation) {
        throw new Error(
          'Conversation data not found'
        );
      }

      const conversation = data.conversation;

      const loadedMessages: Message[] =
        conversation.messages.map(
          (message: any) => ({
            id: String(message.id),
            role:
              message.role === 'user'
                ? 'user'
                : 'assistant',
            content: message.content,
            agentName:
              message.agent_name ||
              undefined,
            timestamp: message.timestamp
              ? new Date(message.timestamp)
              : undefined,
          })
        );

      setConversationId(
        conversation.id
      );

      setMessages(
        loadedMessages
      );

      setInput('');
      setStreamingContent('');
      setStreamingAgent('');

      console.log(
        'Loaded conversation:',
        conversation.id
      );
    } catch (error) {
      console.error(
        'Failed to load conversation:',
        error
      );
    } finally {
      setLoadingConversation(false);
      inputRef.current?.focus();
    }
  };

  // =========================================================
  // Delete conversation
  // =========================================================

  const deleteConversation = async (
    id: number
  ) => {
    if (
      deletingConversationId !== null ||
      loading
    ) {
      return;
    }

    const confirmed = window.confirm(
      'Are you sure you want to delete this conversation?'
    );

    if (!confirmed) {
      return;
    }

    try {
      setDeletingConversationId(id);

      const response = await fetch(
        `http://localhost:8000/api/conversations/${id}`,
        {
          method: 'DELETE',
        }
      );

      if (!response.ok) {
        throw new Error(
          `Failed to delete conversation ${id}`
        );
      }

      const data = await response.json();

      if (!data.success) {
        throw new Error(
          'Conversation could not be deleted'
        );
      }

      // If deleting currently opened conversation
      if (conversationId === id) {
        setConversationId(null);
        setMessages([]);
        setInput('');
        setStreamingContent('');
        setStreamingAgent('');
      }

      await loadConversations();

      console.log(
        'Deleted conversation:',
        id
      );
    } catch (error) {
      console.error(
        'Failed to delete conversation:',
        error
      );

      window.alert(
        'Failed to delete conversation. Please try again.'
      );
    } finally {
      setDeletingConversationId(null);
      inputRef.current?.focus();
    }
  };

  // =========================================================
  // New Chat
  // =========================================================

  const startNewChat = () => {
    if (loading) {
      return;
    }

    setConversationId(null);
    setMessages([]);
    setInput('');
    setStreamingContent('');
    setStreamingAgent('');

    console.log(
      'Started new chat'
    );

    inputRef.current?.focus();
  };

  // =========================================================
  // Load conversations on page open
  // =========================================================

  useEffect(() => {
    loadConversations();
  }, []);

  // =========================================================
  // Auto-scroll
  // =========================================================

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: 'smooth',
    });
  }, [
    messages,
    streamingContent,
  ]);

  // =========================================================
  // Focus input
  // =========================================================

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // =========================================================
  // Send message
  // =========================================================

  const sendMessage = async (
    e: React.FormEvent
  ) => {
    e.preventDefault();

    const trimmed = input.trim();

    if (!trimmed || loading) {
      return;
    }

    const userMsg: Message = {
      id: genId(),
      role: 'user',
      content: trimmed,
      timestamp: new Date(),
    };

    setMessages((prev) => [
      ...prev,
      userMsg,
    ]);

    setInput('');
    setLoading(true);
    setStreamingContent('');
    setStreamingAgent('');

    try {
      const payload: {
        message: string;
        conversation_id?: number;
      } = {
        message: trimmed,
      };

      // Continue existing conversation
      if (conversationId !== null) {
        payload.conversation_id =
          conversationId;
      }

      console.log(
        'Sending chat request:',
        payload
      );

      const response = await fetch(
        'http://localhost:8000/api/chat/stream',
        {
          method: 'POST',
          headers: {
            'Content-Type':
              'application/json',
          },
          body: JSON.stringify(
            payload
          ),
        }
      );

      if (!response.ok) {
        throw new Error(
          `Request failed with status ${response.status}`
        );
      }

      if (!response.body) {
        throw new Error(
          'No response body'
        );
      }

      const reader =
        response.body.getReader();

      const decoder =
        new TextDecoder();

      let fullContent = '';
      let agentName = '';

      while (true) {
        const {
          done,
          value,
        } = await reader.read();

        if (done) {
          break;
        }

        const chunk =
          decoder.decode(value, {
            stream: true,
          });

        const lines =
          chunk.split('\n');

        for (const line of lines) {
          if (
            !line.startsWith(
              'data: '
            )
          ) {
            continue;
          }

          const content =
            line
              .substring(6)
              .trim();

          // ------------------------------------------
          // Conversation ID
          // ------------------------------------------

          if (
            content.startsWith(
              'conversation_id:'
            )
          ) {
            const idString =
              content
                .substring(
                  'conversation_id:'.length
                )
                .trim();

            const newConversationId =
              Number(idString);

            if (
              !Number.isNaN(
                newConversationId
              )
            ) {
              console.log(
                'Conversation ID received:',
                newConversationId
              );

              setConversationId(
                newConversationId
              );
            }

            continue;
          }

          // ------------------------------------------
          // Agent
          // ------------------------------------------

          if (
            content.startsWith(
              'agent:'
            )
          ) {
            agentName =
              content
                .substring(
                  'agent:'.length
                )
                .trim();

            setStreamingAgent(
              agentName
            );

            continue;
          }

          // ------------------------------------------
          // Stream completed
          // ------------------------------------------

          if (
            content === '[DONE]'
          ) {
            continue;
          }

          // ------------------------------------------
          // Backend error
          // ------------------------------------------

          if (
            content.startsWith(
              'Error:'
            )
          ) {
            throw new Error(
              content
            );
          }

          // ------------------------------------------
          // AI response
          // ------------------------------------------

          if (content) {
            fullContent += content;

            setStreamingContent(
              fullContent
            );
          }
        }
      }

      // --------------------------------------------
      // Add assistant message
      // --------------------------------------------

      if (fullContent) {
        const assistantMsg: Message = {
          id: genId(),
          role: 'assistant',
          content: fullContent,
          agentName:
            agentName ||
            'Assistant',
          timestamp: new Date(),
        };

        setMessages((prev) => [
          ...prev,
          assistantMsg,
        ]);
      }

      setStreamingContent('');
      setStreamingAgent('');

      // Refresh conversation list
      await loadConversations();

    } catch (error: any) {
      console.error(
        'Stream error:',
        error
      );

      const errorMsg: Message = {
        id: genId(),
        role: 'assistant',
        content: `⚠️ ${
          error?.message ||
          'Something went wrong'
        }`,
        agentName: 'System',
        timestamp: new Date(),
      };

      setMessages((prev) => [
        ...prev,
        errorMsg,
      ]);
    } finally {
      setLoading(false);
    }
  };

  // =========================================================
  // UI
  // =========================================================

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900">

      {/* =====================================================
          SIDEBAR
          ===================================================== */}

      <aside className="w-80 flex-shrink-0 border-r border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-950">

        {/* Sidebar Header */}

        <div className="p-4 border-b border-gray-200 dark:border-gray-700">

          <div className="flex items-center justify-between gap-3">

            <div className="flex items-center gap-3">

              <div className="w-9 h-9 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold shadow-md">
                AI
              </div>

              <div>
                <h2 className="font-bold text-gray-800 dark:text-gray-100">
                  GanAI
                </h2>

                <p className="text-xs text-gray-500 dark:text-gray-400">
                  AI Agent Platform
                </p>
              </div>

            </div>

          </div>

        </div>

        {/* New Chat Button */}

        <div className="p-3">

          <button
            type="button"
            onClick={startNewChat}
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-gradient-to-r from-blue-500 to-purple-600 text-white font-medium shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            <span className="text-lg">
              +
            </span>

            New Chat
          </button>

        </div>

        {/* Conversation List */}

        <div className="px-3 pb-3">

          <div className="flex items-center justify-between mb-3">

            <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
              Conversations
            </h3>

            <span className="text-xs text-gray-400">
              {conversations.length}
            </span>

          </div>

          <div className="space-y-2 overflow-y-auto max-h-[calc(100vh-170px)]">

            {conversations.length === 0 ? (

              <div className="text-center py-8 text-sm text-gray-400">
                No conversations yet
              </div>

            ) : (

              conversations.map(
                (conversation) => (

                  <div
                    key={conversation.id}
                    className={`group p-3 rounded-xl border transition ${
                      conversation.id ===
                      conversationId
                        ? 'bg-blue-50 dark:bg-blue-950 border-blue-300 dark:border-blue-700'
                        : 'bg-gray-50 dark:bg-gray-900 border-gray-200 dark:border-gray-800 hover:bg-gray-100 dark:hover:bg-gray-800'
                    }`}
                  >

                    {/* Conversation row */}

                    <div className="flex items-start gap-2">

                      {/* Load conversation */}

                      <button
                        type="button"
                        onClick={() =>
                          loadConversation(
                            conversation.id
                          )
                        }
                        disabled={
                          loading ||
                          loadingConversation ||
                          deletingConversationId !==
                            null
                        }
                        className="flex-1 min-w-0 text-left disabled:opacity-50"
                      >

                        <div className="font-medium text-sm text-gray-800 dark:text-gray-100 truncate">
                          {conversation.title}
                        </div>

                        <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                          Conversation #
                          {conversation.id}
                        </div>

                        <div className="flex items-center justify-between mt-2">

                          <span className="text-xs text-gray-500 dark:text-gray-400">
                            {
                              conversation.message_count
                            }{' '}
                            {conversation.message_count ===
                            1
                              ? 'message'
                              : 'messages'}
                          </span>

                          <span className="text-[10px] text-gray-400">
                            {formatConversationDate(
                              conversation.updated_at
                            )}
                          </span>

                        </div>

                      </button>

                      {/* Delete button */}

                      <button
                        type="button"
                        onClick={() =>
                          deleteConversation(
                            conversation.id
                          )
                        }
                        disabled={
                          loading ||
                          deletingConversationId !==
                            null
                        }
                        title="Delete conversation"
                        className="flex-shrink-0 p-2 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-950 disabled:opacity-40 transition-colors"
                      >

                        {deletingConversationId ===
                        conversation.id ? (
                          <svg
                            className="animate-spin w-4 h-4"
                            viewBox="0 0 24 24"
                          >
                            <circle
                              className="opacity-25"
                              cx="12"
                              cy="12"
                              r="10"
                              stroke="currentColor"
                              strokeWidth="4"
                              fill="none"
                            />

                            <path
                              className="opacity-75"
                              fill="currentColor"
                              d="M4 12a8 8 0 018-8"
                            />
                          </svg>
                        ) : (
                          <svg
                            className="w-4 h-4"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                          >
                            <path d="M3 6h18" />
                            <path d="M8 6V4h8v2" />
                            <path d="M19 6l-1 14H6L5 6" />
                            <path d="M10 11v5" />
                            <path d="M14 11v5" />
                          </svg>
                        )}

                      </button>

                    </div>

                  </div>

                )
              )

            )}

          </div>

        </div>

      </aside>

      {/* =====================================================
          MAIN CHAT
          ===================================================== */}

      <main className="flex flex-col flex-1 min-w-0">

        {/* Header */}

        <header className="flex items-center justify-between py-4 px-6 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-950">

          <div className="flex items-center gap-3">

            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-xl font-bold shadow-md">
              AI
            </div>

            <div>

              <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                Assistant
              </h1>

              <p className="text-xs text-gray-500 dark:text-gray-400">

                {loadingConversation
                  ? 'Loading conversation...'
                  : conversationId
                  ? `Conversation #${conversationId}`
                  : messages.length > 0
                  ? `${messages.length} messages`
                  : 'New conversation'}

              </p>

            </div>

          </div>

          <div className="flex items-center gap-2">

            <span className="inline-block w-2 h-2 rounded-full bg-green-400 animate-pulse" />

            <span className="text-xs text-gray-500 dark:text-gray-400">
              Online
            </span>

          </div>

        </header>

        {/* =====================================================
            CHAT AREA
            ===================================================== */}

        <div className="flex-1 overflow-y-auto py-4 px-6 space-y-4 scroll-smooth">

          {loadingConversation ? (

            <div className="flex items-center justify-center h-full">

              <div className="flex items-center gap-3 text-gray-500">

                <svg
                  className="animate-spin w-5 h-5"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                    fill="none"
                  />

                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8"
                  />
                </svg>

                Loading conversation...

              </div>

            </div>

          ) : messages.length === 0 &&
            !streamingContent ? (

            <div className="flex flex-col items-center justify-center h-full text-center text-gray-400 dark:text-gray-500">

              <div className="w-20 h-20 mb-4 rounded-full bg-gradient-to-br from-blue-100 to-purple-100 dark:from-blue-900 dark:to-purple-900 flex items-center justify-center text-4xl">
                🤖
              </div>

              <h2 className="text-xl font-semibold text-gray-700 dark:text-gray-300">
                Start a conversation
              </h2>

              <p className="text-sm max-w-sm mt-2">
                Ask me anything – I can calculate,
                check weather, search the web,
                and more.
              </p>

            </div>

          ) : (

            <>

              {/* Existing messages */}

              {messages.map(
                (msg) => (

                  <div
                    key={msg.id}
                    className={`flex items-start gap-3 ${
                      msg.role === 'user'
                        ? 'flex-row-reverse'
                        : ''
                    }`}
                  >

                    {/* Avatar */}

                    <div
                      className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-white text-sm font-bold shadow-md ${
                        msg.role === 'user'
                          ? 'bg-blue-500'
                          : 'bg-gradient-to-br from-purple-500 to-pink-500'
                      }`}
                    >
                      {msg.role === 'user'
                        ? 'U'
                        : 'AI'}
                    </div>

                    {/* Message */}

                    <div
                      className={`max-w-[80%] px-4 py-3 rounded-2xl shadow-sm ${
                        msg.role === 'user'
                          ? 'bg-blue-500 text-white rounded-tr-none'
                          : 'bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-100 rounded-tl-none border border-gray-200 dark:border-gray-700'
                      }`}
                    >

                      <div className="whitespace-pre-wrap break-words">
                        {msg.content}
                      </div>

                      {msg.role ===
                        'assistant' &&
                        msg.agentName && (

                          <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                            Agent:{' '}
                            <span className="font-medium">
                              {
                                msg.agentName
                              }
                            </span>
                          </div>

                        )}

                      {msg.timestamp && (

                        <div className="mt-1 text-[10px] opacity-60 text-right">
                          {formatTime(
                            msg.timestamp
                          )}
                        </div>

                      )}

                    </div>

                  </div>

                )
              )}

              {/* Streaming message */}

              {streamingContent && (

                <div className="flex items-start gap-3">

                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex-shrink-0 flex items-center justify-center text-white text-sm font-bold shadow-md">
                    AI
                  </div>

                  <div className="max-w-[80%] px-4 py-3 rounded-2xl rounded-tl-none bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-100 border border-gray-200 dark:border-gray-700 shadow-sm">

                    <div className="whitespace-pre-wrap break-words">

                      {streamingContent}

                      <span className="inline-block w-1.5 h-4 bg-gray-400 dark:bg-gray-500 animate-pulse ml-0.5 align-middle" />

                    </div>

                    {streamingAgent && (

                      <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">

                        Agent:{' '}

                        <span className="font-medium">
                          {streamingAgent}
                        </span>

                      </div>

                    )}

                  </div>

                </div>

              )}

              {loading &&
                !streamingContent && (
                  <TypingIndicator />
                )}

            </>

          )}

          <div ref={messagesEndRef} />

        </div>

        {/* =====================================================
            INPUT
            ===================================================== */}

        <form
          onSubmit={sendMessage}
          className="flex gap-2 px-6 py-4 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-950"
        >

          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) =>
              setInput(e.target.value)
            }
            placeholder="Type your message..."
            className="flex-1 p-3 rounded-2xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-shadow disabled:opacity-50"
            disabled={
              loading ||
              loadingConversation
            }
          />

          <button
            type="submit"
            disabled={
              loading ||
              loadingConversation ||
              !input.trim()
            }
            className="px-6 py-3 rounded-2xl bg-gradient-to-r from-blue-500 to-purple-600 text-white font-medium shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center gap-2"
          >

            {loading ? (

              <>

                <svg
                  className="animate-spin h-4 w-4"
                  viewBox="0 0 24 24"
                >

                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                    fill="none"
                  />

                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.746 5.74 4.11 7.13L6 17.291z"
                  />

                </svg>

                Sending

              </>

            ) : (

              'Send'

            )}

          </button>

        </form>

      </main>

    </div>
  );
}

