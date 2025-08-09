"""
UI Components - Reusable UI components for the PDF viewer
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os

class CropFrame(ttk.LabelFrame):
    """Frame for managing crop selections"""
    
    def __init__(self, parent, app):
        super().__init__(parent, text="Crop Selections", padding=10)
        self.app = app
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the crop management interface"""
        # Crop list
        list_frame = ttk.Frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollable listbox for crops
        self.crop_listbox = tk.Listbox(list_frame, height=6, selectmode=tk.SINGLE)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.crop_listbox.yview)
        self.crop_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.crop_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Crop management buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # First row of buttons
        top_button_frame = ttk.Frame(button_frame)
        top_button_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.remove_btn = ttk.Button(top_button_frame, text="Remove Selected", 
                                    command=self.remove_selected_crop, state=tk.DISABLED)
        self.remove_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(top_button_frame, text="Clear All", 
                  command=self.clear_all_crops).pack(side=tk.RIGHT)
        
        # Second row of buttons
        bottom_button_frame = ttk.Frame(button_frame)
        bottom_button_frame.pack(fill=tk.X)
        
        self.save_individual_btn = ttk.Button(bottom_button_frame, text="Save Individual", 
                                            command=self.save_selected_crop, state=tk.DISABLED)
        self.save_individual_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Bind selection events
        self.crop_listbox.bind('<<ListboxSelect>>', self.on_selection_change)
        
    def update_crop_list(self, crop_selections):
        """Update the crop list display"""
        self.crop_listbox.delete(0, tk.END)
        
        for i, crop in enumerate(crop_selections):
            page_num = crop['page'] + 1  # 1-based for display
            coords = crop['coords']
            width = int(coords[2] - coords[0])
            height = int(coords[3] - coords[1])
            
            item_text = f"#{i+1}: Page {page_num} ({width}×{height})"
            self.crop_listbox.insert(tk.END, item_text)
            
        # Update button states
        self.remove_btn.config(state=tk.DISABLED)
        self.save_individual_btn.config(state=tk.DISABLED)
        
    def on_selection_change(self, event):
        """Handle crop selection changes"""
        selection = self.crop_listbox.curselection()
        if selection:
            self.remove_btn.config(state=tk.NORMAL)
            self.save_individual_btn.config(state=tk.NORMAL)
            
            # Navigate to the page containing the selected crop
            crop_index = selection[0]
            if crop_index < len(self.app.crop_selections):
                crop_page = self.app.crop_selections[crop_index]['page']
                if crop_page != self.app.current_page:
                    self.app.current_page = crop_page
                    self.app.render_current_page()
                    self.app.update_navigation()
        else:
            self.remove_btn.config(state=tk.DISABLED)
            self.save_individual_btn.config(state=tk.DISABLED)
            
    def remove_selected_crop(self):
        """Remove the currently selected crop"""
        selection = self.crop_listbox.curselection()
        if selection:
            crop_index = selection[0]
            if crop_index < len(self.app.crop_selections):
                self.app.remove_crop(crop_index)
                
    def clear_all_crops(self):
        """Clear all crop selections"""
        self.app.clear_all_crops()
        
    def save_selected_crop(self):
        """Save the currently selected individual crop"""
        selection = self.crop_listbox.curselection()
        if selection:
            crop_index = selection[0]
            if crop_index < len(self.app.crop_selections):
                self.app.save_individual_crop(crop_index)

