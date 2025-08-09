"""
PDF Viewer Component - Main UI and PDF Display Logic
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import fitz  # PyMuPDF
from PIL import Image, ImageTk
import os
import io
import threading
from pathlib import Path

from ui_components import CropFrame, NamingFrame, ControlFrame
from image_extractor import ImageExtractor
from utils import format_file_size, get_pdf_info

class PDFViewerApp:
    def __init__(self, root):
        self.root = root
        self.pdf_document = None
        self.current_page = 0
        self.zoom_level = 1.0
        self.pdf_images = []  # Cache for rendered pages
        self.crop_selections = []  # List of crop selections
        self.output_directory = ""
        self.naming_pattern = "figure_{:03d}"
        
        self.setup_ui()
        self.setup_bindings()
        
    def setup_ui(self):
        """Initialize the user interface"""
        # Create main menu
        self.create_menu()
        
        # Create main frames
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel for controls
        self.left_panel = ttk.Frame(self.main_frame, width=250)
        self.left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        self.left_panel.pack_propagate(False)
        
        # Right panel for PDF display
        self.right_panel = ttk.Frame(self.main_frame)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Setup control panels
        self.setup_control_panels()
        
        # Setup PDF viewer
        self.setup_pdf_viewer()
        
        # Status bar
        self.setup_status_bar()
        
        # Initial state - show welcome message
        self.show_welcome_message()
        
    def create_menu(self):
        """Create the application menu"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open PDF...", command=self.open_pdf, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit, accelerator="Ctrl+Q")
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Zoom In", command=self.zoom_in, accelerator="Ctrl++")
        view_menu.add_command(label="Zoom Out", command=self.zoom_out, accelerator="Ctrl+-")
        view_menu.add_command(label="Fit to Width", command=self.fit_to_width, accelerator="Ctrl+W")
        view_menu.add_command(label="Reset Zoom", command=self.reset_zoom, accelerator="Ctrl+0")
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Clear All Crops", command=self.clear_all_crops)
        tools_menu.add_command(label="Export All Crops", command=self.export_all_crops)
        
    def setup_control_panels(self):
        """Setup the left control panels"""
        # File operations frame
        file_frame = ttk.LabelFrame(self.left_panel, text="File Operations", padding=10)
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(file_frame, text="Open PDF", command=self.open_pdf).pack(fill=tk.X, pady=2)
        
        # PDF info frame
        self.info_frame = ttk.LabelFrame(self.left_panel, text="PDF Information", padding=10)
        self.info_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.info_text = tk.Text(self.info_frame, height=6, wrap=tk.WORD, state=tk.DISABLED)
        self.info_text.pack(fill=tk.BOTH, expand=True)
        
        # Navigation frame
        nav_frame = ttk.LabelFrame(self.left_panel, text="Navigation", padding=10)
        nav_frame.pack(fill=tk.X, pady=(0, 10))
        
        nav_buttons = ttk.Frame(nav_frame)
        nav_buttons.pack(fill=tk.X)
        
        self.prev_btn = ttk.Button(nav_buttons, text="◀", command=self.previous_page, width=5)
        self.prev_btn.pack(side=tk.LEFT)
        
        self.page_label = ttk.Label(nav_buttons, text="No PDF loaded")
        self.page_label.pack(side=tk.LEFT, expand=True)
        
        self.next_btn = ttk.Button(nav_buttons, text="▶", command=self.next_page, width=5)
        self.next_btn.pack(side=tk.RIGHT)
        
        # Zoom frame
        zoom_frame = ttk.LabelFrame(self.left_panel, text="Zoom", padding=10)
        zoom_frame.pack(fill=tk.X, pady=(0, 10))
        
        zoom_buttons = ttk.Frame(zoom_frame)
        zoom_buttons.pack(fill=tk.X)
        
        ttk.Button(zoom_buttons, text="−", command=self.zoom_out, width=3).pack(side=tk.LEFT)
        self.zoom_label = ttk.Label(zoom_buttons, text="100%")
        self.zoom_label.pack(side=tk.LEFT, expand=True)
        ttk.Button(zoom_buttons, text="+", command=self.zoom_in, width=3).pack(side=tk.RIGHT)
        
        ttk.Button(zoom_frame, text="Fit to Width", command=self.fit_to_width).pack(fill=tk.X, pady=(5, 0))
        
        # Crop frame
        self.crop_frame = CropFrame(self.left_panel, self)
        self.crop_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Naming frame
        self.naming_frame = NamingFrame(self.left_panel, self)
        self.naming_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Export frame
        export_frame = ttk.LabelFrame(self.left_panel, text="Export", padding=10)
        export_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Button(export_frame, text="Select Output Directory", 
                  command=self.select_output_directory).pack(fill=tk.X, pady=2)
        
        self.output_label = ttk.Label(export_frame, text="No directory selected", 
                                     wraplength=200, foreground="gray")
        self.output_label.pack(fill=tk.X, pady=2)
        
        ttk.Button(export_frame, text="Export All Crops", 
                  command=self.export_all_crops, style="Accent.TButton").pack(fill=tk.X, pady=(10, 2))
        
    def setup_pdf_viewer(self):
        """Setup the PDF viewer canvas"""
        # Create scrollable canvas
        canvas_frame = ttk.Frame(self.right_panel)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # Canvas with scrollbars
        self.canvas = tk.Canvas(canvas_frame, bg="white")
        
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid layout for canvas and scrollbars
        self.canvas.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)
        
        # Bind mouse events for cropping
        self.canvas.bind("<Button-1>", self.start_crop)
        self.canvas.bind("<B1-Motion>", self.update_crop)
        self.canvas.bind("<ButtonRelease-1>", self.finish_crop)
        
        # Variables for crop selection
        self.crop_start = None
        self.crop_rect = None
        self.cropping = False
        
    def setup_status_bar(self):
        """Setup the status bar"""
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=(0, 5))
        
        self.status_label = ttk.Label(self.status_bar, text="Ready")
        self.status_label.pack(side=tk.LEFT)
        
        self.progress_bar = ttk.Progressbar(self.status_bar, mode='indeterminate')
        # Initially hidden
        
    def setup_bindings(self):
        """Setup keyboard bindings"""
        self.root.bind("<Control-o>", lambda e: self.open_pdf())
        self.root.bind("<Control-q>", lambda e: self.root.quit())
        self.root.bind("<Control-plus>", lambda e: self.zoom_in())
        self.root.bind("<Control-minus>", lambda e: self.zoom_out())
        self.root.bind("<Control-0>", lambda e: self.reset_zoom())
        self.root.bind("<Control-w>", lambda e: self.fit_to_width())
        self.root.bind("<Left>", lambda e: self.previous_page())
        self.root.bind("<Right>", lambda e: self.next_page())
        
        # Enable drag and drop (simplified for cross-platform compatibility)
        # Note: Advanced drag-drop functionality would require tkinterdnd2
        # For now, we'll rely on file menu only
        
    def show_welcome_message(self):
        """Show welcome message when no PDF is loaded"""
        self.canvas.delete("all")
        welcome_text = "Use File → Open PDF to load a document"
        self.canvas.create_text(
            300, 200, text=welcome_text, 
            font=("Arial", 16), fill="gray", 
            justify=tk.CENTER, tags="welcome"
        )
        
    def open_pdf(self):
        """Open a PDF file"""
        file_path = filedialog.askopenfilename(
            title="Select PDF file",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        if file_path:
            self.load_pdf(file_path)
            
    def load_pdf(self, file_path):
        """Load a PDF document"""
        try:
            self.status_label.config(text="Loading PDF...")
            self.progress_bar.pack(side=tk.RIGHT, padx=(10, 0))
            self.progress_bar.start()
            
            # Load PDF in a separate thread to prevent UI freezing
            threading.Thread(target=self._load_pdf_thread, args=(file_path,), daemon=True).start()
            
        except Exception as e:
            self.progress_bar.stop()
            self.progress_bar.pack_forget()
            self.status_label.config(text="Ready")
            messagebox.showerror("Error", f"Failed to load PDF: {str(e)}")
            
    def _load_pdf_thread(self, file_path):
        """Load PDF in background thread"""
        try:
            # Open PDF document
            pdf_doc = fitz.open(file_path)
            
            # Update UI in main thread
            self.root.after(0, self._pdf_loaded_callback, pdf_doc, file_path)
            
        except Exception as e:
            self.root.after(0, self._pdf_load_error_callback, str(e))
            
    def _pdf_loaded_callback(self, pdf_doc, file_path):
        """Callback when PDF is successfully loaded"""
        self.pdf_document = pdf_doc
        self.current_page = 0
        self.pdf_images = []
        self.crop_selections = []
        
        # Update UI
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.status_label.config(text=f"Loaded: {os.path.basename(file_path)}")
        
        # Update PDF info
        self.update_pdf_info(file_path)
        
        # Render first page
        self.render_current_page()
        
        # Update navigation
        self.update_navigation()
        
    def _pdf_load_error_callback(self, error_msg):
        """Callback when PDF loading fails"""
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.status_label.config(text="Ready")
        messagebox.showerror("Error", f"Failed to load PDF: {error_msg}")
        
    def update_pdf_info(self, file_path):
        """Update the PDF information display"""
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        
        try:
            info = get_pdf_info(self.pdf_document, file_path)
            self.info_text.insert(tk.END, info)
        except Exception as e:
            self.info_text.insert(tk.END, f"Error reading PDF info: {str(e)}")
            
        self.info_text.config(state=tk.DISABLED)
        
    def render_current_page(self):
        """Render the current PDF page"""
        if not self.pdf_document:
            return
            
        try:
            page = self.pdf_document[self.current_page]
            
            # Calculate render matrix for high DPI
            matrix = fitz.Matrix(self.zoom_level * 2, self.zoom_level * 2)  # 2x for high DPI
            
            # Render page to pixmap
            pix = page.get_pixmap(matrix=matrix)
            
            # Convert to PIL Image
            img_data = pix.tobytes("ppm")
            pil_image = Image.open(io.BytesIO(img_data))
            
            # Resize for display (while keeping original for extraction)
            display_width = int(pil_image.width * self.zoom_level)
            display_height = int(pil_image.height * self.zoom_level)
            display_image = pil_image.resize((display_width, display_height), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            self.current_image = ImageTk.PhotoImage(display_image)
            
            # Store original high-res image for extraction
            self.original_image = pil_image
            self.page_dpi = 72 * 2  # Base DPI * matrix scale
            
            # Clear canvas and display image
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.current_image, tags="page")
            
            # Update scroll region
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            
            # Redraw existing crop rectangles
            self.redraw_crop_rectangles()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to render page: {str(e)}")
            
    def update_navigation(self):
        """Update navigation controls"""
        if not self.pdf_document:
            self.page_label.config(text="No PDF loaded")
            self.prev_btn.config(state=tk.DISABLED)
            self.next_btn.config(state=tk.DISABLED)
            return
            
        total_pages = len(self.pdf_document)
        self.page_label.config(text=f"Page {self.current_page + 1} of {total_pages}")
        
        self.prev_btn.config(state=tk.NORMAL if self.current_page > 0 else tk.DISABLED)
        self.next_btn.config(state=tk.NORMAL if self.current_page < total_pages - 1 else tk.DISABLED)
        
        # Update zoom label
        self.zoom_label.config(text=f"{int(self.zoom_level * 100)}%")
        
    def previous_page(self):
        """Go to previous page"""
        if self.pdf_document and self.current_page > 0:
            self.current_page -= 1
            self.render_current_page()
            self.update_navigation()
            
    def next_page(self):
        """Go to next page"""
        if self.pdf_document and self.current_page < len(self.pdf_document) - 1:
            self.current_page += 1
            self.render_current_page()
            self.update_navigation()
            
    def zoom_in(self):
        """Zoom in"""
        self.zoom_level = min(self.zoom_level * 1.25, 5.0)
        self.render_current_page()
        self.update_navigation()
        
    def zoom_out(self):
        """Zoom out"""
        self.zoom_level = max(self.zoom_level / 1.25, 0.1)
        self.render_current_page()
        self.update_navigation()
        
    def reset_zoom(self):
        """Reset zoom to 100%"""
        self.zoom_level = 1.0
        self.render_current_page()
        self.update_navigation()
        
    def fit_to_width(self):
        """Fit page to canvas width"""
        if not self.pdf_document:
            return
            
        canvas_width = self.canvas.winfo_width()
        page = self.pdf_document[self.current_page]
        page_width = page.rect.width
        
        if canvas_width > 100:  # Avoid division by very small numbers
            self.zoom_level = (canvas_width - 20) / page_width  # 20px margin
            self.render_current_page()
            self.update_navigation()
            
    def start_crop(self, event):
        """Start crop selection"""
        if not self.pdf_document:
            return
            
        # Convert canvas coordinates to image coordinates
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        self.crop_start = (canvas_x, canvas_y)
        self.cropping = True
        
        # Delete any existing crop rectangle
        self.canvas.delete("crop_rect")
        
    def update_crop(self, event):
        """Update crop selection rectangle"""
        if not self.cropping or not self.crop_start:
            return
            
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Delete previous rectangle
        self.canvas.delete("crop_rect")
        
        # Draw new rectangle
        self.crop_rect = self.canvas.create_rectangle(
            self.crop_start[0], self.crop_start[1], canvas_x, canvas_y,
            outline="red", width=2, tags="crop_rect"
        )
        
    def finish_crop(self, event):
        """Finish crop selection"""
        if not self.cropping or not self.crop_start:
            return
            
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Calculate crop rectangle
        x1, y1 = self.crop_start
        x2, y2 = canvas_x, canvas_y
        
        # Ensure valid rectangle
        if abs(x2 - x1) > 10 and abs(y2 - y1) > 10:
            # Normalize coordinates
            left = min(x1, x2)
            top = min(y1, y2)
            right = max(x1, x2)
            bottom = max(y1, y2)
            
            # Add to crop selections
            crop_data = {
                'page': self.current_page,
                'coords': (left, top, right, bottom),
                'zoom': self.zoom_level
            }
            self.crop_selections.append(crop_data)
            
            # Update crop list
            self.crop_frame.update_crop_list(self.crop_selections)
            
        self.cropping = False
        self.crop_start = None
        
    def redraw_crop_rectangles(self):
        """Redraw all crop rectangles for current page"""
        self.canvas.delete("saved_crop")
        
        for i, crop in enumerate(self.crop_selections):
            if crop['page'] == self.current_page:
                coords = crop['coords']
                rect = self.canvas.create_rectangle(
                    coords[0], coords[1], coords[2], coords[3],
                    outline="blue", width=2, tags="saved_crop"
                )
                
                # Add crop number label
                center_x = (coords[0] + coords[2]) / 2
                center_y = coords[1] + 15
                self.canvas.create_text(
                    center_x, center_y, text=f"#{i+1}",
                    fill="blue", font=("Arial", 10, "bold"), tags="saved_crop"
                )
                
    def select_output_directory(self):
        """Select output directory for exported images"""
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_directory = directory
            self.output_label.config(
                text=f"Output: {os.path.basename(directory)}", 
                foreground="black"
            )
            
    def clear_all_crops(self):
        """Clear all crop selections"""
        if self.crop_selections:
            result = messagebox.askyesno("Confirm", "Clear all crop selections?")
            if result:
                self.crop_selections = []
                self.crop_frame.update_crop_list([])
                self.redraw_crop_rectangles()
                
    def export_all_crops(self):
        """Export all crop selections"""
        if not self.crop_selections:
            messagebox.showwarning("No Crops", "No crop selections to export")
            return
            
        if not self.output_directory:
            messagebox.showwarning("No Directory", "Please select an output directory first")
            return
            
        try:
            extractor = ImageExtractor(self.pdf_document)
            
            self.status_label.config(text="Exporting crops...")
            self.progress_bar.pack(side=tk.RIGHT, padx=(10, 0))
            self.progress_bar.start()
            
            # Export in background thread
            threading.Thread(
                target=self._export_crops_thread, 
                args=(extractor,), 
                daemon=True
            ).start()
            
        except Exception as e:
            self.progress_bar.stop()
            self.progress_bar.pack_forget()
            self.status_label.config(text="Ready")
            messagebox.showerror("Export Error", f"Failed to export crops: {str(e)}")
            
    def _export_crops_thread(self, extractor):
        """Export crops in background thread"""
        try:
            exported_count = 0
            
            for i, crop in enumerate(self.crop_selections):
                # Generate filename
                filename = self.naming_pattern.format(i + 1)
                if not filename.endswith('.png'):
                    filename += '.png'
                    
                output_path = os.path.join(self.output_directory, filename)
                
                # Extract and save crop
                success = extractor.extract_crop(crop, output_path)
                if success:
                    exported_count += 1
                    
            # Update UI in main thread
            self.root.after(0, self._export_complete_callback, exported_count, len(self.crop_selections))
            
        except Exception as e:
            self.root.after(0, self._export_error_callback, str(e))
            
    def _export_complete_callback(self, exported_count, total_count):
        """Callback when export is complete"""
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.status_label.config(text="Ready")
        
        if exported_count == total_count:
            messagebox.showinfo("Export Complete", 
                               f"Successfully exported {exported_count} images to:\n{self.output_directory}")
        else:
            messagebox.showwarning("Export Partial", 
                                 f"Exported {exported_count} of {total_count} images.\n"
                                 f"Some exports may have failed.")
            
    def _export_error_callback(self, error_msg):
        """Callback when export fails"""
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.status_label.config(text="Ready")
        messagebox.showerror("Export Error", f"Export failed: {error_msg}")
        
    def update_naming_pattern(self, pattern):
        """Update the naming pattern for exported files"""
        self.naming_pattern = pattern
        
    def remove_crop(self, index):
        """Remove a specific crop selection"""
        if 0 <= index < len(self.crop_selections):
            self.crop_selections.pop(index)
            self.crop_frame.update_crop_list(self.crop_selections)
            self.redraw_crop_rectangles()
