"""
Document watermarking service.

This module provides functionality for adding watermarks to documents,
supporting both text and image watermarks with configurable positions
and transparency levels.
"""

import os
import io
import uuid
from typing import Union, Optional, Dict, Any, BinaryIO, Tuple
from enum import Enum
from datetime import datetime
import base64
from dataclasses import dataclass
from pathlib import Path

from ...utils.errors import ValidationError
from ...utils.logging import get_logger

logger = get_logger(__name__)

# Try to import optional dependencies
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("PIL not available, image watermarking will be limited")

try:
    from PyPDF2 import PdfReader, PdfWriter
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logger.warning("PDF libraries not available, PDF watermarking will be limited")


class WatermarkType(Enum):
    """Types of watermarks that can be applied to documents."""
    TEXT = "text"
    IMAGE = "image"
    USER_INFO = "user_info"
    TIMESTAMP = "timestamp"
    CONFIDENTIAL = "confidential"
    DRAFT = "draft"
    CUSTOM = "custom"


class WatermarkPosition(Enum):
    """Positions where watermarks can be placed on a document."""
    CENTER = "center"
    TOP_LEFT = "top_left"
    TOP_RIGHT = "top_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_RIGHT = "bottom_right"
    TOP_CENTER = "top_center"
    BOTTOM_CENTER = "bottom_center"
    TILE = "tile"  # Repeating pattern across the document


@dataclass
class WatermarkOptions:
    """Configuration options for watermarks."""
    opacity: float = 0.3  # 0.0 to 1.0, with 1.0 being fully opaque
    rotation: float = 0.0  # Rotation angle in degrees
    scale: float = 1.0  # Scale factor for the watermark
    color: Tuple[int, int, int] = (128, 128, 128)  # RGB color tuple
    font_size: int = 36  # Font size for text watermarks
    font_path: Optional[str] = None  # Path to custom font file
    padding: int = 20  # Padding from edges for positioned watermarks
    repeat_spacing: int = 200  # Spacing between repeated watermarks for tiling


