# PDF Figure Extractor

## Overview

PDF Figure Extractor is a desktop application built for Windows that enables users to extract high-quality figures and images from PDF documents. The application provides an interactive PDF viewer with cropping capabilities, allowing users to select specific regions of PDF pages and extract them as high-DPI images. The tool is designed for researchers, students, and professionals who need to extract figures from academic papers, reports, or other PDF documents while maintaining image quality.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
The application uses a **desktop GUI architecture** built with Python's Tkinter framework. The UI follows a modular component-based design pattern with separate classes for different interface elements:

- **Main Application Controller** (`PDFViewerApp`): Central application logic and state management
- **Reusable UI Components** (`ui_components.py`): Modular widgets for crop management, naming patterns, and controls
- **Component Separation**: Each UI component is encapsulated in its own class for maintainability and reusability

The UI layout uses a **two-panel design** with a left control panel for settings and crop management, and a right panel for PDF display and interaction. The navigation system provides comprehensive page control including direct page input, first/last page buttons, and real-time input validation.

### PDF Processing Architecture
The application employs a **document processing pipeline** using PyMuPDF (fitz) as the core PDF engine:

- **Document Loading**: Direct PDF document object handling for efficient memory usage
- **Page Rendering**: On-demand page rendering with caching for performance
- **High-DPI Extraction**: Dynamic scaling calculations to ensure extracted images maintain quality at 300+ DPI
- **Coordinate Transformation**: Conversion between display coordinates and PDF native coordinates for accurate cropping

### Image Extraction System
The image extraction follows a **quality-first approach**:

- **Adaptive Scaling**: Automatically calculates optimal extraction resolution based on source content
- **Native Resolution Preservation**: Extracts at PDF native resolution or higher to maintain quality
- **PIL Integration**: Uses Pillow (PIL) for final image processing and format conversion
- **Dual Save Options**: Both batch export to specified directory and individual crop saving with custom filenames/locations
- **Resolution Verification**: Real-time DPI calculation and quality rating display with detailed metadata reporting
- **Quality Preview**: Pre-extraction resolution estimates with file size and quality ratings

### State Management
The application uses a **centralized state management** pattern:

- **Document State**: Current PDF document, page numbers, and zoom levels
- **Selection State**: Active crop selections with coordinates and metadata
- **UI State**: Interface element states and user preferences
- **Threading**: Background processing for non-blocking UI operations

## Recent Updates (January 2025)

### New Features Added
- **URL PDF Loading**: Direct PDF loading from Google Drive and other URLs with automatic link conversion
- **Crop Renaming**: Individual crop renaming functionality with dialog interface
- **Sequential Naming Templates**: Updated to Q{:04d}, A{:04d}, H{:04d} format as requested
- **Keyboard Shortcuts**: Comprehensive shortcuts for all major operations
- **Undo Functionality**: Ctrl+Z to undo last crop selection
- **Enhanced Navigation**: Delete/Backspace keys for crop deletion
- **Google Drive Integration**: Framework for uploading exported crops (requires API setup)
- **Adaptive Naming System**: Smart naming that learns from user rename patterns and automatically applies them to future crops
- **Continuous PDF Scrolling**: Seamless mouse-only navigation through entire PDF documents with all pages displayed continuously
- **Advanced Text Search**: Full-text search with result highlighting and navigation between found instances
- **Auto-Visualization Highlighting**: Automatic highlighting of scientific visualization keywords (fig, figure, plot, diagram, etc.) in blue

### Keyboard Shortcuts
- **File Operations**: Ctrl+O (Open), Ctrl+U (URL Load), Ctrl+E (Export), Ctrl+G (Upload to Drive)
- **View Controls**: Ctrl+Plus/Minus (Zoom), Ctrl+0 (Reset), Ctrl+W (Fit Width)
- **Crop Management**: Ctrl+Z (Undo), Delete/Backspace (Remove Selected)
- **Navigation**: Arrow keys, Page Up/Down, Home/End for page navigation
- **Search Functions**: Ctrl+F (Focus Search), F3 (Next Result), Shift+F3 (Previous Result)

## External Dependencies

### Core PDF Processing
- **PyMuPDF (fitz)**: Primary PDF parsing and rendering engine
- **Pillow (PIL)**: Image processing and format conversion

### UI Framework
- **Tkinter**: Native Python GUI framework for cross-platform desktop interface
- **ttk**: Themed Tkinter widgets for modern UI appearance

### Network and File Operations
- **urllib**: URL downloading and parsing for PDF loading from web sources
- **tempfile**: Temporary file handling for downloaded PDFs
- **shutil**: File operations for download management

### System Integration
- **pathlib**: Modern path handling for cross-platform file operations
- **threading**: Background task processing to maintain UI responsiveness
- **os**: Operating system interface for file operations and system integration

### Built-in Python Modules
- **datetime**: Timestamp formatting for file metadata display
- **sys**: System-specific parameters and functions for application lifecycle management