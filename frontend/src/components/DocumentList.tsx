/**
 * Document List Component - Shows files from data folder
 * Author: Emad Noorizadeh
 */

'use client';

import { useState, useEffect } from 'react';

interface DataFile {
    name: string;
    path: string;
    size_bytes: number;
    size_mb: number;
    modified: string;
    extension: string;
}

interface FileContent {
    filename: string;
    content: string;
    size_bytes: number;
    size_mb: number;
    modified: string;
    extension: string;
    line_count: number;
    word_count: number;
}

interface DocumentMetadata {
    doc_id: string;
    title: string;
    doc_type: string;
    domain: string;
    language: string;
    url: string | null;
    published_at: string | null;
    updated_at: string | null;
    effective_date: string | null;
    expires_at: string | null;
    geo_scope: string;
    currency: string;
    product_entities: string[];
    categories: string[];
    file_path: string;
    file_type: string;
    file_name: string;
    created_at: string;
    updated_at_processing: string;
}

interface ChunkMetadata {
    chunk_id: string;
    token_count: number;
    first_line: string;
}

interface DocumentMetadataResponse {
    document: DocumentMetadata;
    chunks: ChunkMetadata[];
    chunk_count: number;
}

interface DataFilesResponse {
    files: DataFile[];
    folder_path: string;
    total_files: number;
    total_size_mb: number;
    error?: string;
}

