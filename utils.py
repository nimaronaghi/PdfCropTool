"""
Utility Functions - Helper functions for the PDF viewer application
"""

import os
import tkinter as tk
from pathlib import Path
import fitz  # PyMuPDF
from datetime import datetime

def get_unique_filename(filepath):
    """
    Get a unique filename by appending a number if the file already exists.
    
    Args:
        filepath: Desired file path
        
    Returns:
        str: Unique file path
    """
    if not os.path.exists(filepath):
        return filepath
    
    # Split into base and extension
    path = Path(filepath)
    directory = path.parent
    stem = path.stem
    suffix = path.suffix
    
    # Try adding numbers until we find one that doesn't exist
    counter = 2
    while True:
        new_path = directory / f"{stem}_{counter}{suffix}"
        if not new_path.exists():
            return str(new_path)
        counter += 1

def format_file_size(size_bytes):
    """
    Format file size in human readable format
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        str: Formatted size string
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
        
    return f"{size_bytes:.1f} {size_names[i]}"

def get_pdf_info(pdf_document, file_path):
    """
    Get comprehensive information about a PDF document
    
    Args:
        pdf_document: PyMuPDF document object
        file_path: Path to the PDF file
        
    Returns:
        str: Formatted PDF information
    """
    try:
        # Basic file information
        file_stat = os.stat(file_path)
        file_size = format_file_size(file_stat.st_size)
        mod_time = datetime.fromtimestamp(file_stat.st_mtime).strftime("%Y-%m-%d %H:%M")
        
        # PDF metadata
        metadata = pdf_document.metadata
        
        # Document information
        page_count = len(pdf_document)
        
        # Get first page dimensions for reference
        first_page = pdf_document[0]
        page_rect = first_page.rect
        page_width_pt = page_rect.width
        page_height_pt = page_rect.height
        page_width_in = page_width_pt / 72
        page_height_in = page_height_pt / 72
        
        # Check if PDF is encrypted
        is_encrypted = pdf_document.needs_pass
        
        # Build info string
        info_lines = [
            f"Filename: {os.path.basename(file_path)}",
            f"File Size: {file_size}",
            f"Modified: {mod_time}",
            "",
            f"Pages: {page_count}",
            f"Encrypted: {'Yes' if is_encrypted else 'No'}",
            "",
            f"Page Size: {page_width_pt:.0f} × {page_height_pt:.0f} pt",
            f"({page_width_in:.1f}\" × {page_height_in:.1f}\")",
            "",
        ]
        
        # Add metadata if available
        if metadata.get('title'):
            info_lines.append(f"Title: {metadata['title']}")
        if metadata.get('author'):
            info_lines.append(f"Author: {metadata['author']}")
        if metadata.get('subject'):
            info_lines.append(f"Subject: {metadata['subject']}")
        if metadata.get('creator'):
            info_lines.append(f"Creator: {metadata['creator']}")
        if metadata.get('producer'):
            info_lines.append(f"Producer: {metadata['producer']}")
            
        return "\n".join(info_lines)
        
    except Exception as e:
        return f"Error reading PDF info:\n{str(e)}"

def validate_naming_pattern(pattern):
    """
    Validate a file naming pattern
    
    Args:
        pattern: The naming pattern string
        
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        # Test the pattern with a sample number
        test_filename = pattern.format(1)
        
        # Check for invalid filename characters
        invalid_chars = '<>:"/\\|?*'
        if any(char in test_filename for char in invalid_chars):
            return False, "Pattern contains invalid filename characters"
            
        # Check if pattern produces different names
        name1 = pattern.format(1)
        name2 = pattern.format(2)
        if name1 == name2:
            return False, "Pattern does not differentiate between numbers"
            
        return True, ""
        
    except (ValueError, KeyError) as e:
        return False, f"Invalid pattern format: {str(e)}"
    except Exception as e:
        return False, f"Pattern error: {str(e)}"

def ensure_directory_exists(directory_path):
    """
    Ensure a directory exists, create if necessary
    
    Args:
        directory_path: Path to the directory
        
    Returns:
        bool: True if directory exists or was created successfully
    """
    try:
        Path(directory_path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating directory {directory_path}: {str(e)}")
        return False

# Removed duplicate get_unique_filename function - using the one at line 11

def calculate_crop_dpi(crop_coords, zoom_level, target_pixels=1920):
    """
    Calculate optimal DPI for crop extraction
    
    Args:
        crop_coords: Crop coordinates (left, top, right, bottom)
        zoom_level: Current zoom level
        target_pixels: Target width in pixels
        
    Returns:
        int: Recommended DPI
    """
    crop_width_display = crop_coords[2] - crop_coords[0]
    
    # Convert to PDF points (accounting for zoom and display scaling)
    crop_width_points = crop_width_display / zoom_level
    crop_width_inches = crop_width_points / 72
    
    # Calculate DPI needed for target pixel width
    if crop_width_inches > 0:
        recommended_dpi = target_pixels / crop_width_inches
        return min(int(recommended_dpi), 600)  # Cap at reasonable maximum
    
    return 300  # Default DPI

def get_supported_formats():
    """
    Get list of supported export formats - PNG only for lossless quality preservation
    
    Returns:
        list: List of format dictionaries
    """
    return [
        {
            'name': 'PNG (Lossless)',
            'extension': '.png',
            'description': 'Preserves exact DPI and quality without compression artifacts',
            'mime_type': 'image/png'
        }
    ]

def create_desktop_shortcut(app_path, shortcut_path):
    """
    Create a desktop shortcut (Windows only)
    
    Args:
        app_path: Path to the application executable
        shortcut_path: Path where shortcut should be created
        
    Returns:
        bool: True if shortcut was created successfully
    """
    try:
        import win32com.client
        
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = app_path
        shortcut.WindowStyle = 1  # Normal window
        shortcut.IconLocation = app_path
        shortcut.save()
        
        return True
        
    except ImportError:
        # pywin32 not available
        return False
    except Exception as e:
        print(f"Error creating shortcut: {str(e)}")
        return False

def get_system_info():
    """
    Get system information for troubleshooting
    
    Returns:
        dict: System information
    """
    import platform
    import sys
    
    return {
        'platform': platform.platform(),
        'architecture': platform.architecture(),
        'python_version': sys.version,
        'tkinter_version': getattr(tk, 'TkVersion', 'Unknown'),
        'pymupdf_version': getattr(fitz, '__version__', 'Unknown')
    }

def log_error(error_msg, error_type="General"):
    """
    Log error to file for debugging
    
    Args:
        error_msg: Error message
        error_type: Type of error
    """
    try:
        log_dir = Path.home() / "PDFExtractor_Logs"
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"error_log_{datetime.now().strftime('%Y%m%d')}.txt"
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {error_type}: {error_msg}\n"
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
            
    except Exception:
        # If logging fails, just ignore it
        pass
