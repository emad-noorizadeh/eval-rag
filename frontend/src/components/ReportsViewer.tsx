/**
 * Reports Viewer Component - Lists generated PDF reports
 * Author: Emad Noorizadeh (extended by Codex)
 */

'use client';

import { useEffect, useState } from 'react';
import { getApiUrl } from '@/config/api';

interface ReportFile {
  name: string;
  title?: string;
  size_bytes: number;
  size_mb: number;
  modified: string;
}

interface ReportsResponse {
  reports: ReportFile[];
  error?: string;
}

export default function ReportsViewer() {
  const [reports, setReports] = useState<ReportFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchReports = async () => {
      setLoading(true);
      setError('');

      try {
        const response = await fetch(getApiUrl('REPORTS'), {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
        });

        if (response.ok) {
          const data: ReportsResponse = await response.json();
          setReports(data.reports || []);
          if (data.error) {
            setError(data.error);
          }
        } else {
          const errorData = await response.json();
          setError(errorData?.detail ? `Error: ${errorData.detail}` : 'Failed to load reports');
        }
      } catch (err) {
        if (err instanceof TypeError && err.message.includes('Failed to fetch')) {
          setError('Unable to connect to backend server. Please ensure the backend is running on port 9000.');
        } else {
          setError(`Error: ${err instanceof Error ? err.message : 'Unknown error'}`);
        }
      } finally {
        setLoading(false);
      }
    };

    fetchReports();
  }, []);

  const formatDate = (iso: string) => (iso ? new Date(iso).toLocaleString() : 'Unknown');
  const formatSize = (size: number) => `${size.toFixed(2)} MB`;

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-semibold text-gray-900">Research &amp; White Papers</h2>
      </div>

      {loading && (
        <div className="py-10 text-center text-gray-500">
          Loading reports…
        </div>
      )}

      {!loading && error && (
        <div className="mb-4 rounded-md bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {!loading && !error && reports.length === 0 && (
        <div className="py-10 text-center text-gray-500">
          No PDF reports found. Generate reports to see them listed here.
        </div>
      )}

      {!loading && reports.length > 0 && (
        <div className="border border-gray-200 rounded-lg divide-y divide-gray-200">
          {reports.map((report) => (
            <div key={report.name} className="px-4 py-3 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div>
                <p className="font-medium text-gray-900">
                  {report.title && report.title.trim() ? report.title : report.name}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  Updated {formatDate(report.modified)} • {formatSize(report.size_mb)} • {report.name}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <a
                  href={getApiUrl('REPORT_FILE', report.name)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center px-3 py-2 text-sm font-medium text-blue-600 border border-blue-200 rounded-md hover:bg-blue-50 transition-colors"
                >
                  View
                </a>
                <a
                  href={getApiUrl('REPORT_FILE', report.name)}
                  download
                  className="inline-flex items-center px-3 py-2 text-sm font-medium text-gray-600 border border-gray-200 rounded-md hover:bg-gray-50 transition-colors"
                >
                  Download
                </a>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
