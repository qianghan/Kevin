import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import DocumentViewer from '../../../app/ui/components/document/DocumentViewer';
import { DocumentContext } from '../../../app/ui/context/DocumentContext';

// Mock document context
const mockDocumentContext = {
  documents: [
    {
      id: 'doc1',
      title: 'Test Document 1',
      contentType: 'text/plain',
      content: 'This is test document 1 content',
      createdAt: new Date().toISOString(),
      metadata: {
        fileSize: 1024,
        author: 'Test User'
      }
    },
    {
      id: 'doc2',
      title: 'Test PDF Document',
      contentType: 'application/pdf',
      url: '/test-document.pdf',
      createdAt: new Date().toISOString(),
      metadata: {
        fileSize: 2048,
        pageCount: 5
      }
    }
  ],
  loadDocument: jest.fn(),
  getDocumentContent: jest.fn(),
  exportDocument: jest.fn()
};

// Setup wrapper
const renderWithContext = (ui: React.ReactNode) => {
  return render(
    <DocumentContext.Provider value={mockDocumentContext}>
      {ui}
    </DocumentContext.Provider>
  );
};

describe('DocumentViewer Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders document viewer with text document', async () => {
    renderWithContext(<DocumentViewer documentId="doc1" />);
    
    // Wait for document to load
    await waitFor(() => {
      expect(mockDocumentContext.loadDocument).toHaveBeenCalledWith('doc1');
    });
    
    // Check document title is displayed
    expect(screen.getByText('Test Document 1')).toBeInTheDocument();
    
    // Check document content is displayed for text documents
    expect(screen.getByText('This is test document 1 content')).toBeInTheDocument();
    
    // Check metadata is displayed
    expect(screen.getByText('1 KB')).toBeInTheDocument();
    expect(screen.getByText('Test User')).toBeInTheDocument();
  });
  
  test('renders document viewer with PDF document', async () => {
    renderWithContext(<DocumentViewer documentId="doc2" />);
    
    // Wait for document to load
    await waitFor(() => {
      expect(mockDocumentContext.loadDocument).toHaveBeenCalledWith('doc2');
    });
    
    // Check document title is displayed
    expect(screen.getByText('Test PDF Document')).toBeInTheDocument();
    
    // Check PDF viewer component is rendered
    expect(screen.getByTestId('pdf-viewer')).toBeInTheDocument();
    
    // Check metadata is displayed
    expect(screen.getByText('2 KB')).toBeInTheDocument();
    expect(screen.getByText('5 pages')).toBeInTheDocument();
  });
  
  test('handles zoom controls', async () => {
    renderWithContext(<DocumentViewer documentId="doc1" />);
    
    // Find zoom controls
    const zoomInButton = screen.getByLabelText('Zoom in');
    const zoomOutButton = screen.getByLabelText('Zoom out');
    
    // Test zoom in
    fireEvent.click(zoomInButton);
    await waitFor(() => {
      const contentElement = screen.getByTestId('document-content');
      expect(contentElement).toHaveStyle('transform: scale(1.1)');
    });
    
    // Test zoom out
    fireEvent.click(zoomOutButton);
    await waitFor(() => {
      const contentElement = screen.getByTestId('document-content');
      expect(contentElement).toHaveStyle('transform: scale(1)');
    });
  });
  
  test('handles page navigation for multi-page documents', async () => {
    renderWithContext(<DocumentViewer documentId="doc2" />);
    
    // Find page navigation controls
    const nextPageButton = screen.getByLabelText('Next page');
    const prevPageButton = screen.getByLabelText('Previous page');
    const pageIndicator = screen.getByTestId('page-indicator');
    
    // Initial page should be 1
    expect(pageIndicator).toHaveTextContent('Page 1 of 5');
    
    // Go to next page
    fireEvent.click(nextPageButton);
    await waitFor(() => {
      expect(pageIndicator).toHaveTextContent('Page 2 of 5');
    });
    
    // Go to previous page
    fireEvent.click(prevPageButton);
    await waitFor(() => {
      expect(pageIndicator).toHaveTextContent('Page 1 of 5');
    });
  });
  
  test('handles document export', async () => {
    renderWithContext(<DocumentViewer documentId="doc1" />);
    
    // Find export button
    const exportButton = screen.getByText('Export');
    
    // Click export button
    fireEvent.click(exportButton);
    
    // Export format dropdown should appear
    const pdfOption = screen.getByText('PDF');
    fireEvent.click(pdfOption);
    
    await waitFor(() => {
      expect(mockDocumentContext.exportDocument).toHaveBeenCalledWith('doc1', 'pdf');
    });
  });
  
  test('displays error state when document fails to load', async () => {
    // Override loadDocument to simulate error
    mockDocumentContext.loadDocument.mockRejectedValueOnce(new Error('Failed to load document'));
    
    renderWithContext(<DocumentViewer documentId="invalid-id" />);
    
    await waitFor(() => {
      expect(screen.getByText('Error loading document')).toBeInTheDocument();
      expect(screen.getByText('Failed to load document')).toBeInTheDocument();
    });
  });
  
  test('renders loading state', () => {
    // Override loadDocument to never resolve
    mockDocumentContext.loadDocument.mockImplementationOnce(() => new Promise(() => {}));
    
    renderWithContext(<DocumentViewer documentId="doc1" />);
    
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
    expect(screen.getByText('Loading document...')).toBeInTheDocument();
  });
}); 