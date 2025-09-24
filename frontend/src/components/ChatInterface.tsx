/**
 * Chat Interface Component
 * Author: Emad Noorizadeh
 */

'use client';

import { useState, useRef, useEffect } from 'react';
import DebugPanel from './DebugPanel';
import HighlightedText from './HighlightedText';
// useSession is now passed as props from parent component

// Message interface is now defined in parent component
interface Message {
    id: string;
    text: string;
    isUser: boolean;
    timestamp: Date;
    sources?: Array<{
        id: string;
        text: string;
        metadata: Record<string, any>;
        distance?: number;
        similarity?: number;
    }>;
    metrics?: any; // Simplified for now
}

interface ChatInterfaceProps {
    showDebugPanel: boolean;
    setShowDebugPanel: (show: boolean) => void;
    sessionStatus: {
        isValid: boolean;
        sessionId: string | null;
        remainingTime?: number;
        isLoading: boolean;
        error: string | null;
    };
    messages: Message[];
    setMessages: (messages: Message[]) => void;
    currentMetrics: any;
    setCurrentMetrics: (metrics: any) => void;
    expandedSources: Set<string>;
    setExpandedSources: (sources: Set<string>) => void;
}

export default function ChatInterface({
    showDebugPanel,
    setShowDebugPanel,
    sessionStatus,
    messages,
    setMessages,
    currentMetrics,
    setCurrentMetrics,
    expandedSources,
    setExpandedSources
}: ChatInterfaceProps) {
    const [inputText, setInputText] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    // Debug panel state is now managed by parent component
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const messagesLoaded = useRef(false);

    // Session status is now passed as props from parent component

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    const toggleSources = (messageId: string) => {
        setExpandedSources(prev => {
            const newSet = new Set(prev);
            if (newSet.has(messageId)) {
                newSet.delete(messageId);
            } else {
                newSet.add(messageId);
            }
            return newSet;
        });
    };


    // Load messages from localStorage when session is available
    useEffect(() => {
        const loadMessages = () => {
            if (!sessionStatus.sessionId || messagesLoaded.current) {
                return;
            }

            try {
                // Try to load messages from localStorage
                const storedMessages = localStorage.getItem(`chatMessages_${sessionStatus.sessionId}`);
                if (storedMessages) {
                    const parsedMessages = JSON.parse(storedMessages);
                    // Convert timestamp strings back to Date objects
                    const messagesWithDates = parsedMessages.map((msg: any) => ({
                        ...msg,
                        timestamp: new Date(msg.timestamp)
                    }));
                    setMessages(messagesWithDates);
                    messagesLoaded.current = true;
                } else {
                    // No stored messages, add welcome message
                    const welcomeMessage: Message = {
                        id: 'welcome_' + Date.now(),
                        text: "Hello! I'm your RAG assistant. I can help you find information from your uploaded documents. How can I help you today? Ask me any question!",
                        isUser: false,
                        timestamp: new Date(),
                    };
                    setMessages([welcomeMessage]);
                    messagesLoaded.current = true;
                }
            } catch (error) {
                console.error('Error loading messages:', error);
                // Fallback to welcome message
                const welcomeMessage: Message = {
                    id: 'welcome_' + Date.now(),
                    text: "Hello! I'm your RAG assistant. I can help you find information from your uploaded documents. How can I help you today? Ask me any question!",
                    isUser: false,
                    timestamp: new Date(),
                };
                setMessages([welcomeMessage]);
                messagesLoaded.current = true;
            }
        };

        if (sessionStatus.isValid && sessionStatus.sessionId) {
            loadMessages();
        }
    }, [sessionStatus.isValid, sessionStatus.sessionId]);

    // Save messages to localStorage whenever messages change
    useEffect(() => {
        if (sessionStatus.sessionId && messages.length > 0 && typeof window !== 'undefined' && typeof localStorage !== 'undefined') {
            localStorage.setItem(`chatMessages_${sessionStatus.sessionId}`, JSON.stringify(messages));
        }
    }, [messages, sessionStatus.sessionId]);

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!inputText.trim() || loading || !sessionStatus.sessionId) {
            return;
        }

        const userMessage: Message = {
            id: Date.now().toString(),
            text: inputText.trim(),
            isUser: true,
            timestamp: new Date(),
        };

        setMessages(prev => [...prev, userMessage]);
        setInputText('');
        setLoading(true);
        setError('');

        try {
            const response = await fetch('http://localhost:9000/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: userMessage.text,
                    conversation_history: messages.slice(-10).map(msg => ({
                        text: msg.text,
                        isUser: msg.isUser,
                        timestamp: msg.timestamp.toISOString()
                    })), // Convert to backend format
                    session_id: sessionStatus.sessionId,
                }),
            });

            if (response.ok) {
                const data = await response.json();
                const botMessage: Message = {
                    id: (Date.now() + 1).toString(),
                    text: data.answer,
                    isUser: false,
                    timestamp: new Date(),
                    sources: data.sources,
                    metrics: data.metrics,
                };
                setMessages(prev => [...prev, botMessage]);
                // Include generated_by in the metrics object for the debug panel
                setCurrentMetrics({
                    ...data.metrics,
                    generated_by: data.generated_by
                });
            } else if (response.status === 410) {
                // Session expired
                setError('Your session has expired. Please refresh the page to start a new conversation.');
            } else {
                const errorData = await response.json();
                setError(`Error: ${errorData.detail}`);
            }
        } catch (error) {
            setError(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
        } finally {
            setLoading(false);
        }
    };

    const clearChat = async () => {
        setError('');
        setCurrentMetrics(null);
        setShowDebugPanel(false);

        // Clear messages from localStorage
        if (sessionStatus.sessionId && typeof window !== 'undefined' && typeof localStorage !== 'undefined') {
            localStorage.removeItem(`chatMessages_${sessionStatus.sessionId}`);
        }

        // Session management is handled by parent component
        messagesLoaded.current = false;

        // Add welcome message
        const welcomeMessage: Message = {
            id: 'welcome_' + Date.now(),
            text: "Hello! I'm your RAG assistant. I can help you find information from your uploaded documents. How can I help you today? Ask me any question!",
            isUser: false,
            timestamp: new Date(),
        };
        setMessages([welcomeMessage]);
        messagesLoaded.current = true;
    };

    return (
        <div className="bg-white rounded-lg shadow-md h-[600px] flex">
            {/* Chat Panel */}
            <div className={`flex flex-col ${showDebugPanel ? 'flex-1 mr-4' : 'w-full'}`}>
                <div className="flex justify-between items-center p-6 pb-4 border-b border-gray-200">
                    <div className="flex flex-col">
                        <h2 className="text-2xl font-semibold text-gray-900">Chat</h2>
                        {sessionStatus.isValid && sessionStatus.sessionId && (
                            <div className="text-xs text-gray-500 mt-1">
                                Session: {sessionStatus.sessionId.substring(0, 8)}...
                                {sessionStatus.remainingTime && (
                                    <span className="ml-2">
                                        ({Math.floor(sessionStatus.remainingTime / 60)}m {sessionStatus.remainingTime % 60}s remaining)
                                    </span>
                                )}
                            </div>
                        )}
                        {sessionStatus.isLoading && (
                            <div className="text-xs text-yellow-600 mt-1">
                                Initializing session...
                            </div>
                        )}
                        {sessionStatus.error && (
                            <div className="text-xs text-red-600 mt-1">
                                {sessionStatus.error}
                            </div>
                        )}
                    </div>
                    <div className="flex space-x-2">
                        <button
                            onClick={() => setShowDebugPanel(!showDebugPanel)}
                            className={`px-4 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 ${showDebugPanel
                                ? 'bg-blue-500 text-white hover:bg-blue-600 focus:ring-blue-500'
                                : 'bg-gray-200 text-gray-700 hover:bg-gray-300 focus:ring-gray-500'
                                }`}
                        >
                            {showDebugPanel ? 'Hide Debug' : 'Show Debug'}
                        </button>
                        <button
                            onClick={clearChat}
                            className="px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
                        >
                            Clear Chat
                        </button>
                    </div>
                </div>

                {/* Messages Area */}
                <div className="flex-1 overflow-y-auto p-6 space-y-4 text-left">
                    {sessionStatus.isLoading ? (
                        <div className="text-center text-gray-500 py-8">
                            <div className="text-4xl mb-4">⏳</div>
                            <p>Initializing session...</p>
                        </div>
                    ) : messages.length === 0 ? (
                        <div className="text-center text-gray-500 py-8">
                            <div className="text-4xl mb-4">💬</div>
                            <p>Loading chat...</p>
                            {sessionStatus.sessionId && (
                                <p className="text-xs mt-4 text-gray-400">
                                    Session: {sessionStatus.sessionId.substring(0, 20)}...
                                </p>
                            )}
                        </div>
                    ) : (
                        messages.map((message) => (
                            <div
                                key={message.id}
                                className={`flex ${message.isUser ? 'justify-end' : 'justify-start'}`}
                            >
                                <div
                                    className={`max-w-[80%] rounded-lg p-3 ${message.isUser
                                        ? 'bg-blue-500 text-white'
                                        : 'bg-gray-100 text-gray-900'
                                        }`}
                                >
                                    {showDebugPanel &&
                                        message.metrics?.context_utilization &&
                                        typeof message.metrics.context_utilization === 'object' &&
                                        'supported_terms_per_sentence' in message.metrics.context_utilization ? (
                                        <HighlightedText
                                            text={message.text}
                                            supportedTerms={message.metrics.context_utilization.supported_terms_per_sentence?.flatMap(s => s.supported_terms) || []}
                                            supportedEntities={message.metrics.context_utilization.supported_entities?.items || []}
                                        />
                                    ) : (
                                        <p className="whitespace-pre-wrap text-left">{message.text}</p>
                                    )}
                                    {message.sources && message.sources.length > 0 && (
                                        <div className="mt-2 pt-2 border-t border-gray-300">
                                            <button
                                                onClick={() => toggleSources(message.id)}
                                                className="flex items-center text-xs font-semibold mb-1 hover:text-blue-600 transition-colors"
                                            >
                                                <span className="mr-1">
                                                    {expandedSources.has(message.id) ? '▼' : '▶'}
                                                </span>
                                                Sources ({message.sources.length})
                                            </button>
                                            {expandedSources.has(message.id) && (
                                                <div className="mt-2 space-y-2">
                                                    {message.sources.map((source, index) => (
                                                        <div key={index} className="text-xs bg-gray-200 rounded p-2">
                                                            <p className="font-medium">Source {index + 1}</p>
                                                            <p className="text-gray-600 line-clamp-2">{source.text}</p>
                                                            <p className="text-gray-500">
                                                                Similarity: {source.similarity ? source.similarity.toFixed(3) : 'N/A'}
                                                            </p>
                                                        </div>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    )}
                                    <p className="text-xs opacity-70 mt-1">
                                        {message.timestamp.toLocaleTimeString()}
                                    </p>
                                </div>
                            </div>
                        ))
                    )}
                    {loading && (
                        <div className="flex justify-start">
                            <div className="bg-gray-100 text-gray-900 rounded-lg p-3">
                                <div className="flex items-center space-x-2">
                                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600"></div>
                                    <span>Thinking...</span>
                                </div>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                {/* Error Display */}
                {(error || sessionStatus.error) && (
                    <div className="px-6 pb-4">
                        <div className="p-3 bg-red-100 text-red-700 border border-red-300 rounded-md">
                            {error || sessionStatus.error}
                        </div>
                    </div>
                )}

                {/* Input Area */}
                <div className="px-6 pb-6">
                    <form onSubmit={handleSubmit} className="flex space-x-2">
                        <input
                            type="text"
                            value={inputText}
                            onChange={(e) => setInputText(e.target.value)}
                            placeholder={sessionStatus.isValid ? "Ask a question about your documents..." : "Initializing session..."}
                            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            disabled={loading || !sessionStatus.isValid}
                        />
                        <button
                            type="submit"
                            disabled={loading || !inputText.trim() || !sessionStatus.isValid}
                            className="px-6 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            Send
                        </button>
                    </form>
                </div>
            </div>

            {/* Debug Panel */}
            {showDebugPanel && (
                <div className="w-96">
                    <DebugPanel
                        metrics={currentMetrics}
                        isLoading={loading}
                        generatedBy={currentMetrics?.generated_by}
                    />
                </div>
            )}
        </div>
    );
}