class DocumentWatermark:
    """
    Service for adding watermarks to documents.
    
    This service supports adding text or image watermarks to documents
    with configurable positioning, opacity, and other visual properties.
    """
    
    def __init__(self):
        """Initialize the document watermarking service."""
        self._default_font = None
        self._cached_fonts: Dict[str, ImageFont.FreeTypeFont] = {}
        logger.info("Document watermarking service initialized")
    
    def _get_font(self, options: WatermarkOptions) -> ImageFont.FreeTypeFont:
        """
        Get the font to use for text watermarks.
        
        Args:
            options: The watermark options containing font information.
            
        Returns:
            A PIL font object for rendering text.
        """
        if options.font_path:
            if options.font_path not in self._cached_fonts:
                try:
                    self._cached_fonts[options.font_path] = ImageFont.truetype(
                        options.font_path, size=options.font_size
                    )
                except (OSError, IOError):
                    logger.warning(f"Could not load font from {options.font_path}, using default")
                    if self._default_font is None:
                        self._default_font = ImageFont.load_default()
                    return self._default_font
            return self._cached_fonts[options.font_path]
        
        # Use default font if no path specified
        if self._default_font is None:
            self._default_font = ImageFont.load_default()
        return self._default_font
    
    def _calculate_position(
        self, position: WatermarkPosition, 
        doc_width: int, doc_height: int,
        watermark_width: int, watermark_height: int,
        options: WatermarkOptions
    ) -> Tuple[int, int]:
        """
        Calculate the position of the watermark on the document.
        
        Args:
            position: The position enum value for the watermark.
            doc_width: The width of the document.
            doc_height: The height of the document.
            watermark_width: The width of the watermark.
            watermark_height: The height of the watermark.
            options: Watermark options containing padding information.
            
        Returns:
            A tuple of (x, y) coordinates for the watermark.
        """
        padding = options.padding
        
        if position == WatermarkPosition.CENTER:
            return (
                (doc_width - watermark_width) // 2,
                (doc_height - watermark_height) // 2
            )
        elif position == WatermarkPosition.TOP_LEFT:
            return (padding, padding)
        elif position == WatermarkPosition.TOP_RIGHT:
            return (doc_width - watermark_width - padding, padding)
        elif position == WatermarkPosition.BOTTOM_LEFT:
            return (padding, doc_height - watermark_height - padding)
        elif position == WatermarkPosition.BOTTOM_RIGHT:
            return (doc_width - watermark_width - padding, doc_height - watermark_height - padding)
        elif position == WatermarkPosition.TOP_CENTER:
            return ((doc_width - watermark_width) // 2, padding)
        elif position == WatermarkPosition.BOTTOM_CENTER:
            return ((doc_width - watermark_width) // 2, doc_height - watermark_height - padding)
        
        # Default to center if unknown position
        return (
            (doc_width - watermark_width) // 2,
            (doc_height - watermark_height) // 2
        )
    
    def _create_text_watermark(
        self, text: str, options: WatermarkOptions
    ) -> Image.Image:
        """
        Create a text watermark image.
        
        Args:
            text: The text to render as a watermark.
            options: Watermark options for customizing appearance.
            
        Returns:
            A PIL Image containing the rendered text.
        """
        font = self._get_font(options)
        # Get text size to create appropriate image size
        text_width, text_height = font.getsize(text)
        
        # Create a transparent image for the text
        text_img = Image.new('RGBA', (text_width + 20, text_height + 20), (0, 0, 0, 0))
        draw = ImageDraw.Draw(text_img)
        
        # Draw the text on the image
        color_with_alpha = options.color + (int(255 * options.opacity),)
        draw.text((10, 10), text, font=font, fill=color_with_alpha)
        
        # Apply rotation if specified
        if options.rotation != 0.0:
            text_img = text_img.rotate(options.rotation, expand=True, resample=Image.BICUBIC)
        
        # Apply scaling if specified
        if options.scale != 1.0:
            new_size = (int(text_img.width * options.scale), int(text_img.height * options.scale))
            text_img = text_img.resize(new_size, resample=Image.LANCZOS)
        
        return text_img
    
    def _create_image_watermark(
        self, image_path: Union[str, Path], options: WatermarkOptions
    ) -> Image.Image:
        """
        Create an image watermark.
        
        Args:
            image_path: Path to the image file to use as a watermark.
            options: Watermark options for customizing appearance.
            
        Returns:
            A PIL Image containing the processed image watermark.
        """
        try:
            # Open and convert image to RGBA
            watermark_img = Image.open(image_path).convert("RGBA")
            
            # Apply scaling if specified
            if options.scale != 1.0:
                new_size = (int(watermark_img.width * options.scale), 
                           int(watermark_img.height * options.scale))
                watermark_img = watermark_img.resize(new_size, resample=Image.LANCZOS)
            
            # Apply rotation if specified
            if options.rotation != 0.0:
                watermark_img = watermark_img.rotate(
                    options.rotation, expand=True, resample=Image.BICUBIC
                )
            
            # Apply opacity
            if options.opacity != 1.0:
                data = watermark_img.getdata()
                new_data = []
                for item in data:
                    # Update alpha channel in each pixel
                    new_data.append(item[:3] + (int(item[3] * options.opacity),))
                watermark_img.putdata(new_data)
            
            return watermark_img
            
        except (IOError, OSError) as e:
            logger.error(f"Failed to load image watermark from {image_path}: {e}")
            # Create a simple text watermark as fallback
            return self._create_text_watermark("Watermark", options)
    
    def _apply_tiled_watermark(
        self, document: Image.Image, watermark: Image.Image, options: WatermarkOptions
    ) -> Image.Image:
        """
        Apply a tiled watermark pattern to the document.
        
        Args:
            document: The document image to watermark.
            watermark: The watermark image to tile across the document.
            options: Watermark options containing spacing information.
            
        Returns:
            The watermarked document image.
        """
        result = document.copy()
        spacing = options.repeat_spacing
        
        for y in range(0, document.height, spacing + watermark.height):
            for x in range(0, document.width, spacing + watermark.width):
                result.paste(watermark, (x, y), watermark)
        
        return result
    
    def apply_watermark(
        self,
        document_path: Union[str, Path],
        watermark_type: WatermarkType,
        watermark_content: Union[str, Path],
        position: WatermarkPosition = WatermarkPosition.BOTTOM_RIGHT,
        options: Optional[WatermarkOptions] = None,
        output_path: Optional[Union[str, Path]] = None
    ) -> Union[bytes, str]:
        """
        Apply a watermark to a document.
        
        Args:
            document_path: Path to the document to watermark.
            watermark_type: Type of watermark to apply (text or image).
            watermark_content: Text string or path to image for the watermark.
            position: Position to place the watermark on the document.
            options: Options for customizing the watermark appearance.
            output_path: Optional path to save the watermarked document.
            
        Returns:
            If output_path is provided, returns the path as a string.
            Otherwise, returns the watermarked document as bytes.
        """
        if options is None:
            options = WatermarkOptions()
        
        try:
            # Open the document
            document_img = Image.open(document_path).convert("RGBA")
            
            # Create the watermark based on type
            if watermark_type == WatermarkType.TEXT:
                watermark_img = self._create_text_watermark(str(watermark_content), options)
            elif watermark_type == WatermarkType.TIMESTAMP:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                watermark_img = self._create_text_watermark(f"Timestamp: {timestamp}", options)
            elif watermark_type == WatermarkType.CONFIDENTIAL:
                watermark_img = self._create_text_watermark("CONFIDENTIAL", options)
            elif watermark_type == WatermarkType.DRAFT:
                watermark_img = self._create_text_watermark("DRAFT", options)
            elif watermark_type == WatermarkType.USER_INFO:
                watermark_img = self._create_text_watermark(f"User: {watermark_content}", options)
            elif watermark_type == WatermarkType.IMAGE:
                watermark_img = self._create_image_watermark(watermark_content, options)
            else:  # Custom or fallback
                watermark_img = self._create_text_watermark(str(watermark_content), options)
            
            # Apply the watermark based on position
            if position == WatermarkPosition.TILE:
                result_img = self._apply_tiled_watermark(document_img, watermark_img, options)
            else:
                # Calculate the position
                pos = self._calculate_position(
                    position, document_img.width, document_img.height,
                    watermark_img.width, watermark_img.height, options
                )
                
                # Create a new image by pasting the watermark
                result_img = document_img.copy()
                result_img.paste(watermark_img, pos, watermark_img)
            
            # Convert result back to the original format if needed
            if document_img.format and document_img.format != "PNG":
                result_img = result_img.convert(document_img.mode)
            
            # Save or return the result
            if output_path:
                result_img.save(output_path)
                logger.info(f"Watermarked document saved to {output_path}")
                return str(output_path)
            else:
                output_buffer = io.BytesIO()
                result_img.save(output_buffer, format="PNG")
                logger.info("Watermarked document created in memory")
                return output_buffer.getvalue()
                
        except Exception as e:
            logger.error(f"Failed to apply watermark: {e}")
            raise ValueError(f"Failed to apply watermark: {e}")
    
    def create_default_confidential_watermark(
        self, document_path: Union[str, Path], output_path: Optional[Union[str, Path]] = None
    ) -> Union[bytes, str]:
        """
        Apply a standard "CONFIDENTIAL" watermark to a document.
        
        Args:
            document_path: Path to the document to watermark.
            output_path: Optional path to save the watermarked document.
            
        Returns:
            If output_path is provided, returns the path as a string.
            Otherwise, returns the watermarked document as bytes.
        """
        options = WatermarkOptions(
            opacity=0.3,
            rotation=45.0,
            scale=1.5,
            color=(255, 0, 0),
            font_size=72
        )
        return self.apply_watermark(
            document_path,
            WatermarkType.CONFIDENTIAL,
            "CONFIDENTIAL",
            WatermarkPosition.CENTER,
            options,
            output_path
        )
    
    def create_user_watermark(
        self, document_path: Union[str, Path], username: str, 
        output_path: Optional[Union[str, Path]] = None
    ) -> Union[bytes, str]:
        """
        Apply a user-specific watermark with timestamp to a document.
        
        Args:
            document_path: Path to the document to watermark.
            username: Username to include in the watermark.
            output_path: Optional path to save the watermarked document.
            
        Returns:
            If output_path is provided, returns the path as a string.
            Otherwise, returns the watermarked document as bytes.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        watermark_text = f"Downloaded by: {username} on {timestamp}"
        options = WatermarkOptions(
            opacity=0.5,
            color=(0, 0, 0),
            font_size=24
        )
        return self.apply_watermark(
            document_path,
            WatermarkType.TEXT,
            watermark_text,
            WatermarkPosition.BOTTOM_CENTER,
            options,
            output_path
        ) 