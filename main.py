"""
PDF Figure Extractor - Main Application Entry Point
A Windows desktop application for extracting high-DPI figures from PDF documents
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

from pdf_viewer import PDFViewerApp

def main():
    """Main entry point for the application"""
    try:
        # Create the main application window
        root = tk.Tk()
        root.title("PDF Figure Extractor")
        root.geometry("1200x800")
        root.minsize(800, 600)
        
        # Set window icon if available
        try:
            # Try to set a default icon
            root.iconbitmap(default="")
        except:
            pass
        
        # Create and run the PDF viewer application
        app = PDFViewerApp(root)
        
        # Center the window on screen
        root.update_idletasks()
        x = (root.winfo_screenwidth() - root.winfo_width()) // 2
        y = (root.winfo_screenheight() - root.winfo_height()) // 2
        root.geometry(f"+{x}+{y}")
        
        # Start the main event loop
        root.mainloop()
        
    except Exception as e:
        messagebox.showerror("Application Error", f"Failed to start application: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
