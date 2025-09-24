/**
 * RAG Testing Interface - Main Page
 * Author: Emad Noorizadeh
 */

'use client';

import { useState } from 'react';
import DocumentUpload from '@/components/DocumentUpload';
import QueryInterface from '@/components/QueryInterface';
import DocumentList from '@/components/DocumentList';
import ChatInterface from '@/components/ChatInterface';
import Settings from '@/components/Settings';
import { useSession } from '@/hooks/useSession';

// Define Message interface for chat
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
  metrics?: {
    chunks_retrieved: Array<{
      id: string;
      text: string;
      metadata: Record<string, any>;
      similarity_score: number;
    }>;
    context_utilization: {
      precision: number;
      recall: number;
      f1_score: number;
      semantic_coverage: number;
      entity_alignment: number;
      numeric_fact_matching: number;
      sentence_level_alignment: number;
      qa_alignment: number;
      supported_terms: Array<{ term: string, spans: Array<{ start: number, end: number }> }>;
      entities: Array<{ entity: string, spans: Array<{ start: number, end: number }> }>;
    };
    retrieval_metadata: {
      method: string;
      total_chunks: number;
      similarity_threshold: number;
    };
    generation_metadata: {
      model: string;
      temperature: number;
      max_tokens: number;
      response_time: number;
    };
    clarification_questions: Array<string>;
    abstained: boolean;
    reasoning_notes: string;
  };
}

export default function Home() {
  const [activeTab, setActiveTab] = useState<'upload' | 'query' | 'documents' | 'chat' | 'settings'>('upload');
  const [showDebugPanel, setShowDebugPanel] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentMetrics, setCurrentMetrics] = useState<any>(null);
  const [expandedSources, setExpandedSources] = useState<Set<string>>(new Set());
  const { sessionStatus } = useSession();

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <header className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">RAG Testing Interface</h1>
          <p className="text-gray-600">Test and evaluate Retrieval-Augmented Generation</p>
          {sessionStatus.isValid && sessionStatus.sessionId && (
            <div className="mt-4 inline-flex items-center px-3 py-1 rounded-full text-sm bg-green-100 text-green-800">
              <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
              Session Active
              {sessionStatus.remainingTime && (
                <span className="ml-2 text-xs">
                  ({Math.floor(sessionStatus.remainingTime / 60)}m {sessionStatus.remainingTime % 60}s remaining)
                </span>
              )}
            </div>
          )}
          {sessionStatus.isLoading && (
            <div className="mt-4 inline-flex items-center px-3 py-1 rounded-full text-sm bg-yellow-100 text-yellow-800">
              <div className="w-2 h-2 bg-yellow-500 rounded-full mr-2 animate-pulse"></div>
              Initializing Session...
            </div>
          )}
          {sessionStatus.error && (
            <div className="mt-4 inline-flex items-center px-3 py-1 rounded-full text-sm bg-red-100 text-red-800">
              <div className="w-2 h-2 bg-red-500 rounded-full mr-2"></div>
              {sessionStatus.error}
            </div>
          )}
        </header>

        {/* Navigation Tabs */}
        <div className="flex justify-center mb-8">
          <div className="bg-white rounded-lg shadow-sm p-1">
            <button
              onClick={() => setActiveTab('settings')}
              className={`px-6 py-2 rounded-md transition-colors ${activeTab === 'settings'
                ? 'bg-blue-500 text-white'
                : 'text-gray-600 hover:text-gray-900'
                }`}
            >
              Settings
            </button>
            <button
              onClick={() => setActiveTab('upload')}
              className={`px-6 py-2 rounded-md transition-colors ${activeTab === 'upload'
                ? 'bg-blue-500 text-white'
                : 'text-gray-600 hover:text-gray-900'
                }`}
            >
              Upload Documents
            </button>
            <button
              onClick={() => setActiveTab('query')}
              className={`px-6 py-2 rounded-md transition-colors ${activeTab === 'query'
                ? 'bg-blue-500 text-white'
                : 'text-gray-600 hover:text-gray-900'
                }`}
            >
              Query Documents
            </button>
            <button
              onClick={() => setActiveTab('documents')}
              className={`px-6 py-2 rounded-md transition-colors ${activeTab === 'documents'
                ? 'bg-blue-500 text-white'
                : 'text-gray-600 hover:text-gray-900'
                }`}
            >
              View Documents
            </button>
            <button
              onClick={() => setActiveTab('chat')}
              className={`px-6 py-2 rounded-md transition-colors ${activeTab === 'chat'
                ? 'bg-blue-500 text-white'
                : 'text-gray-600 hover:text-gray-900'
                }`}
            >
              Chat
            </button>
          </div>
        </div>

        {/* Tab Content */}
        <div className="max-w-4xl mx-auto">
          {activeTab === 'upload' && <DocumentUpload />}
          {activeTab === 'query' && <QueryInterface />}
          {activeTab === 'documents' && <DocumentList />}
          {activeTab === 'chat' && <ChatInterface
            showDebugPanel={showDebugPanel}
            setShowDebugPanel={setShowDebugPanel}
            sessionStatus={sessionStatus}
            messages={messages}
            setMessages={setMessages}
            currentMetrics={currentMetrics}
            setCurrentMetrics={setCurrentMetrics}
            expandedSources={expandedSources}
            setExpandedSources={setExpandedSources}
          />}
          {activeTab === 'settings' && <Settings />}
        </div>
      </div>
    </div>
  );
}