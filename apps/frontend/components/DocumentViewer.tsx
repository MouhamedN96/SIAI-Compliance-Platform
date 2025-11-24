'use client';

import { useState, useCallback } from 'react';
import { Upload, FileText } from 'lucide-react';

interface DocumentViewerProps {
  document: string | null;
  highlights: any[];
  onUpload: (file: File) => void;
}

export default function DocumentViewer({ document, highlights, onUpload }: DocumentViewerProps) {
  const [isDragging, setIsDragging] = useState(false);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);

      const files = Array.from(e.dataTransfer.files);
      const pdfFile = files.find((file) => file.type === 'application/pdf');

      if (pdfFile) {
        onUpload(pdfFile);
      }
    },
    [onUpload]
  );

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        onUpload(file);
      }
    },
    [onUpload]
  );

  if (!document) {
    return (
      <div className="h-full bg-white flex flex-col">
        <div className="border-b border-gray-200 px-6 py-4">
          <h2 className="text-lg font-semibold text-gray-900">Document Viewer</h2>
        </div>
        <div
          className={`flex-1 flex items-center justify-center p-8 ${
            isDragging ? 'bg-blue-50' : 'bg-gray-50'
          }`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <div className="text-center max-w-md">
            <div
              className={`mx-auto w-16 h-16 rounded-full flex items-center justify-center mb-4 ${
                isDragging ? 'bg-blue-100' : 'bg-gray-100'
              }`}
            >
              <Upload className={`w-8 h-8 ${isDragging ? 'text-blue-600' : 'text-gray-400'}`} />
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Upload a document</h3>
            <p className="text-sm text-gray-500 mb-6">
              Drag and drop a PDF file here, or click to browse
            </p>
            <label className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 cursor-pointer transition-colors">
              <input
                type="file"
                accept=".pdf"
                onChange={handleFileInput}
                className="hidden"
              />
              Choose File
            </label>
            <p className="text-xs text-gray-400 mt-4">Supported formats: PDF</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full bg-white flex flex-col">
      <div className="border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileText className="w-5 h-5 text-gray-600" />
          <h2 className="text-lg font-semibold text-gray-900">Document</h2>
        </div>
        <label className="px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-100 rounded-lg cursor-pointer transition-colors">
          <input
            type="file"
            accept=".pdf"
            onChange={handleFileInput}
            className="hidden"
          />
          Upload New
        </label>
      </div>
      <div className="flex-1 overflow-auto bg-gray-100 p-4">
        <div className="max-w-4xl mx-auto bg-white shadow-lg rounded-lg overflow-hidden">
          <iframe
            src={document}
            className="w-full h-[calc(100vh-200px)]"
            title="Document Viewer"
          />
        </div>
      </div>
    </div>
  );
}
