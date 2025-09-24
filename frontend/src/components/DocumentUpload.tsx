/**
 * Document Upload Component
 * Author: Emad Noorizadeh
 */

'use client';

import { useState } from 'react';

interface DocumentUploadProps { }

export default function DocumentUpload({ }: DocumentUploadProps) {
    const [text, setText] = useState('');
    const [metadata, setMetadata] = useState('');
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState('');
    const [uploadType, setUploadType] = useState<'text' | 'file'>('text');
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [customFilename, setCustomFilename] = useState('');

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            setSelectedFile(file);
            // Set default filename based on the uploaded file name
            const baseName = file.name.replace(/\.[^/.]+$/, ""); // Remove extension
            setCustomFilename(baseName);
            setMessage('');
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (uploadType === 'text' && !text.trim()) return;
        if (uploadType === 'file' && (!selectedFile || !customFilename.trim())) return;

        setLoading(true);
        setMessage('');

        try {
            let response;

            if (uploadType === 'text') {
                // Upload text document
                response = await fetch('http://localhost:9000/documents', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        text: text.trim(),
                        metadata: metadata ? JSON.parse(metadata) : {},
                    }),
                });
            } else {
                // Upload file document
                const formData = new FormData();
                formData.append('file', selectedFile!);
                formData.append('filename', customFilename.trim());

                response = await fetch('http://localhost:9000/documents/file', {
                    method: 'POST',
                    body: formData,
                });
            }

            if (response.ok) {
                const result = await response.json();
                let successMessage = `Document added to index successfully! ID: ${result.id}`;

                if (uploadType === 'file' && result.saved_filename) {
                    successMessage += `\n\nParsed text saved as: ${result.saved_filename}`;
                    if (result.page_count) {
                        successMessage += `\nPages processed: ${result.page_count}`;
                    }
                    if (result.text_length) {
                        successMessage += `\nText length: ${result.text_length} characters`;
                    }
                }

                setMessage(successMessage);
                setText('');
                setMetadata('');
                setSelectedFile(null);
                // Reset file input
                const fileInput = document.getElementById('file') as HTMLInputElement;
                if (fileInput) fileInput.value = '';
            } else {
                const error = await response.json();
                setMessage(`Error: ${error.detail}`);
            }
        } catch (error) {
            setMessage(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="bg-white rounded-lg shadow-md p-6">
            <div className="mb-6">
                <h2 className="text-2xl font-semibold text-gray-900 mb-2">Add Document to Index</h2>
                <p className="text-gray-600">Add documents incrementally to the existing index without rebuilding</p>
            </div>

            {/* Upload Type Selection */}
            <div className="mb-6">
                <div className="flex space-x-4">
                    <button
                        type="button"
                        onClick={() => setUploadType('text')}
                        className={`px-4 py-2 rounded-md font-medium ${uploadType === 'text'
                            ? 'bg-blue-500 text-white'
                            : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                            }`}
                    >
                        Text Input
                    </button>
                    <button
                        type="button"
                        onClick={() => setUploadType('file')}
                        className={`px-4 py-2 rounded-md font-medium ${uploadType === 'file'
                            ? 'bg-blue-500 text-white'
                            : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                            }`}
                    >
                        File Upload
                    </button>
                </div>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
                {uploadType === 'text' ? (
                    <div>
                        <label htmlFor="text" className="block text-sm font-medium text-gray-700 mb-2">
                            Document Text *
                        </label>
                        <textarea
                            id="text"
                            value={text}
                            onChange={(e) => setText(e.target.value)}
                            rows={8}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            placeholder="Enter the document text here..."
                            required
                        />
                    </div>
                ) : (
                    <div>
                        <label htmlFor="file" className="block text-sm font-medium text-gray-700 mb-2">
                            Select File *
                        </label>
                        <input
                            id="file"
                            type="file"
                            onChange={handleFileSelect}
                            accept=".txt,.md,.pdf"
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            required
                        />
                        <div className="mt-1 text-xs text-gray-500">
                            Supported formats: .txt, .md, .pdf (max 50MB)
                        </div>
                        {selectedFile && (
                            <div className="mt-2 text-sm text-gray-600">
                                Selected: {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
                            </div>
                        )}

                        <div className="mt-4">
                            <label htmlFor="filename" className="block text-sm font-medium text-gray-700 mb-2">
                                Document Name *
                            </label>
                            <input
                                id="filename"
                                type="text"
                                value={customFilename}
                                onChange={(e) => setCustomFilename(e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                placeholder="Enter a name for this document"
                                required
                            />
                            <div className="mt-1 text-xs text-gray-500">
                                This will be the name used to identify the document in the system
                            </div>
                        </div>
                    </div>
                )}

                <div>
                    <label htmlFor="metadata" className="block text-sm font-medium text-gray-700 mb-2">
                        Metadata (JSON format, optional)
                    </label>
                    <textarea
                        id="metadata"
                        value={metadata}
                        onChange={(e) => setMetadata(e.target.value)}
                        rows={3}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder='{"title": "Document Title", "author": "Author Name", "category": "Category"}'
                    />
                </div>

                <button
                    type="submit"
                    disabled={loading || (uploadType === 'text' ? !text.trim() : (!selectedFile || !customFilename.trim()))}
                    className="w-full bg-blue-500 text-white py-2 px-4 rounded-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {loading ? 'Adding to Index...' : 'Add to Index'}
                </button>
            </form>

            {message && (
                <div className={`mt-4 p-3 rounded-md ${message.includes('Error')
                    ? 'bg-red-100 text-red-700 border border-red-300'
                    : 'bg-green-100 text-green-700 border border-green-300'
                    }`}>
                    {message}
                </div>
            )}
        </div>
    );
}
