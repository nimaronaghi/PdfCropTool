"""
Image Extractor - High-DPI image extraction from PDF documents
"""

import fitz  # PyMuPDF
from PIL import Image
import os
import io
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
            page_rect = page.rect
            
            # Get the maximum resolution available from the PDF page
            # First, check if the page has embedded images to determine native resolution
            native_scale = self._get_page_native_scale(page)
            
            # Use reasonable scale based on native content but cap for file size
            # For most figures, 300-600 DPI is more than sufficient
            extraction_scale = max(min(native_scale, 8.0), 4.0)  # Between 4x-8x scale (288-576 DPI)
            
            # Get actual output dimensions for verification
            crop_width = coords[2] - coords[0]  # in display pixels
            crop_height = coords[3] - coords[1]  # in display pixels
            
            # Get page dimensions for coordinate validation
            page_rect = page.rect
            
            # Use pre-calculated PDF coordinates if available (new format)
            if 'pdf_coords' in crop_data:
                pdf_left, pdf_top, pdf_right, pdf_bottom = crop_data['pdf_coords']
            else:
                # Fallback: convert display coordinates to PDF coordinates (legacy format)
                display_render_scale = display_zoom * 2.0
                pdf_left = coords[0] / display_render_scale
                pdf_top = coords[1] / display_render_scale  
                pdf_right = coords[2] / display_render_scale
                pdf_bottom = coords[3] / display_render_scale
            
            # Ensure coordinates are within page bounds
            pdf_left = max(0, min(pdf_left, page_rect.width))
            pdf_top = max(0, min(pdf_top, page_rect.height))
            pdf_right = max(pdf_left + 1, min(pdf_right, page_rect.width))
            pdf_bottom = max(pdf_top + 1, min(pdf_bottom, page_rect.height))
            
            # Create clip rectangle in PDF coordinates
            clip_rect = fitz.Rect(pdf_left, pdf_top, pdf_right, pdf_bottom)
            
            # Validate the clip rectangle
            if clip_rect.is_empty or clip_rect.width < 1 or clip_rect.height < 1:
                raise ValueError("Invalid crop rectangle dimensions")
            
            # Create transformation matrix for high-resolution rendering
            matrix = fitz.Matrix(extraction_scale, extraction_scale)
            
            # Render the page with clipping at target resolution
            try:
                pix = page.get_pixmap(matrix=matrix, clip=clip_rect)
                
                # Validate the pixmap
                if pix.width == 0 or pix.height == 0:
                    raise ValueError("Generated pixmap has zero dimensions")
                    
            except Exception as render_error:
                # Fallback to simpler rendering if complex clipping fails
                print(f"Primary rendering failed: {render_error}")
                print(f"Trying fallback rendering method...")
                
                # Try with a simpler matrix
                simple_matrix = fitz.Matrix(4.0, 4.0)  # Fixed 288 DPI
                pix = page.get_pixmap(matrix=simple_matrix, clip=clip_rect)
                
                if pix.width == 0 or pix.height == 0:
                    raise ValueError("Fallback rendering also failed - invalid crop area")
            
            # Convert to PIL Image with error checking
            try:
                img_data = pix.tobytes("ppm")
                if len(img_data) == 0:
                    raise ValueError("Empty image data from pixmap")
                    
                pil_image = Image.open(io.BytesIO(img_data))
                
                # Verify the PIL image is valid
                if pil_image.width == 0 or pil_image.height == 0:
                    raise ValueError("PIL image has zero dimensions")
                    
            except Exception as conversion_error:
                pix = None  # Clean up
                raise ValueError(f"Failed to convert pixmap to image: {conversion_error}")
            
            # Calculate actual DPI achieved
            actual_dpi = int(72 * extraction_scale)
            
            # Calculate physical dimensions at this DPI
            width_inches = pil_image.width / actual_dpi
            height_inches = pil_image.height / actual_dpi
            
            # Add extraction metadata to image
            metadata = {
                'extraction_dpi': actual_dpi,
                'native_scale': native_scale,
                'width_pixels': pil_image.width,
                'height_pixels': pil_image.height,
                'width_inches': round(width_inches, 3),
                'height_inches': round(height_inches, 3),
                'page_number': page_num + 1,
                'extraction_scale': round(extraction_scale, 2),
                'source_quality': 'Maximum Available from PDF'
            }
            
            # Determine output format based on content and size
            file_size_mb = (pil_image.width * pil_image.height * 3) / (1024 * 1024)
            
            if file_size_mb > 50:  # If estimated size > 50MB, use JPEG with high quality
                if not output_path.lower().endswith('.jpg') and not output_path.lower().endswith('.jpeg'):
                    output_path = output_path.rsplit('.', 1)[0] + '.jpg'
                
                pil_image.save(
                    output_path,
                    "JPEG",
                    dpi=(actual_dpi, actual_dpi),
                    quality=95,  # High quality JPEG
                    optimize=True
                )
            else:
                # Use PNG for smaller files to preserve quality
                pil_image.save(
                    output_path,
                    "PNG",
                    dpi=(actual_dpi, actual_dpi),
                    optimize=True,  # PNG optimization without quality loss
                    compress_level=6  # Moderate compression for reasonable file size
                )
            
            return metadata
            
        except Exception as e:
            print(f"Error extracting crop: {str(e)}")
            return None
            
    def _get_page_native_scale(self, page):
        """
        Determine the native scale factor for maximum quality extraction
        
        Args:
            page: PyMuPDF page object
            
        Returns:
            float: Native scale factor for the page
        """
        try:
            # Check for embedded images in the page to determine native resolution
            image_list = page.get_images()
            max_scale = 2.0  # Default minimum scale
            
            if image_list:
                # Analyze embedded images to find the highest resolution
                for img_index, img in enumerate(image_list):
                    try:
                        # Get image dimensions
                        xref = img[0]
                        base_image = self.pdf_document.extract_image(xref)
                        
                        img_width = base_image["width"]
                        img_height = base_image["height"]
                        
                        # Get image placement on page
                        img_dict = page.get_image_bbox(img)
                        if img_dict:
                            # Calculate the scale needed to match native image resolution
                            page_width = img_dict.width
                            page_height = img_dict.height
                            
                            scale_x = img_width / page_width if page_width > 0 else 1.0
                            scale_y = img_height / page_height if page_height > 0 else 1.0
                            
                            # Use the higher scale factor
                            img_scale = max(scale_x, scale_y)
                            max_scale = max(max_scale, img_scale)
                            
                    except Exception:
                        continue
            
            # Also consider text rendering quality - vector content can scale higher
            # For vector content (text, drawings), we can use high scales
            text_objects = page.get_text("dict")
            has_text = len(text_objects.get("blocks", [])) > 0
            
            if has_text:
                # For pages with text, use moderate scaling for readability
                max_scale = max(max_scale, 6.0)  # Up to 432 DPI for text
            
            # Cap at reasonable maximum to avoid huge files
            return min(max_scale, 8.0)  # Max 576 DPI for reasonable file sizes
            
        except Exception as e:
            print(f"Error determining native scale: {e}")
            return 4.0  # Default to 288 DPI
            
    def get_crop_preview_info(self, crop_data):
        """
        Get preview information about a crop before extraction
        
        Args:
            crop_data: Dictionary containing page, coords, and zoom info
            
        Returns:
            dict: Preview information including estimated dimensions and DPI
        """
        try:
            page_num = crop_data['page']
            coords = crop_data['coords']
            display_zoom = crop_data['zoom']
            
            page = self.pdf_document[page_num]
            
            # Calculate what the extraction parameters would be using native resolution
            native_scale = self._get_page_native_scale(page)
            extraction_scale = max(native_scale, 4.0)
            
            # Use pre-calculated PDF coordinates if available (new format)
            if 'pdf_coords' in crop_data:
                pdf_left, pdf_top, pdf_right, pdf_bottom = crop_data['pdf_coords']
            else:
                # Fallback: convert display coordinates to PDF coordinates (legacy format)
                display_render_scale = display_zoom * 2.0
                pdf_left = coords[0] / display_render_scale
                pdf_top = coords[1] / display_render_scale
                pdf_right = coords[2] / display_render_scale
                pdf_bottom = coords[3] / display_render_scale
            
            # Calculate PDF dimensions
            pdf_width = pdf_right - pdf_left
            pdf_height = pdf_bottom - pdf_top
            
            # Calculate final output dimensions at extraction scale
            output_width = int(pdf_width * extraction_scale)
            output_height = int(pdf_height * extraction_scale)
            
            # Calculate actual DPI
            actual_dpi = int(72 * extraction_scale)
            
            # Calculate physical dimensions
            width_inches = output_width / actual_dpi
            height_inches = output_height / actual_dpi
            
            return {
                'estimated_dpi': actual_dpi,
                'native_scale': native_scale,
                'output_width': output_width,
                'output_height': output_height,
                'width_inches': round(width_inches, 3),
                'height_inches': round(height_inches, 3),
                'file_size_estimate': self._estimate_file_size(output_width, output_height),
                'quality_rating': self._get_quality_rating(actual_dpi),
                'source_quality': 'Maximum from PDF Native Resolution'
            }
            
        except Exception as e:
            print(f"Error getting crop preview: {str(e)}")
            return None
            
    def _estimate_file_size(self, width, height):
        """Estimate PNG file size in MB"""
        # Rough estimation: PNG typically uses 3-4 bytes per pixel for RGB
        bytes_estimate = width * height * 3.5
        mb_estimate = bytes_estimate / (1024 * 1024)
        return round(mb_estimate, 2)
        
    def _get_quality_rating(self, dpi):
        """Get quality rating based on DPI"""
        if dpi >= 600:
            return "Excellent (Print Ready)"
        elif dpi >= 300:
            return "Very Good (Print Quality)"
        elif dpi >= 200:
            return "Good (Web/Screen)"
        elif dpi >= 150:
            return "Fair (Low Print)"
        else:
            return "Poor (Screen Only)"
            
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
        
        # Cap at reasonable maximum (600 DPI)
        return min(int(optimal_dpi), 600)
        
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
