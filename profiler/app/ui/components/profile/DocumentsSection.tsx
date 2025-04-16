'use client';

import React, { useState } from 'react';
import DocumentUploader from './DocumentUploader';
import { useDocumentService } from '../../lib/contexts/DocumentContext';
import { useProfile } from '../../lib/contexts/ProfileContext';

interface Document {
  id: string;
  name: string;
  uploadDate: string;
  section: string;
}

const DocumentsSection: React.FC = () => {
  const { documentService, isUploading, lastUploaded } = useDocumentService();
  const { state } = useProfile();
  const [documents, setDocuments] = useState<Document[]>([]);

  const handleDocumentUpload = (documentId: string) => {
    if (documentId && lastUploaded) {
      // In a real app, you would get this data from the backend
      const newDocument: Document = {
        id: documentId,
        name: lastUploaded.filename,
        uploadDate: new Date().toISOString(),
        section: state?.current_section || 'academic',
      };
      
      setDocuments([...documents, newDocument]);
    }
  };

  const handleDeleteDocument = (documentId: string) => {
    // In a real app, you would call an API to delete the document
    setDocuments(documents.filter(doc => doc.id !== documentId));
  };

  return (
    <div className="space-y-6">
      <div className="border-b pb-4">
        <h2 className="text-2xl font-semibold text-gray-800">Documents</h2>
        <p className="text-gray-600 mt-1">
          Upload documents to enhance your profile. We'll analyze them to extract relevant information.
        </p>
      </div>
      
      <DocumentUploader onUpload={handleDocumentUpload} />
      
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
      
      {documents.length === 0 && !isUploading && (
        <div className="text-center py-8 bg-gray-50 rounded-lg border border-gray-200">
          <svg xmlns="http://www.w3.org/2000/svg" className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 13h6m-3-3v6m-9 1V7a2 2 0 012-2h6l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2z" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No documents</h3>
          <p className="mt-1 text-sm text-gray-500">
            Upload a document to get started
          </p>
        </div>
      )}
    </div>
  );
};

export default DocumentsSection; 