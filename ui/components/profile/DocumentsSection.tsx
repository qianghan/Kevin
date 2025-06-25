'use client';

import React, { useState } from 'react';
import { useUserContext } from '@/features/user/context/UserContext';
import DocumentUploader from './DocumentUploader';

interface Document {
  id: string;
  name: string;
  uploadDate: string;
  section: string;
}

export function DocumentsSection() {
  const { profile } = useUserContext();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const handleDocumentUpload = async (file: File) => {
    try {
      setIsUploading(true);
      setUploadError(null);

      // In a real app, you would upload the file to your backend
      // For now, we'll just simulate a successful upload
      await new Promise(resolve => setTimeout(resolve, 1000));

      const newDocument: Document = {
        id: Math.random().toString(36).substring(7),
        name: file.name,
        uploadDate: new Date().toISOString(),
        section: 'general'
      };

      setDocuments(prev => [...prev, newDocument]);
    } catch (error) {
      setUploadError(error instanceof Error ? error.message : 'Failed to upload document');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDeleteDocument = (documentId: string) => {
    setDocuments(documents.filter(doc => doc.id !== documentId));
  };

  if (!profile) {
    return <div className="p-4">Loading...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="border-b pb-4">
        <h2 className="text-2xl font-semibold text-gray-800">Documents</h2>
        <p className="text-gray-600 mt-1">
          Upload documents to enhance your profile. We'll analyze them to extract relevant information.
        </p>
      </div>
      
      <DocumentUploader onUpload={handleDocumentUpload} isUploading={isUploading} />
      
      {uploadError && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {uploadError}
        </div>
      )}
      
      {documents.length > 0 && (
        <div className="mt-8">
          <h3 className="text-lg font-medium mb-3">Your Documents</h3>
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Name
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Section
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Uploaded
                  </th>
                  <th scope="col" className="relative px-6 py-3">
                    <span className="sr-only">Actions</span>
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {documents.map((doc) => (
                  <tr key={doc.id}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="flex-shrink-0 h-10 w-10 flex items-center justify-center bg-blue-100 rounded-md">
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                          </svg>
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-medium text-gray-900">
                            {doc.name}
                          </div>
                          <div className="text-sm text-gray-500">
                            ID: {doc.id.substring(0, 8)}...
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                        {doc.section}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(doc.uploadDate).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={() => handleDeleteDocument(doc.id)}
                        className="text-red-600 hover:text-red-900"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
} 