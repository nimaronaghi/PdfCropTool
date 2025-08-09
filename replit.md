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

The UI layout uses a **two-panel design** with a left control panel for settings and crop management, and a right panel for PDF display and interaction.

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

### State Management
The application uses a **centralized state management** pattern:

- **Document State**: Current PDF document, page numbers, and zoom levels
- **Selection State**: Active crop selections with coordinates and metadata
- **UI State**: Interface element states and user preferences
- **Threading**: Background processing for non-blocking UI operations

## External Dependencies

### Core PDF Processing
- **PyMuPDF (fitz)**: Primary PDF parsing and rendering engine
- **Pillow (PIL)**: Image processing and format conversion

### UI Framework
- **Tkinter**: Native Python GUI framework for cross-platform desktop interface
- **ttk**: Themed Tkinter widgets for modern UI appearance

### System Integration
- **pathlib**: Modern path handling for cross-platform file operations
- **threading**: Background task processing to maintain UI responsiveness
- **os**: Operating system interface for file operations and system integration

### Built-in Python Modules
- **datetime**: Timestamp formatting for file metadata display
- **sys**: System-specific parameters and functions for application lifecycle management