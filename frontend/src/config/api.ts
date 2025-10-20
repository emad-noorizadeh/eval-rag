/**
 * API Configuration
 * Author: Emad Noorizadeh
 */

// Get backend URL from environment variable or use default
export const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:9000';

// API endpoints
export const API_ENDPOINTS = {
  // Chat endpoints
  CHAT: `${API_BASE_URL}/chat`,
  CHAT_CONFIG: `${API_BASE_URL}/chat-config`,
  
  // Document endpoints
  DOCUMENTS: `${API_BASE_URL}/documents`,
  DOCUMENTS_METADATA: `${API_BASE_URL}/documents/metadata`,
  DOCUMENT_UPLOAD_FILE: `${API_BASE_URL}/documents/file`,
  DOCUMENT_CONTENT: (filename: string) => `${API_BASE_URL}/documents/${encodeURIComponent(filename)}/content`,
  DOCUMENT_METADATA: (filename: string) => `${API_BASE_URL}/documents/${encodeURIComponent(filename)}/metadata`,
  DOCUMENT_FILE: (filename: string) => `${API_BASE_URL}/documents/file/${encodeURIComponent(filename)}`,
  
  // Data file endpoints
  DATA_FILES: `${API_BASE_URL}/data-files`,
  DATA_FILE_CONTENT: (filename: string) => `${API_BASE_URL}/data-files/${encodeURIComponent(filename)}`,

  // Reports endpoints
  REPORTS: `${API_BASE_URL}/reports`,
  REPORT_FILE: (filename: string) => `${API_BASE_URL}/reports/${encodeURIComponent(filename)}`,

  // Collection endpoints
  COLLECTION_INFO: `${API_BASE_URL}/collection/info`,
  
  // Query endpoints
  QUERY: `${API_BASE_URL}/query`,
  
  // Session endpoints
  SESSIONS: `${API_BASE_URL}/sessions`,
  SESSION_EXTEND: (sessionId: string) => `${API_BASE_URL}/sessions/${sessionId}/extend`,
  
  // Configuration endpoints
  CHUNKING_CONFIG: `${API_BASE_URL}/chunking-config`,
} as const;

// Helper function to get full URL
export const getApiUrl = (endpoint: keyof typeof API_ENDPOINTS, ...params: any[]): string => {
  const url = API_ENDPOINTS[endpoint];
  return typeof url === 'function' ? url(...params) : url;
};
