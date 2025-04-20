'use client';

import React, { useState, useEffect, useRef } from 'react';
import DocumentPreview from './DocumentPreview';

interface DocumentViewerProps {
  documentId: string;
  filename: string;
  contentType: string;
  url?: string;
  previewContent?: string;
  onClose?: () => void;
  downloadUrl?: string;
  metadata?: Record<string, any>;
}

const DocumentViewer: React.FC<DocumentViewerProps> = ({
  documentId,
  filename,
  contentType,
  url,
  previewContent,
  onClose,
  downloadUrl,
  metadata = {}
}) => {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [scale, setScale] = useState(1);
  const [rotation, setRotation] = useState(0);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const viewerRef = useRef<HTMLDivElement>(null);
  
  // Responsive state
  const [isMobile, setIsMobile] = useState(false);
  
  // Check for mobile screen size
  useEffect(() => {
    const checkIfMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };
    
    // Initial check
    checkIfMobile();
    
    // Listen for resize events
    window.addEventListener('resize', checkIfMobile);
    
    return () => {
      window.removeEventListener('resize', checkIfMobile);
    };
  }, []);
  
  // Handle fullscreen mode
  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      viewerRef.current?.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  };
  
  // Listen for fullscreen changes
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    
    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
    };
  }, []);
  
  // Handle zoom in
  const zoomIn = () => {
    setScale((prevScale) => Math.min(prevScale + 0.25, 3));
  };
  
  // Handle zoom out
  const zoomOut = () => {
    setScale((prevScale) => Math.max(prevScale - 0.25, 0.5));
  };
  
  // Handle reset zoom
  const resetZoom = () => {
    setScale(1);
  };
  
  // Handle rotation
  const rotateClockwise = () => {
    setRotation((prevRotation) => (prevRotation + 90) % 360);
  };
  
  // Handle download
  const handleDownload = () => {
    if (downloadUrl) {
      window.open(downloadUrl, '_blank');
    } else if (url) {
      window.open(url, '_blank');
    }
  };
  
  // Toggle mobile menu
  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };
  
  return (
    <div 
      ref={viewerRef}
      className={`flex flex-col h-full w-full bg-gray-100 rounded-lg overflow-hidden ${isFullscreen ? 'fixed inset-0 z-50' : ''}`}
    >
      {/* Toolbar */}
      <div className="bg-white border-b border-gray-200 py-2 px-4 flex items-center justify-between shadow-sm">
        <div className="flex items-center">
          <h2 className="text-lg font-medium text-gray-800 mr-2 truncate max-w-xs md:max-w-md">{filename}</h2>
          {metadata.version && (
            <span className="bg-blue-100 text-blue-800 text-xs font-medium px-2 py-0.5 rounded">v{metadata.version}</span>
          )}
        </div>
        
        {/* Desktop toolbar */}
        <div className="hidden md:flex items-center space-x-2">
          <button
            onClick={zoomOut}
            className="p-1.5 rounded-md text-gray-700 hover:bg-gray-100"
            aria-label="Zoom out"
            title="Zoom out"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
            </svg>
          </button>
          
          <div className="text-sm text-gray-700">{Math.round(scale * 100)}%</div>
          
          <button
            onClick={zoomIn}
            className="p-1.5 rounded-md text-gray-700 hover:bg-gray-100"
            aria-label="Zoom in"
            title="Zoom in"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
          </button>
          
          <button
            onClick={resetZoom}
            className="p-1.5 rounded-md text-gray-700 hover:bg-gray-100"
            aria-label="Reset zoom"
            title="Reset zoom"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5v-4m0 4h-4m4 0l-5-5" />
            </svg>
          </button>
          
          <div className="h-6 border-l border-gray-300 mx-1"></div>
          
          <button
            onClick={rotateClockwise}
            className="p-1.5 rounded-md text-gray-700 hover:bg-gray-100"
            aria-label="Rotate"
            title="Rotate"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
          
          <div className="h-6 border-l border-gray-300 mx-1"></div>
          
          <button
            onClick={toggleFullscreen}
            className="p-1.5 rounded-md text-gray-700 hover:bg-gray-100"
            aria-label={isFullscreen ? "Exit fullscreen" : "Fullscreen"}
            title={isFullscreen ? "Exit fullscreen" : "Fullscreen"}
          >
            {isFullscreen ? (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 9V4.5M9 9H4.5M9 9L3.75 3.75M9 15v4.5M9 15H4.5M9 15l-5.25 5.25M15 9h4.5M15 9V4.5M15 9l5.25-5.25M15 15h4.5M15 15v4.5m0-4.5l5.25 5.25" />
              </svg>
            ) : (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5v-4m0 4h-4m4 0l-5-5" />
              </svg>
            )}
          </button>
          
          {(downloadUrl || url) && (
            <>
              <div className="h-6 border-l border-gray-300 mx-1"></div>
              
              <button
                onClick={handleDownload}
                className="p-1.5 rounded-md text-gray-700 hover:bg-gray-100"
                aria-label="Download"
                title="Download"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
              </button>
            </>
          )}
          
          {onClose && (
            <>
              <div className="h-6 border-l border-gray-300 mx-1"></div>
              
              <button
                onClick={onClose}
                className="p-1.5 rounded-md text-gray-700 hover:bg-gray-100"
                aria-label="Close"
                title="Close"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </>
          )}
        </div>
        
        {/* Mobile menu button */}
        <div className="md:hidden">
          <button
            onClick={toggleMobileMenu}
            className="p-1.5 rounded-md text-gray-700 hover:bg-gray-100"
            aria-label="Menu"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16m-7 6h7" />
            </svg>
          </button>
        </div>
      </div>
      
      {/* Mobile menu */}
      {isMobile && isMobileMenuOpen && (
        <div className="bg-white border-b border-gray-200 p-2 flex flex-wrap items-center justify-center gap-2">
          <button
            onClick={zoomOut}
            className="p-2 rounded-md text-gray-700 hover:bg-gray-100"
            aria-label="Zoom out"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
            </svg>
          </button>
          
          <div className="text-sm text-gray-700">{Math.round(scale * 100)}%</div>
          
          <button
            onClick={zoomIn}
            className="p-2 rounded-md text-gray-700 hover:bg-gray-100"
            aria-label="Zoom in"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
          </button>
          
          <button
            onClick={resetZoom}
            className="p-2 rounded-md text-gray-700 hover:bg-gray-100"
            aria-label="Reset zoom"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5v-4m0 4h-4m4 0l-5-5" />
            </svg>
          </button>
          
          <button
            onClick={rotateClockwise}
            className="p-2 rounded-md text-gray-700 hover:bg-gray-100"
            aria-label="Rotate"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
          
          <button
            onClick={toggleFullscreen}
            className="p-2 rounded-md text-gray-700 hover:bg-gray-100"
            aria-label={isFullscreen ? "Exit fullscreen" : "Fullscreen"}
          >
            {isFullscreen ? (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 9V4.5M9 9H4.5M9 9L3.75 3.75M9 15v4.5M9 15H4.5M9 15l-5.25 5.25M15 9h4.5M15 9V4.5M15 9l5.25-5.25M15 15h4.5M15 15v4.5m0-4.5l5.25 5.25" />
              </svg>
            ) : (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5v-4m0 4h-4m4 0l-5-5" />
              </svg>
            )}
          </button>
          
          {(downloadUrl || url) && (
            <button
              onClick={handleDownload}
              className="p-2 rounded-md text-gray-700 hover:bg-gray-100"
              aria-label="Download"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
            </button>
          )}
          
          {onClose && (
            <button
              onClick={onClose}
              className="p-2 rounded-md text-gray-700 hover:bg-gray-100"
              aria-label="Close"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
      )}
      
      {/* Document content */}
      <div className="flex-grow overflow-auto p-4">
        <div 
          className="max-w-5xl mx-auto"
          style={{
            transform: `scale(${scale}) rotate(${rotation}deg)`,
            transformOrigin: 'center center',
            transition: 'transform 0.3s ease'
          }}
        >
          <DocumentPreview
            documentId={documentId}
            filename={filename}
            contentType={contentType}
            url={url}
            previewContent={previewContent}
            thumbnailUrl={metadata.thumbnailUrl}
          />
        </div>
      </div>
      
      {/* Footer with metadata */}
      {Object.keys(metadata).length > 0 && (
        <div className="bg-white border-t border-gray-200 py-2 px-4 text-xs text-gray-500">
          <div className="flex flex-wrap gap-x-4 gap-y-1">
            {metadata.uploadedBy && (
              <div>
                <span className="font-medium">Uploaded by:</span> {metadata.uploadedBy}
              </div>
            )}
            {metadata.uploadDate && (
              <div>
                <span className="font-medium">Date:</span> {new Date(metadata.uploadDate).toLocaleDateString()}
              </div>
            )}
            {metadata.size && (
              <div>
                <span className="font-medium">Size:</span> {typeof metadata.size === 'number' ? `${(metadata.size / 1024).toFixed(1)} KB` : metadata.size}
              </div>
            )}
            {metadata.pages && (
              <div>
                <span className="font-medium">Pages:</span> {metadata.pages}
              </div>
            )}
            {metadata.category && (
              <div>
                <span className="font-medium">Category:</span> {metadata.category}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentViewer; 