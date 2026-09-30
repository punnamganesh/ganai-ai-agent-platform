'use client';

import { useState, useRef, useEffect } from 'react';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  agentName?: string;
  timestamp?: Date;
}

// Simple unique ID generator
const genId = () => Math.random().toString(36).substring(2, 9);

// Typing indicator (bouncing dots)
const TypingIndicator = () => (
  <div className="flex items-start gap-3 mb-4">
    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white text-sm font-bold shadow-md">
      AI
    </div>
    <div className="bg-gray-200 dark:bg-gray-700 rounded-2xl rounded-tl-none px-4 py-3 shadow-sm">
      <div className="flex space-x-1">
        <span className="w-2 h-2 bg-gray-500 dark:bg-gray-300 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
        <span className="w-2 h-2 bg-gray-500 dark:bg-gray-300 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
        <span className="w-2 h-2 bg-gray-500 dark:bg-gray-300 rounded-full animate-bounce"></span>
      </div>
    </div>
  </div>
);

// Helper: format timestamp
const formatTime = (date: Date) => {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
};

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [streamingContent, setStreamingContent] = useState<string>('');
  const [streamingAgent, setStreamingAgent] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingContent]);

  // Focus input on load
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || loading) return;

    // Add user message
    const userMsg: Message = {
      id: genId(),
      role: 'user',
      content: trimmed,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);
    setStreamingContent('');
    setStreamingAgent('');

    try {
      const payload: any = { message: trimmed };
      if (conversationId) payload.conversation_id = conversationId;

      const response = await fetch('http://localhost:8000/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.body) throw new Error('No response body');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullContent = '';
      let agentName = '';
      let newConvId = conversationId;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const content = line.substring(6).trim();
            if (content === '[DONE]') {
              // stream finished
              break;
            } else if (content.startsWith('agent:')) {
              agentName = content.substring(6).trim();
              setStreamingAgent(agentName);
            } else if (content.startsWith('Error:')) {
              throw new Error(content);
            } else {
              fullContent += content;
              setStreamingContent(fullContent);
            }
          }
        }
      }

      // Finalise the assistant message
      if (fullContent) {
        const assistantMsg: Message = {
          id: genId(),
          role: 'assistant',
          content: fullContent,
          agentName: agentName || streamingAgent || 'Assistant',
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, assistantMsg]);
        // Store conversation ID if we got one (we can extract from response headers or assume it's passed)
        // For now, we'll keep the existing convId – the backend should set a new one if not provided.
        // We'll update it from a custom header if needed – but we can also read it from the first message?
        // To simplify, we'll generate a new one if not present.
        if (!conversationId) {
          // We could get it from the response header, but let's just create one
          // Actually we don't have it – we'll rely on the backend to send it via a separate event if needed.
          // For now, we'll keep what we had.
        }
      }

      setStreamingContent('');
      setStreamingAgent('');
    } catch (error: any) {
      console.error('Stream error:', error);
      const errorMsg: Message = {
        id: genId(),
        role: 'assistant',
        content: `⚠️ ${error.message || 'Something went wrong'}`,
        agentName: 'System',
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto p-4 bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="flex items-center justify-between py-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-xl font-bold shadow-md">
            AI
          </div>
          <div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              Assistant
            </h1>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {messages.length > 0 ? `${messages.length} messages` : 'Ready to help'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-block w-2 h-2 rounded-full bg-green-400 animate-pulse"></span>
          <span className="text-xs text-gray-500 dark:text-gray-400">Online</span>
        </div>
      </header>

      {/* Chat area */}
      <div className="flex-1 overflow-y-auto py-4 space-y-4 scroll-smooth">
        {messages.length === 0 && !streamingContent ? (
          <div className="flex flex-col items-center justify-center h-full text-center text-gray-400 dark:text-gray-500">
            <div className="w-20 h-20 mb-4 rounded-full bg-gradient-to-br from-blue-100 to-purple-100 dark:from-blue-900 dark:to-purple-900 flex items-center justify-center text-4xl">
              🤖
            </div>
            <h2 className="text-xl font-semibold text-gray-700 dark:text-gray-300">Start a conversation</h2>
            <p className="text-sm max-w-sm mt-2">
              Ask me anything – I can calculate, check weather, search the web, and more.
            </p>
          </div>
        ) : (
          <>
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex items-start gap-3 ${
                  msg.role === 'user' ? 'flex-row-reverse' : ''
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
                  {msg.role === 'user' ? 'U' : 'AI'}
                </div>

                {/* Message bubble */}
                <div
                  className={`max-w-[80%] px-4 py-3 rounded-2xl shadow-sm ${
                    msg.role === 'user'
                      ? 'bg-blue-500 text-white rounded-tr-none'
                      : 'bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-100 rounded-tl-none border border-gray-200 dark:border-gray-700'
                  }`}
                >
                  <div className="whitespace-pre-wrap break-words">{msg.content}</div>
                  {msg.role === 'assistant' && msg.agentName && (
                    <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                      Agent: <span className="font-medium">{msg.agentName}</span>
                    </div>
                  )}
                  {msg.timestamp && (
                    <div className="mt-1 text-[10px] opacity-60 text-right">
                      {formatTime(msg.timestamp)}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {/* Streaming message */}
            {streamingContent && (
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex-shrink-0 flex items-center justify-center text-white text-sm font-bold shadow-md">
                  AI
                </div>
                <div className="max-w-[80%] px-4 py-3 rounded-2xl rounded-tl-none bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-100 border border-gray-200 dark:border-gray-700 shadow-sm">
                  <div className="whitespace-pre-wrap break-words">
                    {streamingContent}
                    <span className="inline-block w-1.5 h-4 bg-gray-400 dark:bg-gray-500 animate-pulse ml-0.5 align-middle"></span>
                  </div>
                  {streamingAgent && (
                    <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                      Agent: <span className="font-medium">{streamingAgent}</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {loading && !streamingContent && <TypingIndicator />}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input form */}
      <form onSubmit={sendMessage} className="flex gap-2 pt-4 border-t border-gray-200 dark:border-gray-700">
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          className="flex-1 p-3 rounded-2xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-shadow disabled:opacity-50"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="px-6 py-3 rounded-2xl bg-gradient-to-r from-blue-500 to-purple-600 text-white font-medium shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center gap-2"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Sending
            </>
          ) : (
            'Send'
          )}
        </button>
      </form>
    </div>
  );
}