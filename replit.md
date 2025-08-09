# PDF Figure Extractor

## Overview

PDF Figure Extractor is a Windows desktop application designed to extract high-quality figures and images from PDF documents. The application provides an interactive PDF viewer with precise cropping capabilities, enabling users to select and extract visual content at optimal resolution for research and documentation purposes.

## Recent Updates (August 2025)

### Major Changes
- **Zoom Functionality Removed**: Disabled all zoom controls (buttons, menu items, keyboard shortcuts) due to display issues while preserving cropping functionality at optimal fixed scale
- **Comprehensive Documentation Added**: Created detailed README.md with installation, usage instructions, and troubleshooting guide

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
The application uses a **desktop GUI architecture** built with Python's Tkinter framework. The UI follows a modular component-based design pattern with separate classes for different interface elements:

- **Main Application Controller** (`PDFViewerApp`): Central application logic and state management
- **Reusable UI Components** (`ui_components.py`): Modular widgets for crop management, naming patterns, and controls
- **Component Separation**: Each UI component is encapsulated in its own class for maintainability and reusability

The UI layout uses a **two-panel design** with a left control panel for settings and crop management, and a right panel for PDF display and interaction. The navigation system provides comprehensive page browsing.

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

### State Management
The application uses a **centralized state management** pattern:

- **Document State**: Current PDF document, page numbers, and fixed display scale
- **Selection State**: Active crop selections with coordinates and metadata
- **UI State**: Interface element states and user preferences
- **Threading**: Background processing for non-blocking UI operations

## External Dependencies

### Core Libraries
- **PyMuPDF (fitz)**: Primary PDF processing engine for document parsing, page rendering, and coordinate handling
- **Pillow (PIL)**: Image processing library for format conversion, quality optimization, and final output generation
- **Tkinter**: Built-in Python GUI framework for desktop interface components

### System Dependencies
- **Windows Desktop Environment**: Application designed specifically for Windows with native file system integration
- **Python Runtime**: Requires Python 3.x with standard library modules for file I/O, threading, and system operations

### File System Integration
- **Local File Access**: Direct filesystem operations for PDF loading and image saving
- **Directory Management**: Automatic output directory creation and file naming pattern management
- **Path Handling**: Cross-platform path operations using pathlib for robust file management