/**
 * Debug Panel Component
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
        new Set(isLangGraphMetrics ? ['agent'] : ['chunks', 'scores'])
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
    if (isLangGraphMetrics && metrics.clarify_count === 0 && metrics.conversation_length === 0) {
        return (
            <div className="bg-gray-50 rounded-lg p-4 h-full">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">System Debug</h3>
                <div className="text-center text-gray-500 py-8">
                    <div className="text-4xl mb-4">📊</div>
                    <p>Waiting for conversation data...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="bg-gray-50 rounded-lg p-4 h-full overflow-y-auto">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">System Debug</h3>

            {isLangGraphMetrics ? (
                // LangGraph Metrics Display
                <>
                    {/* LangGraph Agent Metrics */}
                    <div className="mb-6">
                        <button
                            onClick={() => toggleSection('agent')}
                            className="flex items-center justify-between w-full text-left font-medium text-gray-900 mb-2"
                        >
                            <span>Agent Metrics</span>
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
                // Legacy RAG Metrics Display
                <>
                    {/* Chunks Retrieved */}
                    {metrics.chunks_retrieved && metrics.chunks_retrieved.length > 0 && (
                        <div className="mb-6">
                            <button
                                onClick={() => toggleSection('chunks')}
                                className="flex items-center justify-between w-full text-left font-medium text-gray-900 mb-2"
                            >
                                <span>Chunks Retrieved ({metrics.chunks_retrieved.length})</span>
                                <span className={`transform transition-transform ${expandedSections.has('chunks') ? 'rotate-180' : ''}`}>
                                    ▼
                                </span>
                            </button>
                            {expandedSections.has('chunks') && (
                                <div className="space-y-3">
                                    {metrics.chunks_retrieved.map((chunk, index) => (
                                        <div key={chunk.id} className="bg-white rounded-lg p-3 border">
                                            <div className="flex justify-between items-start mb-2">
                                                <span className="text-sm font-medium text-blue-600">Chunk {chunk.chunk_index || index + 1}</span>
                                                <div className="flex space-x-2 text-xs">
                                                    {chunk.similarity_score && (
                                                        <span className={`px-2 py-1 rounded ${getScoreColor(chunk.similarity_score)}`}>
                                                            {chunk.similarity_score.toFixed(3)}
                                                        </span>
                                                    )}
                                                    {chunk.text_length && (
                                                        <span className="px-2 py-1 bg-gray-200 rounded">
                                                            {chunk.text_length} chars
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                            <p className="text-sm text-gray-700 line-clamp-3 mb-2">{chunk.text}</p>
                                            {Object.keys(chunk.metadata).length > 0 && (
                                                <div className="text-xs text-gray-500">
                                                    <strong>Metadata:</strong> {JSON.stringify(chunk.metadata)}
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}
                </>
            )}

            {/* Scores - Only show for legacy RAG metrics */}
            {!isLangGraphMetrics && (metrics.confidence !== undefined || metrics.faithfulness_score !== undefined || metrics.completeness_score !== undefined) && (
                <div className="mb-6">
                    <button
                        onClick={() => toggleSection('scores')}
                        className="flex items-center justify-between w-full text-left font-medium text-gray-900 mb-2"
                    >
                        <span>RAG Scores</span>
                        <span className={`transform transition-transform ${expandedSections.has('scores') ? 'rotate-180' : ''}`}>
                            ▼
                        </span>
                    </button>
                    {expandedSections.has('scores') && (
                        <div className="space-y-4">
                            {metrics.confidence !== undefined && (
                                <div>
                                    <div className="flex justify-between items-center mb-1">
                                        <span className="text-sm font-medium">Confidence</span>
                                        <span className={`text-sm px-2 py-1 rounded ${getScoreColor(metrics.confidence)}`}>
                                            {metrics.confidence.toFixed(3)}
                                        </span>
                                    </div>
                                    {getScoreBar(metrics.confidence)}
                                </div>
                            )}

                            {metrics.faithfulness_score !== undefined && (
                                <div>
                                    <div className="flex justify-between items-center mb-1">
                                        <span className="text-sm font-medium">Faithfulness</span>
                                        <span className={`text-sm px-2 py-1 rounded ${getScoreColor(metrics.faithfulness_score)}`}>
                                            {metrics.faithfulness_score.toFixed(3)}
                                        </span>
                                    </div>
                                    {getScoreBar(metrics.faithfulness_score)}
                                </div>
                            )}

                            {metrics.completeness_score !== undefined && (
                                <div>
                                    <div className="flex justify-between items-center mb-1">
                                        <span className="text-sm font-medium">Completeness</span>
                                        <span className={`text-sm px-2 py-1 rounded ${getScoreColor(metrics.completeness_score)}`}>
                                            {metrics.completeness_score.toFixed(3)}
                                        </span>
                                    </div>
                                    {getScoreBar(metrics.completeness_score)}
                                </div>
                            )}
                        </div>
                    )}
                </div>
            )}

            {/* Analysis - Only show for legacy RAG metrics */}
            {!isLangGraphMetrics && (metrics.answer_type !== undefined || metrics.context_utilization !== undefined || metrics.abstained !== undefined) && (
                <div className="mb-6">
                    <button
                        onClick={() => toggleSection('analysis')}
                        className="flex items-center justify-between w-full text-left font-medium text-gray-900 mb-2"
                    >
                        <span>Analysis</span>
                        <span className={`transform transition-transform ${expandedSections.has('analysis') ? 'rotate-180' : ''}`}>
                            ▼
                        </span>
                    </button>
                    {expandedSections.has('analysis') && (
                        <div className="space-y-3">
                            {metrics.answer_type && (
                                <div className="bg-white rounded-lg p-3 border">
                                    <div className="flex justify-between items-center mb-2">
                                        <span className="text-sm font-medium">Answer Type</span>
                                        <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">
                                            {metrics.answer_type}
                                        </span>
                                    </div>
                                </div>
                            )}

                            {metrics.context_utilization !== undefined && (
                                <div className="bg-white rounded-lg p-3 border">
                                    <div className="text-sm font-medium mb-2">Context Utilization</div>
                                    <div className="text-xs text-gray-600 bg-gray-50 p-2 rounded border">
                                        {metrics.context_utilization.toFixed(3)} - {metrics.context_utilization >= 0.8 ? 'High utilization of retrieved context' :
                                            metrics.context_utilization >= 0.5 ? 'Moderate utilization of retrieved context' :
                                                'Low utilization of retrieved context'}
                                    </div>
                                </div>
                            )}

                            {metrics.abstained !== undefined && (
                                <div className="bg-white rounded-lg p-3 border">
                                    <div className="flex justify-between items-center mb-2">
                                        <span className="text-sm font-medium">Abstained</span>
                                        <span className={`px-2 py-1 rounded text-xs ${metrics.abstained ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'}`}>
                                            {metrics.abstained ? 'Yes' : 'No'}
                                        </span>
                                    </div>
                                </div>
                            )}

                            {metrics.missing_information && metrics.missing_information.length > 0 && (
                                <div className="bg-white rounded-lg p-3 border">
                                    <div className="text-sm font-medium mb-2">Missing Information</div>
                                    <ul className="text-xs text-gray-600 space-y-1">
                                        {metrics.missing_information.map((item, index) => (
                                            <li key={index} className="flex items-start">
                                                <span className="text-red-500 mr-2">•</span>
                                                {item}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            )}

            {/* Reasoning Notes - Only show if available */}
            {metrics.reasoning_notes && (
                <div className="mb-6">
                    <button
                        onClick={() => toggleSection('reasoning')}
                        className="flex items-center justify-between w-full text-left font-medium text-gray-900 mb-2"
                    >
                        <span>Reasoning Notes</span>
                        <span className={`transform transition-transform ${expandedSections.has('reasoning') ? 'rotate-180' : ''}`}>
                            ▼
                        </span>
                    </button>
                    {expandedSections.has('reasoning') && (
                        <div className="bg-white rounded-lg p-3 border">
                            <p className="text-sm text-gray-700">{metrics.reasoning_notes}</p>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
