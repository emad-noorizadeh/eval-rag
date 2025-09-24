/**
 * Debug Panel Component with Integrated Detailed Node Metrics
 * Author: Emad Noorizadeh
 */

'use client';

import { useState } from 'react';
import HighlightedText from './HighlightedText';

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
    context_utilization?: number | string | any[] | {
        precision_token?: number | null;
        recall_snippet?: number | null;
        numeric_match?: number | null;
        per_sentence?: number[];
        summary?: string;
    };
    confidence?: number;
    faithfulness?: number;  // Updated from faithfulness_score
    completeness?: number;  // Updated from completeness_score
    missing_information?: string | string[];
    answer_type?: string;
    abstained?: boolean;
    reasoning_notes?: string;
}

interface DebugPanelProps {
    metrics: RAGMetrics | null;
    isLoading: boolean;
    generatedBy?: string;
}

export default function DebugPanel({ metrics, isLoading, generatedBy }: DebugPanelProps) {

    // Check if this is LangGraph metrics or legacy RAG metrics
    const isLangGraphMetrics = metrics?.ingest_metrics !== undefined ||
        metrics?.retrieve_metrics !== undefined ||
        metrics?.route_metrics !== undefined ||
        metrics?.clarify_metrics !== undefined ||
        metrics?.rag_metrics !== undefined;

    // Set default expanded sections based on metric type
    const [expandedSections, setExpandedSections] = useState<Set<string>>(
        new Set(isLangGraphMetrics ? ['chunks', 'scores', 'analysis', 'supported'] : ['chunks', 'scores'])
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

    const getScoreColor = (score: number | string) => {
        // Handle string values
        if (typeof score === 'string') {
            const lowerScore = score.toLowerCase();
            if (lowerScore === 'high') return 'text-green-600 bg-green-100';
            if (lowerScore === 'medium') return 'text-yellow-600 bg-yellow-100';
            if (lowerScore === 'low') return 'text-red-600 bg-red-100';
            return 'text-gray-600 bg-gray-100'; // Unknown or other values
        }

        // Handle number values
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
                // LangGraph Metrics Display with Detailed Node Information
                <>
                    {/* Ingest Node - Show in Chunks Retrieved section */}
                    {metrics.ingest_metrics && (
                        <div className="mb-6">
                            <button
                                onClick={() => toggleSection('chunks')}
                                className="flex items-center justify-between w-full text-left font-medium text-gray-900 mb-2"
                            >
                                <span>📥 Ingest Node</span>
                                <span className={`transform transition-transform ${expandedSections.has('chunks') ? 'rotate-180' : ''}`}>
                                    ▼
                                </span>
                            </button>
                            {expandedSections.has('chunks') && (
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

                    {/* Chunks Retrieved - Show retrieved chunks */}
                    {metrics.chunks_retrieved && metrics.chunks_retrieved.length > 0 && (
                        <div className="mb-6">
                            <button
                                onClick={() => toggleSection('chunks')}
                                className="flex items-center justify-between w-full text-left font-medium text-gray-900 mb-2"
                            >
                                <span>📄 Chunks Retrieved ({metrics.chunks_retrieved.length})</span>
                                <span className={`transform transition-transform ${expandedSections.has('chunks') ? 'rotate-180' : ''}`}>
                                    ▼
                                </span>
                            </button>
                            {expandedSections.has('chunks') && (
                                <div className="space-y-3">
                                    {metrics.chunks_retrieved.map((chunk, idx) => (
                                        <div key={idx} className="bg-white rounded-lg p-3 border">
                                            <div className="flex justify-between items-start mb-2">
                                                <span className="font-medium text-sm text-gray-700">Chunk {chunk.chunk_index || idx + 1}</span>
                                                <span className={`px-2 py-1 rounded text-xs ${getScoreColor(chunk.similarity_score || 0)}`}>
                                                    {chunk.similarity_score !== null && chunk.similarity_score !== undefined ?
                                                        chunk.similarity_score.toFixed(3) :
                                                        (chunk.score || 0).toFixed(3)
                                                    }
                                                </span>
                                            </div>
                                            <div className="text-xs text-gray-600 mb-2">
                                                {metrics.context_utilization &&
                                                    typeof metrics.context_utilization === 'object' &&
                                                    'supported_terms_per_sentence' in metrics.context_utilization ? (
                                                    <HighlightedText
                                                        text={chunk.text?.substring(0, 200) + '...' || ''}
                                                        supportedTerms={metrics.context_utilization.supported_terms_per_sentence?.flatMap(s => s.supported_terms) || []}
                                                        supportedEntities={metrics.context_utilization.supported_entities?.items || []}
                                                        className="text-xs"
                                                    />
                                                ) : (
                                                    <span>{chunk.text?.substring(0, 200)}...</span>
                                                )}
                                            </div>
                                            <div className="text-xs text-gray-500">
                                                Length: {chunk.text_length || 0} chars
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    {/* RAG Scores */}
                    <div className="mb-6">
                        <button
                            onClick={() => toggleSection('scores')}
                            className="flex items-center justify-between w-full text-left font-medium text-gray-900 mb-2"
                        >
                            <span>📊 RAG Scores</span>
                            <span className={`transform transition-transform ${expandedSections.has('scores') ? 'rotate-180' : ''}`}>
                                ▼
                            </span>
                        </button>
                        {expandedSections.has('scores') && (
                            <div className="space-y-4">
                                <div className="bg-white rounded-lg p-4 border">
                                    <div className="space-y-4">
                                        <div>
                                            <div className="flex justify-between items-center mb-1">
                                                <span className="font-medium">Confidence</span>
                                                <span className={`text-sm font-medium ${getScoreColor(metrics.confidence || 0)}`}>
                                                    {typeof metrics.confidence === 'number'
                                                        ? (metrics.confidence || 0).toFixed(3)
                                                        : metrics.confidence || 'Unknown'}
                                                </span>
                                            </div>
                                            {typeof metrics.confidence === 'number' && getScoreBar(metrics.confidence || 0)}
                                        </div>
                                        <div>
                                            <div className="flex justify-between items-center mb-1">
                                                <span className="font-medium">Faithfulness</span>
                                                <span className={`text-sm font-medium ${getScoreColor(metrics.faithfulness || 0)}`}>
                                                    {(() => {
                                                        // For clarification or abstained cases, show N/A
                                                        if (metrics.answer_type === 'clarification' || metrics.abstained === true) {
                                                            return 'N/A';
                                                        }
                                                        return metrics.faithfulness !== null && metrics.faithfulness !== undefined ?
                                                            metrics.faithfulness.toFixed(3) :
                                                            'N/A';
                                                    })()}
                                                </span>
                                            </div>
                                            {(() => {
                                                // For clarification or abstained cases, don't show progress bar
                                                if (metrics.answer_type === 'clarification' || metrics.abstained === true) {
                                                    return null;
                                                }
                                                return getScoreBar(metrics.faithfulness || 0);
                                            })()}
                                        </div>
                                        <div>
                                            <div className="flex justify-between items-center mb-1">
                                                <span className="font-medium">Completeness</span>
                                                <span className={`text-sm font-medium ${getScoreColor(metrics.completeness || 0)}`}>
                                                    {(() => {
                                                        // For clarification or abstained cases, show N/A
                                                        if (metrics.answer_type === 'clarification' || metrics.abstained === true) {
                                                            return 'N/A';
                                                        }
                                                        return metrics.completeness !== null && metrics.completeness !== undefined ?
                                                            metrics.completeness.toFixed(3) :
                                                            'N/A';
                                                    })()}
                                                </span>
                                            </div>
                                            {(() => {
                                                // For clarification or abstained cases, don't show progress bar
                                                if (metrics.answer_type === 'clarification' || metrics.abstained === true) {
                                                    return null;
                                                }
                                                return getScoreBar(metrics.completeness || 0);
                                            })()}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Analysis */}
                    <div className="mb-6">
                        <button
                            onClick={() => toggleSection('analysis')}
                            className="flex items-center justify-between w-full text-left font-medium text-gray-900 mb-2"
                        >
                            <span>📈 Analysis</span>
                            <span className={`transform transition-transform ${expandedSections.has('analysis') ? 'rotate-180' : ''}`}>
                                ▼
                            </span>
                        </button>
                        {expandedSections.has('analysis') && (
                            <div className="space-y-4">
                                {/* Basic Analysis */}
                                <div className="bg-white rounded-lg p-4 border">
                                    <div className="space-y-4">
                                        <div className="flex justify-between items-center">
                                            <span className="font-medium">Answer Type</span>
                                            <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded text-sm font-medium">
                                                {metrics.answer_type || 'unknown'}
                                            </span>
                                        </div>
                                        {generatedBy && (
                                            <div className="flex justify-between items-center">
                                                <span className="font-medium">Generated By</span>
                                                <span className="px-3 py-1 bg-purple-100 text-purple-800 rounded text-sm font-medium">
                                                    {generatedBy}
                                                </span>
                                            </div>
                                        )}
                                        <div className="flex justify-between items-center">
                                            <span className="font-medium">Abstained</span>
                                            <span className={`px-3 py-1 rounded text-sm font-medium ${metrics.abstained ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'}`}>
                                                {metrics.abstained ? 'Yes' : 'No'}
                                            </span>
                                        </div>
                                        {metrics.missing_information && (
                                            Array.isArray(metrics.missing_information) ?
                                                metrics.missing_information.length > 0 :
                                                typeof metrics.missing_information === 'string' && metrics.missing_information.trim()
                                        ) && (
                                                <div>
                                                    <span className="font-medium">Missing Information</span>
                                                    <div className="mt-2">
                                                        <div className="text-sm text-gray-600 bg-yellow-50 border border-yellow-200 rounded p-2">
                                                            {Array.isArray(metrics.missing_information) ?
                                                                metrics.missing_information.map((item, index) => (
                                                                    <div key={index} className="mb-1">
                                                                        • {item}
                                                                    </div>
                                                                )) :
                                                                metrics.missing_information
                                                            }
                                                        </div>
                                                    </div>
                                                </div>
                                            )}
                                    </div>
                                </div>

                                {/* Advanced Analysis */}
                                {(() => {
                                    const ctx = metrics.context_utilization;
                                    if (ctx && typeof ctx === 'object' && ctx.summary) {
                                        return (
                                            <div className="bg-white rounded-lg p-4 border">
                                                <h4 className="font-medium text-gray-900 mb-4">🔍 Advanced Analysis</h4>

                                                {/* Summary */}
                                                <div className="mb-4">
                                                    <div className="flex justify-between items-center mb-2">
                                                        <span className="font-medium">Summary</span>
                                                    </div>
                                                    <div className="text-sm text-gray-600 bg-blue-50 border border-blue-200 rounded p-3">
                                                        {ctx.summary}
                                                    </div>
                                                </div>

                                                {/* Core Metrics */}
                                                <div className="grid grid-cols-2 gap-4 mb-4">
                                                    <div>
                                                        <div className="flex justify-between items-center mb-1">
                                                            <span className="text-sm font-medium">Precision Token</span>
                                                            <span className="text-sm text-gray-600">
                                                                {ctx.precision_token !== null && !isNaN(ctx.precision_token) ? `${(ctx.precision_token * 100).toFixed(1)}%` : 'N/A'}
                                                            </span>
                                                        </div>
                                                        {ctx.precision_token !== null && !isNaN(ctx.precision_token) && getScoreBar(ctx.precision_token)}
                                                    </div>
                                                    <div>
                                                        <div className="flex justify-between items-center mb-1">
                                                            <span className="text-sm font-medium">Recall Context</span>
                                                            <span className="text-sm text-gray-600">
                                                                {ctx.recall_context !== null && !isNaN(ctx.recall_context) ? `${(ctx.recall_context * 100).toFixed(1)}%` : 'N/A'}
                                                            </span>
                                                        </div>
                                                        {ctx.recall_context !== null && !isNaN(ctx.recall_context) && getScoreBar(ctx.recall_context)}
                                                    </div>
                                                    <div>
                                                        <div className="flex justify-between items-center mb-1">
                                                            <span className="text-sm font-medium">Numeric Match</span>
                                                            <span className="text-sm text-gray-600">
                                                                {ctx.numeric_match !== null && !isNaN(ctx.numeric_match) ? `${(ctx.numeric_match * 100).toFixed(1)}%` : 'N/A'}
                                                            </span>
                                                        </div>
                                                        {ctx.numeric_match !== null && !isNaN(ctx.numeric_match) && getScoreBar(ctx.numeric_match)}
                                                    </div>
                                                    <div>
                                                        <div className="flex justify-between items-center mb-1">
                                                            <span className="text-sm font-medium">Entity Match</span>
                                                            <span className="text-sm text-gray-600">
                                                                {ctx.entity_match && ctx.entity_match.overall !== null ? `${(ctx.entity_match.overall * 100).toFixed(1)}%` : 'N/A'}
                                                            </span>
                                                        </div>
                                                        {ctx.entity_match && ctx.entity_match.overall !== null && getScoreBar(ctx.entity_match.overall)}
                                                    </div>
                                                </div>

                                                {/* Entity Analysis */}
                                                {ctx.entity_match && (
                                                    <div className="mb-4">
                                                        <div className="font-medium mb-2">🏷️ Entity Analysis</div>
                                                        <div className="space-y-2">
                                                            <div className="text-sm">
                                                                <span className="font-medium">Overall Coverage: </span>
                                                                <span className="text-gray-600">
                                                                    {ctx.entity_match.overall !== null && ctx.entity_match.overall !== undefined ? `${(ctx.entity_match.overall * 100).toFixed(1)}%` : 'N/A'}
                                                                </span>
                                                            </div>
                                                            {ctx.entity_match.by_type && Object.keys(ctx.entity_match.by_type).length > 0 && (
                                                                <div>
                                                                    <div className="text-sm font-medium mb-1">By Type:</div>
                                                                    <div className="grid grid-cols-2 gap-2 text-xs">
                                                                        {Object.entries(ctx.entity_match.by_type).map(([type, score]) => (
                                                                            <div key={type} className="flex justify-between">
                                                                                <span className="capitalize">{type}:</span>
                                                                                <span className="text-gray-600">{(score * 100).toFixed(1)}%</span>
                                                                            </div>
                                                                        ))}
                                                                    </div>
                                                                </div>
                                                            )}
                                                            {ctx.entity_match.unsupported && Array.isArray(ctx.entity_match.unsupported) && ctx.entity_match.unsupported.length > 0 && (
                                                                <div>
                                                                    <div className="text-sm font-medium mb-1">Unsupported Entities:</div>
                                                                    <div className="text-xs text-red-600 bg-red-50 border border-red-200 rounded p-2">
                                                                        {ctx.entity_match.unsupported.map((entity, index) => (
                                                                            <div key={index}>• {entity}</div>
                                                                        ))}
                                                                    </div>
                                                                </div>
                                                            )}
                                                        </div>
                                                    </div>
                                                )}

                                                {/* Question-Answer Alignment */}
                                                {ctx.qr_alignment && (
                                                    <div className="mb-4">
                                                        <div className="font-medium mb-2">🔄 Question-Answer Alignment</div>
                                                        <div className="grid grid-cols-2 gap-4 text-sm">
                                                            <div>
                                                                <span className="font-medium">TF-IDF Cosine: </span>
                                                                <span className="text-gray-600">
                                                                    {ctx.qr_alignment.cosine_tfidf !== null && ctx.qr_alignment.cosine_tfidf !== undefined ? ctx.qr_alignment.cosine_tfidf.toFixed(3) : 'N/A'}
                                                                </span>
                                                            </div>
                                                            <div>
                                                                <span className="font-medium">Answer Covers Question: </span>
                                                                <span className="text-gray-600">
                                                                    {ctx.qr_alignment.answer_covers_question !== null && ctx.qr_alignment.answer_covers_question !== undefined ? `${(ctx.qr_alignment.answer_covers_question * 100).toFixed(1)}%` : 'N/A'}
                                                                </span>
                                                            </div>
                                                            <div>
                                                                <span className="font-medium">Embedding Cosine: </span>
                                                                <span className="text-gray-600">
                                                                    {ctx.qr_alignment.cosine_embed !== null && ctx.qr_alignment.cosine_embed !== undefined ? ctx.qr_alignment.cosine_embed.toFixed(3) : 'N/A'}
                                                                </span>
                                                            </div>
                                                            <div>
                                                                <span className="font-medium">Semantic Coverage: </span>
                                                                <span className="text-gray-600">
                                                                    {ctx.qr_alignment.answer_covers_question_sem !== null && ctx.qr_alignment.answer_covers_question_sem !== undefined ? `${(ctx.qr_alignment.answer_covers_question_sem * 100).toFixed(1)}%` : 'N/A'}
                                                                </span>
                                                            </div>
                                                        </div>
                                                    </div>
                                                )}

                                                {/* Per-Sentence Analysis */}
                                                {ctx.per_sentence && ctx.per_sentence.length > 0 && (
                                                    <div className="mb-4">
                                                        <div className="font-medium mb-2">📝 Per-Sentence Precision</div>
                                                        <div className="text-sm text-gray-600">
                                                            {ctx.per_sentence.map((score, index) => (
                                                                <span key={index} className="inline-block mr-2 mb-1 px-2 py-1 bg-gray-100 rounded text-xs">
                                                                    S{index + 1}: {(score * 100).toFixed(1)}%
                                                                </span>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}

                                                {/* Unsupported Terms */}
                                                {ctx.unsupported_terms && Array.isArray(ctx.unsupported_terms) && ctx.unsupported_terms.length > 0 && (
                                                    <div className="mb-4">
                                                        <div className="font-medium mb-2">❌ Unsupported Terms</div>
                                                        <div className="text-xs space-y-1">
                                                            {ctx.unsupported_terms.slice(0, 10).map((term, index) => (
                                                                <div key={index} className="flex justify-between items-center bg-red-50 border border-red-200 rounded p-2">
                                                                    <span className="font-mono">{term.term || 'Unknown'}</span>
                                                                    <div className="text-gray-600">
                                                                        <span className="mr-2">count: {term.count || 0}</span>
                                                                        <span className="mr-2">idf: {term.idf ? term.idf.toFixed(2) : 'N/A'}</span>
                                                                        <span>impact: {term.impact ? term.impact.toFixed(2) : 'N/A'}</span>
                                                                    </div>
                                                                </div>
                                                            ))}
                                                            {ctx.unsupported_terms.length > 10 && (
                                                                <div className="text-gray-500 text-center">
                                                                    ... and {ctx.unsupported_terms.length - 10} more terms
                                                                </div>
                                                            )}
                                                        </div>
                                                    </div>
                                                )}

                                                {/* Unsupported Numbers */}
                                                {ctx.unsupported_numbers && Array.isArray(ctx.unsupported_numbers) && ctx.unsupported_numbers.length > 0 && (
                                                    <div className="mb-4">
                                                        <div className="font-medium mb-2">🔢 Unsupported Numbers</div>
                                                        <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded p-2">
                                                            {ctx.unsupported_numbers.map((num, index) => (
                                                                <div key={index}>• {num || 'Unknown'}</div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}
                                            </div>
                                        );
                                    } else {
                                        // Fallback for simple context utilization
                                        return (
                                            <div className="bg-white rounded-lg p-4 border">
                                                <div>
                                                    <span className="font-medium">Context Utilization</span>
                                                    <div className="mt-2">
                                                        <div className="flex justify-between items-center mb-1">
                                                            <span className="text-sm text-gray-600">
                                                                {(() => {
                                                                    // For clarification or abstained cases, show N/A
                                                                    if (metrics.answer_type === 'clarification' || metrics.abstained === true) {
                                                                        return 'N/A';
                                                                    }
                                                                    if (typeof ctx === 'string') {
                                                                        return ctx;
                                                                    } else if (typeof ctx === 'number') {
                                                                        return `${ctx.toFixed(1)}%`;
                                                                    } else if (Array.isArray(ctx)) {
                                                                        return 'Array data';
                                                                    } else {
                                                                        return 'N/A';
                                                                    }
                                                                })()} - {
                                                                    (() => {
                                                                        // For clarification or abstained cases, show Not Available
                                                                        if (metrics.answer_type === 'clarification' || metrics.abstained === true) {
                                                                            return 'Not Available (No answer generated)';
                                                                        }
                                                                        if (typeof ctx === 'string') {
                                                                            return 'Context utilization from backend';
                                                                        } else if (typeof ctx === 'number') {
                                                                            return (ctx >= 0.8 ? 'High' : ctx >= 0.6 ? 'Moderate' : 'Low') + ' utilization of retrieved context';
                                                                        } else if (Array.isArray(ctx)) {
                                                                            return 'Array data received';
                                                                        } else {
                                                                            return 'Unknown';
                                                                        }
                                                                    })()
                                                                }
                                                            </span>
                                                        </div>
                                                        {(() => {
                                                            if (typeof ctx === 'number') {
                                                                return getScoreBar(ctx || 0);
                                                            }
                                                            return null;
                                                        })()}
                                                    </div>
                                                </div>
                                            </div>
                                        );
                                    }
                                })()}
                            </div>
                        )}
                    </div>

                    {/* Supported Terms and Entities */}
                    {metrics.context_utilization &&
                        typeof metrics.context_utilization === 'object' &&
                        'supported_terms' in metrics.context_utilization && (
                            <div className="mb-6">
                                <button
                                    onClick={() => toggleSection('supported')}
                                    className="flex items-center justify-between w-full text-left font-medium text-gray-900 mb-2"
                                >
                                    <span>🎯 Supported Terms & Entities</span>
                                    <span className={`transform transition-transform ${expandedSections.has('supported') ? 'rotate-180' : ''}`}>
                                        ▼
                                    </span>
                                </button>
                                {expandedSections.has('supported') && (
                                    <div className="space-y-4">
                                        {/* Color Legend */}
                                        <div className="bg-gray-50 rounded-lg p-3 border">
                                            <div className="text-sm font-medium text-gray-700 mb-2">🎨 Color Coding:</div>
                                            <div className="flex flex-wrap gap-4 text-xs">
                                                <div className="flex items-center gap-2">
                                                    <div className="w-4 h-4 bg-blue-200 border border-blue-300 rounded"></div>
                                                    <span className="text-gray-600">Blue = Supported Terms</span>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <div className="w-4 h-4 bg-green-200 border border-green-300 rounded"></div>
                                                    <span className="text-gray-600">Green = Supported Entities</span>
                                                </div>
                                            </div>
                                            <div className="mt-2 text-xs text-gray-500">
                                                Terms and entities highlighted in the chat are grounded in the retrieved context.
                                            </div>
                                        </div>
                                        {/* Supported Terms */}
                                        {metrics.context_utilization.supported_terms &&
                                            metrics.context_utilization.supported_terms.length > 0 && (
                                                <div className="bg-white rounded-lg p-4 border">
                                                    <div className="font-medium mb-3">📝 Supported Terms</div>
                                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                                        {metrics.context_utilization.supported_terms.slice(0, 10).map((term, index) => (
                                                            <div key={index} className="flex justify-between items-center bg-blue-50 border border-blue-200 rounded p-2">
                                                                <span className="font-mono text-sm">{term.term}</span>
                                                                <div className="text-xs text-gray-600">
                                                                    <span className="mr-2">count: {term.count}</span>
                                                                    <span>idf: {term.idf.toFixed(2)}</span>
                                                                </div>
                                                            </div>
                                                        ))}
                                                        {metrics.context_utilization.supported_terms.length > 10 && (
                                                            <div className="col-span-full text-center text-gray-500 text-sm">
                                                                ... and {metrics.context_utilization.supported_terms.length - 10} more terms
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                            )}

                                        {/* Supported Entities */}
                                        {metrics.context_utilization.supported_entities &&
                                            metrics.context_utilization.supported_entities.items &&
                                            metrics.context_utilization.supported_entities.items.length > 0 && (
                                                <div className="bg-white rounded-lg p-4 border">
                                                    <div className="font-medium mb-3">🏷️ Supported Entities</div>
                                                    <div className="space-y-2">
                                                        {metrics.context_utilization.supported_entities.items.map((entity, index) => (
                                                            <div key={index} className="flex justify-between items-center bg-green-50 border border-green-200 rounded p-2">
                                                                <div>
                                                                    <span className="font-mono text-sm">{entity.text}</span>
                                                                    <span className="ml-2 px-2 py-1 bg-green-200 text-green-800 rounded text-xs">
                                                                        {entity.type}
                                                                    </span>
                                                                </div>
                                                                <div className="text-xs text-gray-600">
                                                                    [{entity.start}:{entity.end}]
                                                                </div>
                                                            </div>
                                                        ))}
                                                    </div>
                                                    <div className="mt-3 text-sm text-gray-600">
                                                        Total: {metrics.context_utilization.supported_entities.count} entities
                                                    </div>
                                                </div>
                                            )}

                                        {/* Per-Sentence Analysis */}
                                        {metrics.context_utilization.supported_terms_per_sentence &&
                                            metrics.context_utilization.supported_terms_per_sentence.length > 0 && (
                                                <div className="bg-white rounded-lg p-4 border">
                                                    <div className="font-medium mb-3">📄 Per-Sentence Analysis</div>
                                                    <div className="space-y-3">
                                                        {metrics.context_utilization.supported_terms_per_sentence.map((sentenceData, index) => (
                                                            <div key={index} className="border-l-4 border-blue-200 pl-3">
                                                                <div className="text-sm text-gray-700 mb-2">
                                                                    "{sentenceData.sentence.substring(0, 100)}{sentenceData.sentence.length > 100 ? '...' : ''}"
                                                                </div>
                                                                {sentenceData.supported_terms.length > 0 && (
                                                                    <div className="flex flex-wrap gap-1">
                                                                        {sentenceData.supported_terms.map((term, termIndex) => (
                                                                            <span
                                                                                key={termIndex}
                                                                                className="px-2 py-1 bg-blue-200 text-blue-900 rounded text-xs font-mono"
                                                                                title={`Position: [${term.start}:${term.end}]`}
                                                                            >
                                                                                {term.term}
                                                                            </span>
                                                                        ))}
                                                                    </div>
                                                                )}
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}
                                    </div>
                                )}
                            </div>
                        )}

                    {/* Reasoning Notes */}
                    <div className="mb-6">
                        <button
                            onClick={() => toggleSection('reasoning')}
                            className="flex items-center justify-between w-full text-left font-medium text-gray-900 mb-2"
                        >
                            <span>💭 Reasoning Notes</span>
                            <span className={`transform transition-transform ${expandedSections.has('reasoning') ? 'rotate-180' : ''}`}>
                                ▼
                            </span>
                        </button>
                        {expandedSections.has('reasoning') && (
                            <div className="bg-white rounded-lg p-4 border">
                                {metrics.reasoning_notes ? (
                                    <div className="text-sm text-gray-700">
                                        {metrics.reasoning_notes}
                                    </div>
                                ) : (
                                    <div className="text-sm text-gray-500 italic">
                                        No reasoning notes provided by the LLM
                                    </div>
                                )}
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
                                                            {chunk.similarity_score !== null && chunk.similarity_score !== undefined ?
                                                                chunk.similarity_score.toFixed(3) :
                                                                (chunk.score || 0).toFixed(3)
                                                            }
                                                        </span>
                                                    )}
                                                    {chunk.text_length && (
                                                        <span className="px-2 py-1 bg-gray-200 rounded">
                                                            {chunk.text_length} chars
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                            <div className="text-sm text-gray-700 line-clamp-3 mb-2">
                                                {metrics.context_utilization &&
                                                    typeof metrics.context_utilization === 'object' &&
                                                    'supported_terms_per_sentence' in metrics.context_utilization ? (
                                                    <HighlightedText
                                                        text={chunk.text || ''}
                                                        supportedTerms={metrics.context_utilization.supported_terms_per_sentence?.flatMap(s => s.supported_terms) || []}
                                                        supportedEntities={metrics.context_utilization.supported_entities?.items || []}
                                                        className="text-sm"
                                                    />
                                                ) : (
                                                    <span>{chunk.text}</span>
                                                )}
                                            </div>
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

                    {/* Scores - Only show for legacy RAG metrics */}
                    {(metrics.confidence !== undefined || metrics.faithfulness !== undefined || metrics.completeness !== undefined) && (
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
                                                    {typeof metrics.confidence === 'number'
                                                        ? metrics.confidence.toFixed(3)
                                                        : metrics.confidence}
                                                </span>
                                            </div>
                                            {typeof metrics.confidence === 'number' && getScoreBar(metrics.confidence)}
                                        </div>
                                    )}

                                    {metrics.faithfulness !== undefined && (
                                        <div>
                                            <div className="flex justify-between items-center mb-1">
                                                <span className="text-sm font-medium">Faithfulness</span>
                                                <span className={`text-sm px-2 py-1 rounded ${getScoreColor(metrics.faithfulness)}`}>
                                                    {(() => {
                                                        // For clarification or abstained cases, show N/A
                                                        if (metrics.answer_type === 'clarification' || metrics.abstained === true) {
                                                            return 'N/A';
                                                        }
                                                        return metrics.faithfulness !== null && metrics.faithfulness !== undefined ?
                                                            metrics.faithfulness.toFixed(3) :
                                                            'N/A';
                                                    })()}
                                                </span>
                                            </div>
                                            {(() => {
                                                // For clarification or abstained cases, don't show progress bar
                                                if (metrics.answer_type === 'clarification' || metrics.abstained === true) {
                                                    return null;
                                                }
                                                return getScoreBar(metrics.faithfulness);
                                            })()}
                                        </div>
                                    )}

                                    {metrics.completeness !== undefined && (
                                        <div>
                                            <div className="flex justify-between items-center mb-1">
                                                <span className="text-sm font-medium">Completeness</span>
                                                <span className={`text-sm px-2 py-1 rounded ${getScoreColor(metrics.completeness)}`}>
                                                    {(() => {
                                                        // For clarification or abstained cases, show N/A
                                                        if (metrics.answer_type === 'clarification' || metrics.abstained === true) {
                                                            return 'N/A';
                                                        }
                                                        return metrics.completeness !== null && metrics.completeness !== undefined ?
                                                            metrics.completeness.toFixed(3) :
                                                            'N/A';
                                                    })()}
                                                </span>
                                            </div>
                                            {(() => {
                                                // For clarification or abstained cases, don't show progress bar
                                                if (metrics.answer_type === 'clarification' || metrics.abstained === true) {
                                                    return null;
                                                }
                                                return getScoreBar(metrics.completeness);
                                            })()}
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    )}

                    {/* Analysis - Only show for legacy RAG metrics */}
                    {(metrics.answer_type !== undefined || metrics.context_utilization !== undefined || metrics.abstained !== undefined) && (
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
                                    {generatedBy && (
                                        <div className="bg-white rounded-lg p-3 border">
                                            <div className="flex justify-between items-center mb-2">
                                                <span className="text-sm font-medium">Generated By</span>
                                                <span className="px-2 py-1 bg-purple-100 text-purple-800 rounded text-xs">
                                                    {generatedBy}
                                                </span>
                                            </div>
                                        </div>
                                    )}

                                    {metrics.context_utilization !== undefined && (
                                        <div className="bg-white rounded-lg p-3 border">
                                            <div className="text-sm font-medium mb-2">Context Utilization</div>
                                            <div className="text-xs text-gray-600 bg-gray-50 p-2 rounded border">
                                                {(() => {
                                                    // For clarification or abstained cases, show N/A
                                                    if (metrics.answer_type === 'clarification' || metrics.abstained === true) {
                                                        return 'N/A';
                                                    }
                                                    const ctx = metrics.context_utilization;
                                                    if (typeof ctx === 'string') {
                                                        return ctx;
                                                    } else if (typeof ctx === 'number') {
                                                        return `${(ctx * 100).toFixed(1)}%`;
                                                    } else if (Array.isArray(ctx)) {
                                                        return 'Array data';
                                                    } else if (ctx && typeof ctx === 'object' && ctx.summary) {
                                                        return ctx.summary;
                                                    } else {
                                                        return 'N/A';
                                                    }
                                                })()} - {
                                                    (() => {
                                                        // For clarification or abstained cases, show Not Available
                                                        if (metrics.answer_type === 'clarification' || metrics.abstained === true) {
                                                            return 'Not Available (No answer generated)';
                                                        }
                                                        const ctx = metrics.context_utilization;
                                                        if (typeof ctx === 'string') {
                                                            return 'Context utilization from backend';
                                                        } else if (typeof ctx === 'number') {
                                                            return (ctx >= 0.8 ? 'High utilization of retrieved context' :
                                                                ctx >= 0.5 ? 'Moderate utilization of retrieved context' :
                                                                    'Low utilization of retrieved context');
                                                        } else if (Array.isArray(ctx)) {
                                                            return 'Array data received';
                                                        } else if (ctx && typeof ctx === 'object' && ctx.summary) {
                                                            return 'Advanced context utilization analysis';
                                                        } else {
                                                            return 'Unknown';
                                                        }
                                                    })()
                                                }
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

                                    {metrics.missing_information && Array.isArray(metrics.missing_information) && metrics.missing_information.length > 0 && (
                                        <div className="bg-white rounded-lg p-3 border">
                                            <div className="text-sm font-medium mb-2">Missing Information</div>
                                            <div className="text-xs text-gray-600 bg-yellow-50 border border-yellow-200 rounded p-2">
                                                {metrics.missing_information.map((item, index) => (
                                                    <div key={index} className="mb-1">
                                                        • {item}
                                                    </div>
                                                ))}
                                            </div>
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
                </>
            )}
        </div>
    );
}
