/**
 * Query Interface Component - RAG Document Search
 * Author: Emad Noorizadeh
 */

'use client';

import { useState } from 'react';

interface QueryResult {
    id: string;
    text: string;
    metadata: Record<string, any>;
    score: number;
    similarity_score: number;
}

interface QueryResponse {
    results: QueryResult[];
    query: string;
}

export default function QueryInterface() {
    const [query, setQuery] = useState('');
    const [nResults, setNResults] = useState(5);
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState<QueryResult[]>([]);
    const [error, setError] = useState('');
    const [expandedResults, setExpandedResults] = useState<Set<string>>(new Set());

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!query.trim()) return;

        setLoading(true);
        setError('');
        setResults([]);
        setExpandedResults(new Set());

        try {
            const response = await fetch('http://localhost:9000/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: query.trim(),
                    n_results: nResults,
                }),
            });

            if (response.ok) {
                const data: QueryResponse = await response.json();
                setResults(data.results);
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

    const toggleExpanded = (resultId: string) => {
        setExpandedResults(prev => {
            const newSet = new Set(prev);
            if (newSet.has(resultId)) {
                newSet.delete(resultId);
            } else {
                newSet.add(resultId);
            }
            return newSet;
        });
    };

    const getSimilarityColor = (score: number) => {
        if (score >= 0.8) return 'text-green-600 bg-green-100';
        if (score >= 0.6) return 'text-yellow-600 bg-yellow-100';
        if (score >= 0.4) return 'text-orange-600 bg-orange-100';
        return 'text-red-600 bg-red-100';
    };

    const getSimilarityLabel = (score: number) => {
        if (score >= 0.8) return 'Very High';
        if (score >= 0.6) return 'High';
        if (score >= 0.4) return 'Medium';
        if (score >= 0.2) return 'Low';
        return 'Very Low';
    };


    return (
        <div className="bg-white rounded-lg shadow-md p-6">
            <div className="mb-6">
                <h2 className="text-2xl font-semibold text-gray-900 mb-2">Document Query Testing</h2>
                <p className="text-gray-600">Test semantic search queries against the indexed documents in your data folder</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4 mb-6">
                <div>
                    <label htmlFor="query" className="block text-sm font-medium text-gray-700 mb-2">
                        Search Query *
                    </label>
                    <input
                        type="text"
                        id="query"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder="Test your query against the indexed documents..."
                        required
                    />
                </div>

                <div className="flex space-x-4">
                    <div className="flex-1">
                        <label htmlFor="nResults" className="block text-sm font-medium text-gray-700 mb-2">
                            Number of Results
                        </label>
                        <input
                            type="number"
                            id="nResults"
                            value={nResults}
                            onChange={(e) => setNResults(parseInt(e.target.value) || 5)}
                            min="1"
                            max="20"
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                    </div>
                    <div className="flex items-end">
                        <button
                            type="submit"
                            disabled={loading || !query.trim()}
                            className="px-6 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {loading ? (
                                <div className="flex items-center">
                                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                                    Testing...
                                </div>
                            ) : (
                                'Test Query'
                            )}
                        </button>
                    </div>
                </div>
            </form>

            {error && (
                <div className="mb-6 p-3 bg-red-100 text-red-700 border border-red-300 rounded-md">
                    {error}
                </div>
            )}

            {results.length > 0 && (
                <div className="space-y-4">
                    <div className="flex justify-between items-center">
                        <h3 className="text-lg font-semibold text-gray-900">
                            Query Results ({results.length} found)
                        </h3>
                        <div className="text-sm text-gray-500">
                            Query: "{query}"
                        </div>
                    </div>

                    {results.map((result, index) => {
                        const isExpanded = expandedResults.has(result.id);
                        const similarityScore = result.similarity_score || result.score || 0;
                        const similarityColor = getSimilarityColor(similarityScore);
                        const similarityLabel = getSimilarityLabel(similarityScore);

                        return (
                            <div key={result.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
                                <div className="flex justify-between items-start mb-3">
                                    <div className="flex items-center space-x-3">
                                        <span className="text-sm font-medium text-blue-600 bg-blue-100 px-2 py-1 rounded">
                                            #{index + 1}
                                        </span>
                                        <span className={`text-xs px-2 py-1 rounded-full ${similarityColor}`}>
                                            {similarityLabel} ({similarityScore.toFixed(3)})
                                        </span>
                                    </div>
                                    <button
                                        onClick={() => toggleExpanded(result.id)}
                                        className="text-gray-400 hover:text-gray-600 text-sm"
                                    >
                                        {isExpanded ? '▼' : '▶'} {isExpanded ? 'Show Less' : 'Show More'}
                                    </button>
                                </div>

                                <div className="text-gray-900 mb-3">
                                    {isExpanded ? (
                                        <p className="whitespace-pre-wrap">{result.text}</p>
                                    ) : (
                                        <p className="line-clamp-3">{result.text}</p>
                                    )}
                                </div>

                                {Object.keys(result.metadata).length > 0 && (
                                    <div className="text-sm text-gray-600 border-t border-gray-200 pt-3">
                                        <div className="flex items-center justify-between mb-2">
                                            <strong>Document Metadata:</strong>
                                            <span className="text-xs text-gray-500">
                                                ID: {result.id}
                                            </span>
                                        </div>
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
                                            {Object.entries(result.metadata).map(([key, value]) => (
                                                <div key={key} className="flex">
                                                    <span className="font-medium text-gray-700 mr-2">{key}:</span>
                                                    <span className="text-gray-600 truncate">
                                                        {typeof value === 'string' ? value : JSON.stringify(value)}
                                                    </span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            )}

            {!loading && results.length === 0 && query && (
                <div className="text-center py-8">
                    <div className="text-gray-400 mb-4">
                        <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                    </div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No results found</h3>
                    <p className="text-gray-500">Try adjusting your query or increasing the number of results.</p>
                </div>
            )}
        </div>
    );
}
