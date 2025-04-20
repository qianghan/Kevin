"""
Document OCR (Optical Character Recognition) service.

This module provides functionality for extracting text from images and scanned PDF documents.
"""

import os
import io
import logging
import tempfile
from typing import BinaryIO, Dict, Any, Optional, List, Union
from pathlib import Path
import base64

from ...utils.logging import get_logger

logger = get_logger(__name__)

# Try to import optional dependencies
try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logger.warning("pytesseract or PIL not available, OCR will use fallback methods")

try:
    import pdf2image
    PDF_TO_IMAGE_AVAILABLE = True
except ImportError:
    PDF_TO_IMAGE_AVAILABLE = False
    logger.warning("pdf2image not available, PDF OCR will be limited")


class OCRException(Exception):
    """Exception raised for OCR-related errors."""
    pass


class DocumentOCR:
    """
    Service for performing OCR on images and scanned documents.
    
    This service extracts text from images and scanned documents using OCR,
    with support for multiple languages and image preprocessing.
    """
    
    def __init__(self, 
                 tesseract_path: Optional[str] = None, 
                 language: str = 'eng',
                 temp_dir: Optional[str] = None):
        """
        Initialize the OCR service.
        
        Args:
            tesseract_path: Path to the Tesseract executable
            language: OCR language(s) to use (comma-separated for multiple)
            temp_dir: Directory for temporary files
        """
        self.language = language
        self.temp_dir = temp_dir or tempfile.gettempdir()
        
        # Configure tesseract path if provided
        if tesseract_path and TESSERACT_AVAILABLE:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        logger.info(f"OCR service initialized with language: {language}")
    
    async def initialize(self) -> None:
        """Initialize the OCR service."""
        # Verify tesseract is available
        if TESSERACT_AVAILABLE:
            try:
                version = pytesseract.get_tesseract_version()
                logger.info(f"Tesseract version: {version}")
            except Exception as e:
                logger.error(f"Failed to get Tesseract version: {e}")
                logger.warning("OCR functionality may be limited")
        
        # Create temp directory if it doesn't exist
        os.makedirs(self.temp_dir, exist_ok=True)
    
    async def extract_text_from_image(self, 
                                    image_file: Union[BinaryIO, str, Path],
                                    preprocess: bool = True,
                                    lang: Optional[str] = None) -> str:
        """
        Extract text from an image using OCR.
        
        Args:
            image_file: Image file (file-like object or path)
            preprocess: Whether to preprocess the image for better OCR results
            lang: Language for OCR (overrides default)
            
        Returns:
            Extracted text content
            
        Raises:
            OCRException: If OCR processing fails
        """
        if not TESSERACT_AVAILABLE:
            raise OCRException("Tesseract OCR is not available")
        
        try:
            # Open the image
            if isinstance(image_file, (str, Path)):
                img = Image.open(image_file)
            else:
                # Get current position to restore later
                pos = image_file.tell()
                # Reset to beginning of file
                image_file.seek(0)
                img = Image.open(image_file)
                # Restore position
                image_file.seek(pos)
            
            # Preprocess image if requested
            if preprocess:
                img = self._preprocess_image(img)
            
            # Perform OCR
            ocr_lang = lang or self.language
            text = pytesseract.image_to_string(img, lang=ocr_lang)
            
            logger.info(f"OCR extracted {len(text)} characters from image")
            return text
            
        except Exception as e:
            logger.error(f"OCR processing failed: {str(e)}")
            raise OCRException(f"OCR processing failed: {str(e)}")
    
    async def extract_text_from_pdf(self, 
                                  pdf_file: Union[BinaryIO, str, Path],
                                  pages: Optional[List[int]] = None,
                                  preprocess: bool = True,
                                  lang: Optional[str] = None) -> Dict[int, str]:
        """
        Extract text from a scanned PDF using OCR.
        
        Args:
            pdf_file: PDF file (file-like object or path)
            pages: List of page numbers to process (1-indexed, None for all)
            preprocess: Whether to preprocess images for better OCR results
            lang: Language for OCR (overrides default)
            
        Returns:
            Dictionary mapping page numbers to extracted text
            
        Raises:
            OCRException: If PDF processing fails
        """
        if not TESSERACT_AVAILABLE or not PDF_TO_IMAGE_AVAILABLE:
            raise OCRException("Required libraries for PDF OCR are not available")
        
        try:
            # Create a temporary directory for PDF images
            with tempfile.TemporaryDirectory(dir=self.temp_dir) as temp_dir:
                # Convert PDF to images
                if isinstance(pdf_file, (str, Path)):
                    pdf_path = pdf_file
                else:
                    # Save the PDF content to a temporary file
                    temp_pdf = os.path.join(temp_dir, "temp.pdf")
                    pos = pdf_file.tell()
                    pdf_file.seek(0)
                    with open(temp_pdf, 'wb') as f:
                        f.write(pdf_file.read())
                    pdf_file.seek(pos)
                    pdf_path = temp_pdf
                
                # Convert PDF pages to images
                pdf_pages = pdf2image.convert_from_path(
                    pdf_path,
                    dpi=300,
                    output_folder=temp_dir,
                    fmt="jpeg",
                    paths_only=True
                )
                
                # Process requested pages
                result = {}
                page_nums = pages if pages else range(1, len(pdf_pages) + 1)
                
                for i, page_num in enumerate(page_nums, 1):
                    if 1 <= page_num <= len(pdf_pages):
                        # Get the image path for this page
                        img_path = pdf_pages[page_num - 1]
                        
                        # Extract text from this page
                        img = Image.open(img_path)
                        if preprocess:
                            img = self._preprocess_image(img)
                        
                        ocr_lang = lang or self.language
                        text = pytesseract.image_to_string(img, lang=ocr_lang)
                        
                        result[page_num] = text
                        logger.info(f"OCR processed PDF page {page_num}, extracted {len(text)} characters")
                
                return result
                
        except Exception as e:
            logger.error(f"Failed to process PDF: {str(e)}")
            raise OCRException(f"Failed to process PDF: {str(e)}")
    
    def _preprocess_image(self, img: "Image.Image") -> "Image.Image":
        """
        Preprocess an image for better OCR results.
        
        Args:
            img: PIL Image object
            
        Returns:
            Preprocessed PIL Image object
        """
        # Convert to grayscale
        img = img.convert('L')
        
        # Increase contrast
        img = img.point(lambda x: 0 if x < 128 else 255)
        
        return img
    
    async def extract_text(self, 
                         file_content: BinaryIO, 
                         filename: str,
                         mime_type: str,
                         preprocess: bool = True,
                         lang: Optional[str] = None) -> str:
        """
        Extract text from a file using OCR if needed.
        
        Args:
            file_content: File content
            filename: Name of the file
            mime_type: MIME type of the file
            preprocess: Whether to preprocess images for better OCR results
            lang: Language for OCR (overrides default)
            
        Returns:
            Extracted text content
            
        Raises:
            OCRException: If text extraction fails
        """
        try:
            if mime_type.startswith('image/'):
                # Process as image
                return await self.extract_text_from_image(
                    file_content,
                    preprocess=preprocess,
                    lang=lang
                )
            elif mime_type == 'application/pdf':
                # Process as PDF
                result = await self.extract_text_from_pdf(
                    file_content,
                    preprocess=preprocess,
                    lang=lang
                )
                # Combine text from all pages
                return '\n\n'.join(result.values())
            else:
                raise OCRException(f"Unsupported file type: {mime_type}")
                
        except Exception as e:
            logger.error(f"Failed to extract text from {filename}: {str(e)}")
            raise OCRException(f"Failed to extract text: {str(e)}")
    
    @staticmethod
    def is_scanned_document(file_content: BinaryIO, mime_type: str) -> bool:
        """
        Check if a file appears to be a scanned document.
        
        Args:
            file_content: File content
            mime_type: MIME type of the file
            
        Returns:
            True if the file appears to be a scanned document, False otherwise
        """
        # For now, assume all images and PDFs are scanned documents
        # TODO: Implement more sophisticated detection
        return mime_type.startswith('image/') or mime_type == 'application/pdf' 