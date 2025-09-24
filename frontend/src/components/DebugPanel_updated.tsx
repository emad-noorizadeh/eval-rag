/**
 * Debug Panel Component with Detailed Node Metrics
 * Author: Emad Noorizadeh
 */

'use client';

import { useState } from 'react';

interface RAGMetrics {
    // LangGraph metrics
    clarify_count?: number;
    threshold?: number;
    top_k?: number;
    max_clarify?: number;
    conversation_length?: number;

    // Detailed node metrics
    ingest_metrics?: {
        original_question?: string;
        processed_question?: string;
        is_clarification_response?: boolean;
        conversation_length?: number;
        rephrased?: boolean;
        summary?: string;
    };
    retrieve_metrics?: {
        question?: string;
        top_k?: number;
        chunks_retrieved?: number;
        avg_similarity?: number;
        max_similarity?: number;
        min_similarity?: number;
        chunk_scores?: number[];
        context_length?: number;
        valid_chunk_ids?: string[];
    };
    route_metrics?: {
        retrieved_chunks?: number;
        avg_similarity?: number;
        threshold?: number;
        is_clarification_response?: boolean;
        route_decision?: string;
        scores?: number[];
        above_threshold?: boolean;
    };
    rag_metrics?: {
        question?: string;
        context_used?: string;
        response_generated?: string;
        clarification_question?: string;
        confidence?: string;
        answer_type?: string;
        reasoning?: string;
    };
    clarify_metrics?: {
        question?: string;
        clarification_question?: string;
        clarify_count?: number;
        max_clarify?: number;
        reason?: string;
    };

    // Legacy RAG metrics
    chunks_retrieved?: Array<{
        id: string;
        text: string;
        metadata: Record<string, any>;
        similarity_score?: number;
        chunk_index?: number;
        text_length?: number;
        relevance_rank?: number;
    }>;
    context_utilization?: number;
    confidence?: number;
    faithfulness_score?: number;
    completeness_score?: number;
    missing_information?: string[];
    answer_type?: string;
    abstained?: boolean;
    reasoning_notes?: string;
}

interface DebugPanelProps {
    metrics: RAGMetrics | null;
    isLoading: boolean;
}

