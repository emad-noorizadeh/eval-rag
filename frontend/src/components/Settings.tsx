/**
 * Settings Component - Display System Configuration
 * Author: Emad Noorizadeh
 */

'use client';

import { useState, useEffect } from 'react';

interface ChatConfig {
    retrieval_method: string;
    routing_strategy: string;
    retrieval_top_k: number;
    similarity_threshold: number;
    max_clarify: number;
    reclarify_threshold: number;
    window_k: number;
    hybrid_config: any;
    available_retrieval_methods: string[];
    available_routing_strategies: string[];
    db_path: string;
    collection_name: string;
}

interface ChunkingConfig {
    chunk_size: number;
    chunk_overlap: number;
    llamaindex_defaults: {
        chunk_size: number;
        chunk_overlap: number;
    };
    current_vs_defaults: {
        chunk_size: string;
        chunk_overlap: string;
    };
}

interface SystemInfo {
    count: number;
    collection_info: {
        collection_name: string;
        total_documents: number;
        database_path: string;
    };
}

export default function Settings() {
    const [chatConfig, setChatConfig] = useState<ChatConfig | null>(null);
    const [chunkingConfig, setChunkingConfig] = useState<ChunkingConfig | null>(null);
    const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetchAllConfig();
    }, []);

    const fetchAllConfig = async () => {
        try {
            setLoading(true);
            setError(null);

            // Fetch all configuration data in parallel
            const [chatResponse, chunkingResponse, documentsResponse] = await Promise.all([
                fetch('/api/chat-config').then(res => res.json()),
                fetch('/api/chunking-config').then(res => res.json()),
                fetch('/api/documents').then(res => res.json())
            ]);

            setChatConfig(chatResponse);
            setChunkingConfig(chunkingResponse);
            setSystemInfo(documentsResponse);

        } catch (err) {
            console.error('Error fetching configuration:', err);
            setError('Failed to load configuration data');
        } finally {
            setLoading(false);
        }
    };

    const formatValue = (value: any): string => {
        if (value === null || value === undefined) return 'N/A';
        if (typeof value === 'boolean') return value ? 'Yes' : 'No';
        if (typeof value === 'object') return JSON.stringify(value, null, 2);
        return String(value);
    };

    const getStatusColor = (value: any): string => {
        if (typeof value === 'boolean') return value ? 'text-green-600' : 'text-red-600';
        if (typeof value === 'number' && value > 0) return 'text-green-600';
        return 'text-gray-600';
    };

    if (loading) {
        return (
            <div className="max-w-6xl mx-auto p-6">
                <div className="bg-white rounded-lg shadow-sm p-6">
                    <div className="flex items-center justify-center">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                        <span className="ml-3 text-gray-600">Loading configuration...</span>
                    </div>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="max-w-6xl mx-auto p-6">
                <div className="bg-white rounded-lg shadow-sm p-6">
                    <div className="text-center">
                        <div className="text-red-500 text-xl mb-2">⚠️</div>
                        <p className="text-red-600">{error}</p>
                        <button
                            onClick={fetchAllConfig}
                            className="mt-4 px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors"
                        >
                            Retry
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="max-w-6xl mx-auto p-6 space-y-6">
            <div className="text-center mb-8">
                <h2 className="text-3xl font-bold text-gray-900 mb-2">System Configuration</h2>
                <p className="text-gray-600">Current system settings and status (Read-only)</p>
            </div>

            {/* System Information */}
            <div className="bg-white rounded-lg shadow-sm p-6">
                <h3 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                    <span className="text-2xl mr-2">🔧</span>
                    System Information
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-3">
                        <div className="flex justify-between items-center py-2 border-b border-gray-100">
                            <span className="font-medium text-gray-700">Database Path:</span>
                            <span className="text-sm text-gray-600 font-mono">{chatConfig?.db_path || 'Unknown'}</span>
                        </div>
                        <div className="flex justify-between items-center py-2 border-b border-gray-100">
                            <span className="font-medium text-gray-700">Collection Name:</span>
                            <span className="text-sm text-gray-600 font-mono">{chatConfig?.collection_name || 'Unknown'}</span>
                        </div>
                    </div>
                    <div className="space-y-3">
                        <div className="flex justify-between items-center py-2 border-b border-gray-100">
                            <span className="font-medium text-gray-700">Total Documents:</span>
                            <span className={`font-medium ${getStatusColor(systemInfo?.collection_info?.total_documents)}`}>
                                {formatValue(systemInfo?.collection_info?.total_documents)}
                            </span>
                        </div>
                        <div className="flex justify-between items-center py-2 border-b border-gray-100">
                            <span className="font-medium text-gray-700">Index Status:</span>
                            <span className="text-green-600 font-medium">
                                {systemInfo?.count > 0 ? 'Active' : 'Empty'}
                            </span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Chat Configuration */}
            {chatConfig && (
                <div className="bg-white rounded-lg shadow-sm p-6">
                    <h3 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                        <span className="text-2xl mr-2">💬</span>
                        Chat Agent Configuration
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-3">
                            <div className="flex justify-between items-center py-2 border-b border-gray-100">
                                <span className="font-medium text-gray-700">Retrieval Method:</span>
                                <span className="text-sm text-blue-600 font-medium bg-blue-50 px-2 py-1 rounded">
                                    {chatConfig.retrieval_method}
                                </span>
                            </div>
                            <div className="flex justify-between items-center py-2 border-b border-gray-100">
                                <span className="font-medium text-gray-700">Routing Strategy:</span>
                                <span className="text-sm text-blue-600 font-medium bg-blue-50 px-2 py-1 rounded">
                                    {chatConfig.routing_strategy}
                                </span>
                            </div>
                            <div className="flex justify-between items-center py-2 border-b border-gray-100">
                                <span className="font-medium text-gray-700">Retrieval Top K:</span>
                                <span className="text-sm text-gray-600 font-mono">{chatConfig.retrieval_top_k}</span>
                            </div>
                            <div className="flex justify-between items-center py-2 border-b border-gray-100">
                                <span className="font-medium text-gray-700">Similarity Threshold:</span>
                                <span className="text-sm text-gray-600 font-mono">{chatConfig.similarity_threshold}</span>
                            </div>
                        </div>
                        <div className="space-y-3">
                            <div className="flex justify-between items-center py-2 border-b border-gray-100">
                                <span className="font-medium text-gray-700">Max Clarify:</span>
                                <span className="text-sm text-gray-600 font-mono">{chatConfig.max_clarify}</span>
                            </div>
                            <div className="flex justify-between items-center py-2 border-b border-gray-100">
                                <span className="font-medium text-gray-700">Reclarify Threshold:</span>
                                <span className="text-sm text-gray-600 font-mono">{chatConfig.reclarify_threshold}</span>
                            </div>
                            <div className="flex justify-between items-center py-2 border-b border-gray-100">
                                <span className="font-medium text-gray-700">Window K:</span>
                                <span className="text-sm text-gray-600 font-mono">{chatConfig.window_k}</span>
                            </div>
                        </div>
                    </div>

                    {/* Hybrid Configuration */}
                    {chatConfig.retrieval_method === 'hybrid' && chatConfig.hybrid_config && (
                        <div className="mt-6">
                            <h4 className="font-medium text-gray-700 mb-3">Hybrid Retrieval Configuration:</h4>
                            <div className="bg-gray-50 rounded-lg p-4">
                                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                                    <div>
                                        <span className="font-medium text-gray-600">Embedding Results (k_embed):</span>
                                        <span className="ml-2 text-gray-800">{chatConfig.hybrid_config.k_embed}</span>
                                    </div>
                                    <div>
                                        <span className="font-medium text-gray-600">BM25 Chunk Results (k_bm25_chunk):</span>
                                        <span className="ml-2 text-gray-800">{chatConfig.hybrid_config.k_bm25_chunk}</span>
                                    </div>
                                    <div>
                                        <span className="font-medium text-gray-600">BM25 Metadata Results (k_bm25_meta_docs):</span>
                                        <span className="ml-2 text-gray-800">{chatConfig.hybrid_config.k_bm25_meta_docs}</span>
                                    </div>
                                    <div>
                                        <span className="font-medium text-gray-600">Final Results (k_final):</span>
                                        <span className="ml-2 text-gray-800">{chatConfig.hybrid_config.k_final}</span>
                                    </div>
                                    <div>
                                        <span className="font-medium text-gray-600">RRF Pool Size (k_rrf):</span>
                                        <span className="ml-2 text-gray-800">{chatConfig.hybrid_config.k_rrf}</span>
                                    </div>
                                </div>
                                <div className="mt-3 text-xs text-gray-500">
                                    <p><strong>Hybrid Method:</strong> Combines semantic search, BM25 on chunks, BM25 on metadata, and heuristics using Reciprocal Rank Fusion (RRF)</p>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Available Methods */}
                    <div className="mt-6">
                        <h4 className="font-medium text-gray-700 mb-3">Available Retrieval Methods:</h4>
                        <div className="flex flex-wrap gap-2">
                            {(chatConfig.available_retrieval_methods || []).map((method, index) => (
                                <span
                                    key={index}
                                    className={`px-3 py-1 rounded-full text-xs font-medium ${method === chatConfig.retrieval_method
                                        ? 'bg-blue-100 text-blue-800 border border-blue-200'
                                        : 'bg-gray-100 text-gray-600'
                                        }`}
                                >
                                    {method}
                                </span>
                            ))}
                        </div>
                    </div>

                    <div className="mt-4">
                        <h4 className="font-medium text-gray-700 mb-3">Available Routing Strategies:</h4>
                        <div className="flex flex-wrap gap-2">
                            {(chatConfig.available_routing_strategies || []).map((strategy, index) => (
                                <span
                                    key={index}
                                    className={`px-3 py-1 rounded-full text-xs font-medium ${strategy === chatConfig.routing_strategy
                                        ? 'bg-green-100 text-green-800 border border-green-200'
                                        : 'bg-gray-100 text-gray-600'
                                        }`}
                                >
                                    {strategy}
                                </span>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* Chunking Configuration */}
            {chunkingConfig && (
                <div className="bg-white rounded-lg shadow-sm p-6">
                    <h3 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                        <span className="text-2xl mr-2">✂️</span>
                        Document Chunking Configuration
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-3">
                            <div className="flex justify-between items-center py-2 border-b border-gray-100">
                                <span className="font-medium text-gray-700">Chunk Size:</span>
                                <span className="text-sm text-gray-600 font-mono">{chunkingConfig.chunk_size} characters</span>
                            </div>
                            <div className="flex justify-between items-center py-2 border-b border-gray-100">
                                <span className="font-medium text-gray-700">Chunk Overlap:</span>
                                <span className="text-sm text-gray-600 font-mono">{chunkingConfig.chunk_overlap} characters</span>
                            </div>
                        </div>
                        <div className="space-y-3">
                            <div className="flex justify-between items-center py-2 border-b border-gray-100">
                                <span className="font-medium text-gray-700">Current vs Defaults:</span>
                                <div className="text-sm text-gray-600">
                                    <div className="text-xs">{chunkingConfig.current_vs_defaults.chunk_size}</div>
                                    <div className="text-xs">{chunkingConfig.current_vs_defaults.chunk_overlap}</div>
                                </div>
                            </div>
                        </div>
                    </div>

                </div>
            )}
        </div>
    );
}