export default function DocumentList() {
    const [files, setFiles] = useState<DataFile[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [selectedFile, setSelectedFile] = useState<FileContent | null>(null);
    const [showFileContent, setShowFileContent] = useState(false);
    const [documentMetadata, setDocumentMetadata] = useState<DocumentMetadataResponse | null>(null);
    const [showMetadata, setShowMetadata] = useState(false);
    const [loadingMetadata, setLoadingMetadata] = useState(false);
    const [folderPath, setFolderPath] = useState('');
    const [totalSize, setTotalSize] = useState(0);
    const [deletingFile, setDeletingFile] = useState<string | null>(null);
    const [deleteMessage, setDeleteMessage] = useState('');
    const [collectionInfo, setCollectionInfo] = useState<any>(null);

    const fetchCollectionInfo = async () => {
        try {
            const response = await fetch('http://localhost:9000/collection/info');
            if (response.ok) {
                const data = await response.json();
                setCollectionInfo(data);
            }
        } catch (error) {
            console.error('Error fetching collection info:', error);
        }
    };

    const fetchDataFiles = async () => {
        setLoading(true);
        setError('');

        try {
            const response = await fetch('http://localhost:9000/data-files', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (response.ok) {
                const data: DataFilesResponse = await response.json();
                setFiles(data.files);
                setFolderPath(data.folder_path);
                setTotalSize(data.total_size_mb);
                if (data.error) {
                    setError(data.error);
                }
            } else {
                const errorData = await response.json();
                setError(`Error: ${errorData.detail}`);
            }
        } catch (error) {
            if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
                setError('Unable to connect to backend server. Please ensure the backend is running on port 9000.');
            } else {
                setError(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
            }
        } finally {
            setLoading(false);
        }
    };

    const fetchFileContent = async (filename: string) => {
        try {
            const response = await fetch(`http://localhost:9000/data-files/${encodeURIComponent(filename)}`);
            if (response.ok) {
                const data: FileContent = await response.json();
                setSelectedFile(data);
                setShowFileContent(true);
            } else {
                const errorData = await response.json();
                setError(`Error loading file: ${errorData.detail}`);
            }
        } catch (error) {
            setError(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    };

    const fetchDocumentMetadata = async (filename: string) => {
        setLoadingMetadata(true);
        setError('');

        try {
            const response = await fetch(`http://localhost:9000/documents/${encodeURIComponent(filename)}/metadata`);
            if (response.ok) {
                const data: DocumentMetadataResponse = await response.json();
                setDocumentMetadata(data);
                setShowMetadata(true);
            } else {
                const errorData = await response.json();
                setError(`Error loading metadata: ${errorData.detail}`);
            }
        } catch (error) {
            setError(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
        } finally {
            setLoadingMetadata(false);
        }
    };

    const deleteFile = async (filename: string) => {
        if (!confirm(`Are you sure you want to delete "${filename}"? This will remove it from both the data folder and the search index.`)) {
            return;
        }

        setDeletingFile(filename);
        setDeleteMessage('');
        setError('');

        try {
            const response = await fetch(`http://localhost:9000/documents/file/${encodeURIComponent(filename)}`, {
                method: 'DELETE',
            });

            if (response.ok) {
                const result = await response.json();
                setDeleteMessage(`Successfully deleted: ${result.files_deleted_count} file(s) and ${result.documents_deleted_count} document(s) from index`);
                // Refresh the file list and collection info
                await fetchDataFiles();
                await fetchCollectionInfo();
            } else {
                const errorData = await response.json();
                setError(`Error deleting file: ${errorData.detail}`);
            }
        } catch (error) {
            setError(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
        } finally {
            setDeletingFile(null);
        }
    };

    const formatFileSize = (bytes: number) => {
        if (bytes < 1024) return `${bytes} B`;
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleString();
    };

    const getFileIcon = (extension: string) => {
        switch (extension) {
            case '.txt':
                return '📄';
            case '.pdf':
                return '📕';
            case '.doc':
            case '.docx':
                return '📘';
            case '.md':
                return '📝';
            case '.json':
                return '📋';
            case '.csv':
                return '📊';
            default:
                return '📄';
        }
    };

    useEffect(() => {
        // Add a small delay to ensure backend is ready
        const timer = setTimeout(() => {
            fetchDataFiles();
            fetchCollectionInfo();
        }, 1000);

        return () => clearTimeout(timer);
    }, []);

    if (loading) {
        return (
            <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex justify-center items-center h-32">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                </div>
            </div>
        );
    }

    return (
        <div className="bg-white rounded-lg shadow-md p-6">
            <div className="mb-6">
                <h2 className="text-2xl font-semibold text-gray-900">
                    Data Files ({files.length})
                </h2>
                <p className="text-sm text-gray-600 mt-1">
                    {folderPath} • Total size: {totalSize.toFixed(2)} MB
                </p>
            </div>

            {/* Collection Information */}
            {collectionInfo && (
                <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <h3 className="text-lg font-semibold text-blue-900 mb-3">
                        Collection: {collectionInfo.collection_name}
                    </h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                            <label className="text-blue-700 font-medium">Documents</label>
                            <p className="text-blue-900 font-semibold">{collectionInfo.total_documents}</p>
                        </div>
                        <div>
                            <label className="text-blue-700 font-medium">Total Chunks</label>
                            <p className="text-blue-900 font-semibold">{collectionInfo.total_chunks}</p>
                        </div>
                        <div>
                            <label className="text-blue-700 font-medium">Embedding Model</label>
                            <p className="text-blue-900 font-semibold">{collectionInfo.embedding_model}</p>
                        </div>
                        <div>
                            <label className="text-blue-700 font-medium">Chunk Size</label>
                            <p className="text-blue-900 font-semibold">{collectionInfo.chunk_size} tokens</p>
                        </div>
                    </div>
                </div>
            )}

            {error && (
                <div className="mb-6 p-3 bg-red-100 text-red-700 border border-red-300 rounded-md">
                    {error}
                </div>
            )}

            {deleteMessage && (
                <div className="mb-6 p-3 bg-green-100 text-green-700 border border-green-300 rounded-md">
                    {deleteMessage}
                </div>
            )}

            {files.length === 0 ? (
                <div className="text-center py-12">
                    <div className="text-gray-400 mb-4">
                        <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                    </div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No files found</h3>
                    <p className="text-gray-500">Add some files to the data folder to get started with RAG testing.</p>
                </div>
            ) : (
                <div className="space-y-3">
                    {files.map((file, index) => (
                        <div key={file.name} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center space-x-3">
                                    <span className="text-2xl">{getFileIcon(file.extension)}</span>
                                    <div>
                                        <h3 className="text-lg font-medium text-gray-900">{file.name}</h3>
                                        <div className="flex items-center space-x-4 text-sm text-gray-500">
                                            <span>{formatFileSize(file.size_bytes)}</span>
                                            <span>{file.extension.toUpperCase()}</span>
                                            <span>Modified: {formatDate(file.modified)}</span>
                                        </div>
                                    </div>
                                </div>
                                <div className="flex space-x-2">
                                    <button
                                        onClick={() => fetchFileContent(file.name)}
                                        className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                                    >
                                        View Content
                                    </button>
                                    <button
                                        onClick={() => fetchDocumentMetadata(file.name)}
                                        disabled={loadingMetadata}
                                        className="px-4 py-2 bg-green-500 text-white rounded-md hover:bg-green-600 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                        {loadingMetadata ? (
                                            <div className="flex items-center">
                                                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                                                Loading...
                                            </div>
                                        ) : (
                                            'View Metadata'
                                        )}
                                    </button>
                                    <button
                                        onClick={() => deleteFile(file.name)}
                                        disabled={deletingFile === file.name}
                                        className="px-4 py-2 bg-red-500 text-white rounded-md hover:bg-red-600 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                        {deletingFile === file.name ? (
                                            <div className="flex items-center">
                                                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                                                Deleting...
                                            </div>
                                        ) : (
                                            'Delete'
                                        )}
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* File Content Modal */}
            {showFileContent && selectedFile && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg max-w-4xl w-full mx-4 max-h-[80vh] flex flex-col">
                        <div className="flex justify-between items-center p-6 border-b border-gray-200">
                            <div>
                                <h3 className="text-lg font-semibold text-gray-900">{selectedFile.filename}</h3>
                                <div className="flex items-center space-x-4 text-sm text-gray-500 mt-1">
                                    <span>{formatFileSize(selectedFile.size_bytes)}</span>
                                    <span>{selectedFile.extension.toUpperCase()}</span>
                                    <span>{selectedFile.line_count} lines</span>
                                    <span>{selectedFile.word_count} words</span>
                                    <span>Modified: {formatDate(selectedFile.modified)}</span>
                                </div>
                            </div>
                            <button
                                onClick={() => setShowFileContent(false)}
                                className="text-gray-400 hover:text-gray-600"
                            >
                                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                        </div>
                        <div className="flex-1 overflow-auto p-6">
                            <pre className="whitespace-pre-wrap text-sm text-gray-900 bg-gray-50 p-4 rounded-lg max-h-96 overflow-auto">
                                {selectedFile.content}
                            </pre>
                        </div>
                    </div>
                </div>
            )}

            {/* Document Metadata Modal */}
            {showMetadata && documentMetadata && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg max-w-6xl w-full mx-4 max-h-[90vh] flex flex-col">
                        <div className="flex justify-between items-center p-6 border-b border-gray-200">
                            <div>
                                <h3 className="text-xl font-semibold text-gray-900">Enhanced Document Metadata</h3>
                                <p className="text-sm text-gray-500 mt-1">{documentMetadata.document.file_name}</p>
                            </div>
                            <button
                                onClick={() => setShowMetadata(false)}
                                className="text-gray-400 hover:text-gray-600"
                            >
                                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                        </div>
                        <div className="flex-1 overflow-auto p-6">
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                {/* Document Information */}
                                <div className="space-y-4">
                                    <h4 className="text-lg font-medium text-gray-900 border-b border-gray-200 pb-2">Document Information</h4>

                                    <div className="space-y-3">
                                        <div>
                                            <label className="text-sm font-medium text-gray-500">Title</label>
                                            <p className="text-sm text-gray-900">{documentMetadata.document.title}</p>
                                        </div>

                                        <div className="grid grid-cols-2 gap-4">
                                            <div>
                                                <label className="text-sm font-medium text-gray-500">Document Type</label>
                                                <p className="text-sm text-gray-900 capitalize">{documentMetadata.document.doc_type}</p>
                                            </div>
                                            <div>
                                                <label className="text-sm font-medium text-gray-500">Domain</label>
                                                <p className="text-sm text-gray-900">{documentMetadata.document.domain}</p>
                                            </div>
                                        </div>

                                        <div className="grid grid-cols-2 gap-4">
                                            <div>
                                                <label className="text-sm font-medium text-gray-500">Language</label>
                                                <p className="text-sm text-gray-900">{documentMetadata.document.language}</p>
                                            </div>
                                            <div>
                                                <label className="text-sm font-medium text-gray-500">URL</label>
                                                <p className="text-sm text-gray-900">{documentMetadata.document.url || 'None'}</p>
                                            </div>
                                        </div>

                                        <div className="grid grid-cols-2 gap-4">
                                            <div>
                                                <label className="text-sm font-medium text-gray-500">Geo Scope</label>
                                                <p className="text-sm text-gray-900">{documentMetadata.document.geo_scope}</p>
                                            </div>
                                            <div>
                                                <label className="text-sm font-medium text-gray-500">Currency</label>
                                                <p className="text-sm text-gray-900">{documentMetadata.document.currency}</p>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                {/* Temporal Information */}
                                <div className="space-y-4">
                                    <h4 className="text-lg font-medium text-gray-900 border-b border-gray-200 pb-2">Temporal Information</h4>

                                    <div className="space-y-3">
                                        <div>
                                            <label className="text-sm font-medium text-gray-500">Published At</label>
                                            <p className="text-sm text-gray-900">{documentMetadata.document.published_at || 'Not specified'}</p>
                                        </div>

                                        <div>
                                            <label className="text-sm font-medium text-gray-500">Updated At</label>
                                            <p className="text-sm text-gray-900">{documentMetadata.document.updated_at || 'Not specified'}</p>
                                        </div>

                                        <div>
                                            <label className="text-sm font-medium text-gray-500">Effective Date</label>
                                            <p className="text-sm text-gray-900">{documentMetadata.document.effective_date || 'Not specified'}</p>
                                        </div>

                                        <div>
                                            <label className="text-sm font-medium text-gray-500">Expires At</label>
                                            <p className="text-sm text-gray-900">{documentMetadata.document.expires_at || 'Not specified'}</p>
                                        </div>
                                    </div>
                                </div>

                                {/* Content Analysis */}
                                <div className="space-y-4">
                                    <h4 className="text-lg font-medium text-gray-900 border-b border-gray-200 pb-2">Content Analysis</h4>

                                    <div>
                                        <label className="text-sm font-medium text-gray-500">Product Entities</label>
                                        <div className="flex flex-wrap gap-1 mt-1">
                                            {documentMetadata.document.product_entities.map((entity, index) => (
                                                <span key={index} className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                                    {entity}
                                                </span>
                                            ))}
                                        </div>
                                    </div>

                                    <div>
                                        <label className="text-sm font-medium text-gray-500">Categories</label>
                                        <div className="flex flex-wrap gap-1 mt-1">
                                            {documentMetadata.document.categories.map((category, index) => (
                                                <span key={index} className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                                    {category}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                </div>

                                {/* Chunk Information */}
                                <div className="space-y-4">
                                    <h4 className="text-lg font-medium text-gray-900 border-b border-gray-200 pb-2">Chunk Information</h4>

                                    <div>
                                        <label className="text-sm font-medium text-gray-500">Total Chunks</label>
                                        <p className="text-sm text-gray-900">{documentMetadata.chunk_count}</p>
                                    </div>

                                    <div>
                                        <label className="text-sm font-medium text-gray-500">Chunks with Numbers</label>
                                        <p className="text-sm text-gray-900">{documentMetadata.chunks.filter(c => c.has_numbers).length}</p>
                                    </div>

                                    <div>
                                        <label className="text-sm font-medium text-gray-500">Chunks with Currency</label>
                                        <p className="text-sm text-gray-900">{documentMetadata.chunks.filter(c => c.has_currency).length}</p>
                                    </div>

                                    <div>
                                        <label className="text-sm font-medium text-gray-500">Average Token Count</label>
                                        <p className="text-sm text-gray-900">
                                            {documentMetadata.chunks.length > 0
                                                ? Math.round(documentMetadata.chunks.reduce((sum, c) => sum + c.token_count, 0) / documentMetadata.chunks.length)
                                                : 0
                                            }
                                        </p>
                                    </div>
                                </div>
                            </div>

                            {/* Chunks Detail */}
                            {documentMetadata.chunks.length > 0 && (
                                <div className="mt-8">
                                    <h4 className="text-lg font-medium text-gray-900 border-b border-gray-200 pb-2 mb-4">Chunk Details</h4>
                                    <div className="space-y-3">
                                        {documentMetadata.chunks.map((chunk, index) => (
                                            <div key={chunk.chunk_id} className="border border-gray-200 rounded-lg p-4">
                                                <div className="flex justify-between items-start mb-2">
                                                    <h5 className="text-sm font-medium text-gray-900">Chunk {index + 1}</h5>
                                                    <div className="flex space-x-2">
                                                        {chunk.has_numbers && (
                                                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                                                                Numbers
                                                            </span>
                                                        )}
                                                        {chunk.has_currency && (
                                                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                                                Currency
                                                            </span>
                                                        )}
                                                    </div>
                                                </div>
                                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                                                    <div>
                                                        <label className="text-gray-500">Chunk ID</label>
                                                        <p className="text-gray-900 font-mono text-xs">{chunk.chunk_id}</p>
                                                    </div>
                                                    <div>
                                                        <label className="text-gray-500">Tokens</label>
                                                        <p className="text-gray-900">{chunk.token_count}</p>
                                                    </div>
                                                    <div>
                                                        <label className="text-gray-500">First Line</label>
                                                        <p className="text-gray-900">{chunk.first_line || 'None'}</p>
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
