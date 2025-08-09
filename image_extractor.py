"""
Image Extractor - High-DPI image extraction from PDF documents
"""

import fitz  # PyMuPDF
from PIL import Image
import os
from pathlib import Path

class ImageExtractor:
    """Class for extracting high-quality images from PDF documents"""
    
    def __init__(self, pdf_document):
        """
        Initialize the image extractor
        
        Args:
            pdf_document: PyMuPDF document object
        """
        self.pdf_document = pdf_document
        self.max_dpi = 300  # Maximum DPI for extraction
        
    def extract_crop(self, crop_data, output_path):
        """
        Extract a cropped region from a PDF page
        
        Args:
            crop_data: Dictionary containing page, coords, and zoom info
            output_path: Path to save the extracted image
            
        Returns:
            bool: True if extraction was successful, False otherwise
        """
        try:
            page_num = crop_data['page']
            coords = crop_data['coords']  # (left, top, right, bottom) in display coordinates
            display_zoom = crop_data['zoom']
            
            # Get the PDF page
            page = self.pdf_document[page_num]
            
            # Calculate extraction parameters for maximum quality
            # We want to extract at native resolution or higher
            extraction_scale = max(2.0, 300 / 72)  # At least 300 DPI
            
            # Create transformation matrix for high-resolution rendering
            matrix = fitz.Matrix(extraction_scale, extraction_scale)
            
            # Convert display coordinates to PDF coordinates
            # Display coordinates are based on zoom level
            scale_factor = extraction_scale / (display_zoom * 2)  # 2x was used for initial rendering
            
            pdf_left = coords[0] * scale_factor
            pdf_top = coords[1] * scale_factor
            pdf_right = coords[2] * scale_factor
            pdf_bottom = coords[3] * scale_factor
            
            # Create clip rectangle in PDF coordinates
            clip_rect = fitz.Rect(pdf_left, pdf_top, pdf_right, pdf_bottom)
            
            # Render the page with clipping
            pix = page.get_pixmap(matrix=matrix, clip=clip_rect)
            
            # Convert to PIL Image
            img_data = pix.tobytes("ppm")
            pil_image = Image.open(io.BytesIO(img_data))
            
            # Set DPI metadata
            dpi = int(72 * extraction_scale)
            
            # Save as PNG with maximum quality and DPI metadata
            pil_image.save(
                output_path,
                "PNG",
                dpi=(dpi, dpi),
                optimize=False,  # Don't optimize to preserve quality
                compress_level=0  # No compression for maximum quality
            )
            
            return True
            
        except Exception as e:
            print(f"Error extracting crop: {str(e)}")
            return False
            
    def get_page_info(self, page_num):
        """
        Get information about a specific page
        
        Args:
            page_num: Page number (0-based)
            
        Returns:
            dict: Page information including dimensions and DPI
        """
        try:
            page = self.pdf_document[page_num]
            rect = page.rect
            
            return {
                'width': rect.width,
                'height': rect.height,
                'width_inches': rect.width / 72,
                'height_inches': rect.height / 72,
                'native_dpi': 72  # PDF native DPI
            }
            
        except Exception as e:
            print(f"Error getting page info: {str(e)}")
            return None
            
    def extract_all_images(self, output_dir):
        """
        Extract all embedded images from the PDF document
        
        Args:
            output_dir: Directory to save extracted images
            
        Returns:
            list: List of extracted image paths
        """
        extracted_images = []
        
        try:
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            for page_num in range(len(self.pdf_document)):
                page = self.pdf_document[page_num]
                image_list = page.get_images()
                
                for img_index, img in enumerate(image_list):
                    xref = img[0]  # Image reference number
                    
                    # Get image data
                    base_image = self.pdf_document.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    
                    # Generate filename
                    filename = f"page_{page_num + 1}_image_{img_index + 1}.{image_ext}"
                    image_path = os.path.join(output_dir, filename)
                    
                    # Save image
                    with open(image_path, "wb") as image_file:
                        image_file.write(image_bytes)
                        
                    extracted_images.append(image_path)
                    
            return extracted_images
            
        except Exception as e:
            print(f"Error extracting embedded images: {str(e)}")
            return []
            
    def get_optimal_dpi(self, crop_coords, target_width=1920):
        """
        Calculate optimal DPI for extraction based on crop size
        
        Args:
            crop_coords: Crop coordinates (left, top, right, bottom)
            target_width: Target width in pixels for the extracted image
            
        Returns:
            int: Optimal DPI for extraction
        """
        crop_width = crop_coords[2] - crop_coords[0]
        
        # Calculate DPI needed to achieve target width
        crop_width_inches = crop_width / 72  # Convert points to inches
        optimal_dpi = target_width / crop_width_inches
        
        # Cap at reasonable maximum
        return min(int(optimal_dpi), self.max_dpi)
        
    def preview_crop(self, crop_data, max_size=(300, 300)):
        """
        Generate a preview of the crop selection
        
        Args:
            crop_data: Dictionary containing page, coords, and zoom info
            max_size: Maximum size for preview (width, height)
            
        Returns:
            PIL.Image: Preview image or None if failed
        """
        try:
            page_num = crop_data['page']
            coords = crop_data['coords']
            
            page = self.pdf_document[page_num]
            
            # Use moderate resolution for preview
            matrix = fitz.Matrix(1.5, 1.5)
            
            # Convert coordinates
            scale_factor = 1.5 / (crop_data['zoom'] * 2)
            pdf_left = coords[0] * scale_factor
            pdf_top = coords[1] * scale_factor  
            pdf_right = coords[2] * scale_factor
            pdf_bottom = coords[3] * scale_factor
            
            clip_rect = fitz.Rect(pdf_left, pdf_top, pdf_right, pdf_bottom)
            pix = page.get_pixmap(matrix=matrix, clip=clip_rect)
            
            # Convert to PIL
            import io
            img_data = pix.tobytes("ppm")
            pil_image = Image.open(io.BytesIO(img_data))
            
            # Resize to fit preview size
            pil_image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            return pil_image
            
        except Exception as e:
            print(f"Error generating crop preview: {str(e)}")
            return None