class NamingFrame(ttk.LabelFrame):
    """Frame for configuring file naming patterns"""
    
    def __init__(self, parent, app):
        super().__init__(parent, text="File Naming", padding=10)
        self.app = app
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the naming configuration interface"""
        # Pattern input
        ttk.Label(self, text="Naming Pattern:").pack(anchor=tk.W)
        
        self.pattern_var = tk.StringVar(value="figure_{:03d}")
        self.pattern_entry = ttk.Entry(self, textvariable=self.pattern_var, width=20)
        self.pattern_entry.pack(fill=tk.X, pady=(2, 5))
        
        # Bind pattern changes
        self.pattern_var.trace('w', self.on_pattern_change)
        
        # Preview
        ttk.Label(self, text="Preview:").pack(anchor=tk.W)
        self.preview_label = ttk.Label(self, text="figure_001.png, figure_002.png, ...", 
                                      foreground="gray", wraplength=200)
        self.preview_label.pack(fill=tk.X, pady=(2, 5))
        
        # Preset buttons
        preset_frame = ttk.Frame(self)
        preset_frame.pack(fill=tk.X, pady=(5, 0))
        
        presets = [
            ("Fig {}", "fig_{:d}"),
            ("Image 001", "image_{:03d}"),
            ("Crop_01", "crop_{:02d}")
        ]
        
        for i, (label, pattern) in enumerate(presets):
            ttk.Button(preset_frame, text=label, width=8,
                      command=lambda p=pattern: self.set_pattern(p)).pack(side=tk.LEFT, padx=1)
        
        # Help text
        help_text = ("Use {:d} for numbers, {:03d} for zero-padded numbers.\n"
                    "Example: 'figure_{:03d}' → figure_001.png")
        ttk.Label(self, text=help_text, font=("Arial", 8), 
                 foreground="gray", wraplength=200, justify=tk.LEFT).pack(pady=(10, 0))
        
    def on_pattern_change(self, *args):
        """Handle pattern changes"""
        pattern = self.pattern_var.get()
        
        # Update app naming pattern
        self.app.update_naming_pattern(pattern)
        
        # Update preview
        self.update_preview(pattern)
        
    def update_preview(self, pattern):
        """Update the naming preview"""
        try:
            # Generate preview with sample numbers
            samples = []
            for i in range(1, 4):
                try:
                    filename = pattern.format(i)
                    if not filename.endswith('.png'):
                        filename += '.png'
                    samples.append(filename)
                except:
                    samples.append("(invalid pattern)")
                    break
                    
            if len(samples) == 3 and "(invalid pattern)" not in samples:
                preview = f"{samples[0]}, {samples[1]}, ..."
            else:
                preview = samples[0] if samples else "(invalid pattern)"
                
            self.preview_label.config(text=preview, foreground="gray" if "(invalid" not in preview else "red")
            
        except Exception:
            self.preview_label.config(text="(invalid pattern)", foreground="red")
            
    def set_pattern(self, pattern):
        """Set a preset naming pattern"""
        self.pattern_var.set(pattern)

class ControlFrame(ttk.Frame):
    """Frame for general application controls"""
    
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the control interface"""
        # Quality settings
        quality_frame = ttk.LabelFrame(self, text="Export Quality", padding=10)
        quality_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.dpi_var = tk.StringVar(value="300")
        
        ttk.Label(quality_frame, text="Target DPI:").pack(anchor=tk.W)
        
        dpi_frame = ttk.Frame(quality_frame)
        dpi_frame.pack(fill=tk.X, pady=2)
        
        dpi_values = ["150", "300", "600", "Auto"]
        for dpi in dpi_values:
            ttk.Radiobutton(dpi_frame, text=dpi, value=dpi, 
                           variable=self.dpi_var).pack(side=tk.LEFT, padx=(0, 10))
        
        # Keyboard shortcuts help
        help_frame = ttk.LabelFrame(self, text="Keyboard Shortcuts", padding=10)
        help_frame.pack(fill=tk.BOTH, expand=True)
        
        shortcuts = [
            "Ctrl+O: Open PDF",
            "Ctrl+W: Fit to width",
            "Ctrl+Plus: Zoom in",
            "Ctrl+Minus: Zoom out",
            "←/→: Navigate pages",
            "Click+Drag: Select crop area"
        ]
        
        for shortcut in shortcuts:
            ttk.Label(help_frame, text=shortcut, font=("Arial", 9)).pack(anchor=tk.W, pady=1)

class StatusBar(ttk.Frame):
    """Status bar component"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the status bar"""
        self.status_label = ttk.Label(self, text="Ready")
        self.status_label.pack(side=tk.LEFT)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self, variable=self.progress_var, length=200)
        # Initially hidden
        
    def set_status(self, text):
        """Set status text"""
        self.status_label.config(text=text)
        
    def show_progress(self, show=True):
        """Show or hide progress bar"""
        if show:
            self.progress_bar.pack(side=tk.RIGHT, padx=(10, 0))
        else:
            self.progress_bar.pack_forget()
            
    def set_progress(self, value):
        """Set progress bar value (0-100)"""
        self.progress_var.set(value)
        
    def start_indeterminate(self):
        """Start indeterminate progress"""
        self.progress_bar.config(mode='indeterminate')
        self.progress_bar.start()
        
    def stop_indeterminate(self):
        """Stop indeterminate progress"""
        self.progress_bar.stop()
        self.progress_bar.config(mode='determinate')