export default function DebugPanel({ metrics, isLoading }: DebugPanelProps) {
    // Check if this is LangGraph metrics or legacy RAG metrics
    const isLangGraphMetrics = metrics?.clarify_count !== undefined;

    // Set default expanded sections based on metric type
    const [expandedSections, setExpandedSections] = useState<Set<string>>(
        new Set(isLangGraphMetrics ? ['ingest', 'retrieve', 'route'] : ['chunks', 'scores'])
    );

    const toggleSection = (section: string) => {
        const newExpanded = new Set(expandedSections);
        if (newExpanded.has(section)) {
            newExpanded.delete(section);
        } else {
            newExpanded.add(section);
        }
        setExpandedSections(newExpanded);
    };

    const getScoreColor = (score: number) => {
        if (score >= 0.8) return 'text-green-600 bg-green-100';
        if (score >= 0.6) return 'text-yellow-600 bg-yellow-100';
        return 'text-red-600 bg-red-100';
    };

    const getScoreBar = (score: number) => {
        const percentage = Math.round(score * 100);
        return (
            <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                    className={`h-2 rounded-full ${score >= 0.8 ? 'bg-green-500' : score >= 0.6 ? 'bg-yellow-500' : 'bg-red-500'}`}
                    style={{ width: `${percentage}%` }}
                ></div>
            </div>
        );
    };

    if (isLoading) {
        return (
            <div className="bg-gray-50 rounded-lg p-4 h-full">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">System Debug</h3>
                <div className="flex items-center justify-center h-32">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                </div>
            </div>
        );
    }

    if (!metrics) {
        return (
            <div className="bg-gray-50 rounded-lg p-4 h-full">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">System Debug</h3>
                <div className="text-center text-gray-500 py-8">
                    <div className="text-4xl mb-4">🔍</div>
                    <p>Send a message to see debug information</p>
                </div>
            </div>
        );
    }

    // If LangGraph metrics but no meaningful data, show a message
    if (isLangGraphMetrics && !metrics.ingest_metrics && !metrics.retrieve_metrics && !metrics.route_metrics) {
        return (
            <div className="bg-gray-50 rounded-lg p-4 h-full">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">System Debug</h3>
                <div className="text-center text-gray-500 py-8">
                    <div className="text-4xl mb-4">🤖</div>
                    <p>Waiting for conversation data...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="bg-gray-50 rounded-lg p-4 h-full overflow-y-auto">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">System Debug</h3>

            {isLangGraphMetrics ? (
                <>
                    {/* Ingest Node Metrics */}
                    {metrics.ingest_metrics && (
                        <div className="mb-6">
                            <button
                                onClick={() => toggleSection('ingest')}
                                className="flex items-center justify-between w-full text-left font-medium text-gray-900 mb-2"
                            >
                                <span>📥 Ingest Node</span>
                                <span className={`transform transition-transform ${expandedSections.has('ingest') ? 'rotate-180' : ''}`}>
                                    ▼
                                </span>
                            </button>
                            {expandedSections.has('ingest') && (
                                <div className="space-y-3">
                                    <div className="bg-white rounded-lg p-3 border">
                                        <div className="space-y-2 text-sm">
                                            <div>
                                                <span className="font-medium">Original Question:</span>
                                                <div className="mt-1 p-2 bg-gray-50 rounded text-xs">
                                                    {metrics.ingest_metrics.original_question || 'N/A'}
                                                </div>
                                            </div>
                                            <div>
                                                <span className="font-medium">Processed Question:</span>
                                                <div className="mt-1 p-2 bg-blue-50 rounded text-xs">
                                                    {metrics.ingest_metrics.processed_question || 'N/A'}
                                                </div>
                                            </div>
                                            <div className="grid grid-cols-2 gap-4">
                                                <div>
                                                    <span className="font-medium">Rephrased:</span>
                                                    <span className={`ml-2 px-2 py-1 rounded text-xs ${metrics.ingest_metrics.rephrased ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                                                        {metrics.ingest_metrics.rephrased ? 'Yes' : 'No'}
                                                    </span>
                                                </div>
                                                <div>
                                                    <span className="font-medium">Clarification Response:</span>
                                                    <span className={`ml-2 px-2 py-1 rounded text-xs ${metrics.ingest_metrics.is_clarification_response ? 'bg-yellow-100 text-yellow-800' : 'bg-gray-100 text-gray-800'}`}>
                                                        {metrics.ingest_metrics.is_clarification_response ? 'Yes' : 'No'}
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* Retrieve Node Metrics */}
                    {metrics.retrieve_metrics && (
                        <div className="mb-6">
                            <button
                                onClick={() => toggleSection('retrieve')}
                                className="flex items-center justify-between w-full text-left font-medium text-gray-900 mb-2"
                            >
                                <span>🔍 Retrieve Node ({metrics.retrieve_metrics.chunks_retrieved || 0} chunks)</span>
                                <span className={`transform transition-transform ${expandedSections.has('retrieve') ? 'rotate-180' : ''}`}>
                                    ▼
                                </span>
                            </button>
                            {expandedSections.has('retrieve') && (
                                <div className="space-y-3">
                                    <div className="bg-white rounded-lg p-3 border">
                                        <div className="space-y-3 text-sm">
                                            <div className="grid grid-cols-3 gap-4">
                                                <div>
                                                    <span className="font-medium">Avg Similarity:</span>
                                                    <div className="mt-1">
                                                        <span className={`px-2 py-1 rounded text-xs ${getScoreColor(metrics.retrieve_metrics.avg_similarity || 0)}`}>
                                                            {(metrics.retrieve_metrics.avg_similarity || 0).toFixed(3)}
                                                        </span>
                                                        {getScoreBar(metrics.retrieve_metrics.avg_similarity || 0)}
                                                    </div>
                                                </div>
                                                <div>
                                                    <span className="font-medium">Max Similarity:</span>
                                                    <div className="mt-1">
                                                        <span className={`px-2 py-1 rounded text-xs ${getScoreColor(metrics.retrieve_metrics.max_similarity || 0)}`}>
                                                            {(metrics.retrieve_metrics.max_similarity || 0).toFixed(3)}
                                                        </span>
                                                    </div>
                                                </div>
                                                <div>
                                                    <span className="font-medium">Min Similarity:</span>
                                                    <div className="mt-1">
                                                        <span className={`px-2 py-1 rounded text-xs ${getScoreColor(metrics.retrieve_metrics.min_similarity || 0)}`}>
                                                            {(metrics.retrieve_metrics.min_similarity || 0).toFixed(3)}
                                                        </span>
                                                    </div>
                                                </div>
                                            </div>
                                            <div className="grid grid-cols-2 gap-4">
                                                <div>
                                                    <span className="font-medium">Top K:</span>
                                                    <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">
                                                        {metrics.retrieve_metrics.top_k || 0}
                                                    </span>
                                                </div>
                                                <div>
                                                    <span className="font-medium">Context Length:</span>
                                                    <span className="ml-2 px-2 py-1 bg-gray-100 text-gray-800 rounded text-xs">
                                                        {metrics.retrieve_metrics.context_length || 0} chars
                                                    </span>
                                                </div>
                                            </div>
                                            {metrics.retrieve_metrics.chunk_scores && metrics.retrieve_metrics.chunk_scores.length > 0 && (
                                                <div>
                                                    <span className="font-medium">Chunk Scores:</span>
                                                    <div className="mt-1 flex flex-wrap gap-1">
                                                        {metrics.retrieve_metrics.chunk_scores.map((score, idx) => (
                                                            <span key={idx} className={`px-2 py-1 rounded text-xs ${getScoreColor(score)}`}>
                                                                C{idx + 1}: {score.toFixed(3)}
                                                            </span>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* Route Node Metrics */}
                    {metrics.route_metrics && (
                        <div className="mb-6">
                            <button
                                onClick={() => toggleSection('route')}
                                className="flex items-center justify-between w-full text-left font-medium text-gray-900 mb-2"
                            >
                                <span>🚦 Route Node ({metrics.route_metrics.route_decision || 'unknown'})</span>
                                <span className={`transform transition-transform ${expandedSections.has('route') ? 'rotate-180' : ''}`}>
                                    ▼
                                </span>
                            </button>
                            {expandedSections.has('route') && (
                                <div className="space-y-3">
                                    <div className="bg-white rounded-lg p-3 border">
                                        <div className="space-y-3 text-sm">
                                            <div className="grid grid-cols-2 gap-4">
                                                <div>
                                                    <span className="font-medium">Route Decision:</span>
                                                    <span className={`ml-2 px-2 py-1 rounded text-xs ${metrics.route_metrics.route_decision === 'answer' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}`}>
                                                        {metrics.route_metrics.route_decision || 'unknown'}
                                                    </span>
                                                </div>
                                                <div>
                                                    <span className="font-medium">Above Threshold:</span>
                                                    <span className={`ml-2 px-2 py-1 rounded text-xs ${metrics.route_metrics.above_threshold ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                                                        {metrics.route_metrics.above_threshold ? 'Yes' : 'No'}
                                                    </span>
                                                </div>
                                            </div>
                                            <div className="grid grid-cols-2 gap-4">
                                                <div>
                                                    <span className="font-medium">Avg Similarity:</span>
                                                    <div className="mt-1">
                                                        <span className={`px-2 py-1 rounded text-xs ${getScoreColor(metrics.route_metrics.avg_similarity || 0)}`}>
                                                            {(metrics.route_metrics.avg_similarity || 0).toFixed(3)}
                                                        </span>
                                                        {getScoreBar(metrics.route_metrics.avg_similarity || 0)}
                                                    </div>
                                                </div>
                                                <div>
                                                    <span className="font-medium">Threshold:</span>
                                                    <span className="ml-2 px-2 py-1 bg-gray-100 text-gray-800 rounded text-xs">
                                                        {metrics.route_metrics.threshold || 0}
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* Agent Overview */}
                    <div className="mb-6">
                        <button
                            onClick={() => toggleSection('agent')}
                            className="flex items-center justify-between w-full text-left font-medium text-gray-900 mb-2"
                        >
                            <span>🤖 Agent Overview</span>
                            <span className={`transform transition-transform ${expandedSections.has('agent') ? 'rotate-180' : ''}`}>
                                ▼
                            </span>
                        </button>
                        {expandedSections.has('agent') && (
                            <div className="space-y-3">
                                <div className="bg-white rounded-lg p-3 border">
                                    <div className="grid grid-cols-2 gap-4 text-sm">
                                        <div>
                                            <span className="font-medium">Clarify Count:</span>
                                            <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">
                                                {metrics.clarify_count || 0}
                                            </span>
                                        </div>
                                        <div>
                                            <span className="font-medium">Max Clarify:</span>
                                            <span className="ml-2 px-2 py-1 bg-gray-100 text-gray-800 rounded text-xs">
                                                {metrics.max_clarify || 0}
                                            </span>
                                        </div>
                                        <div>
                                            <span className="font-medium">Threshold:</span>
                                            <span className="ml-2 px-2 py-1 bg-gray-100 text-gray-800 rounded text-xs">
                                                {metrics.threshold || 0}
                                            </span>
                                        </div>
                                        <div>
                                            <span className="font-medium">Top K:</span>
                                            <span className="ml-2 px-2 py-1 bg-gray-100 text-gray-800 rounded text-xs">
                                                {metrics.top_k || 0}
                                            </span>
                                        </div>
                                        <div className="col-span-2">
                                            <span className="font-medium">Conversation Length:</span>
                                            <span className="ml-2 px-2 py-1 bg-green-100 text-green-800 rounded text-xs">
                                                {metrics.conversation_length || 0} messages
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </>
            ) : (
                // Legacy RAG Metrics Display (unchanged)
                <div className="text-center text-gray-500 py-8">
                    <div className="text-4xl mb-4">📊</div>
                    <p>Legacy RAG metrics not implemented</p>
                </div>
            )}
        </div>
    );
}
