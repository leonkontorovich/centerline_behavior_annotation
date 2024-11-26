import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import yaml
from pathlib import Path
import threading
import queue
import re

class CoordinateCollectorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Coordinate Collector")
        self.root.geometry("600x400")
        
        # Initialize variables
        self.queue = queue.Queue()
        self.processing = False
        self.total_folders = 0
        self.processed_folders = 0
        
        # Configure grid
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(2, weight=1)
        
        # Create widgets
        self.create_widgets()
        
        # Start queue checking
        self.check_queue()

    def create_widgets(self):
        # Frame for input
        input_frame = ttk.Frame(self.root, padding="10")
        input_frame.grid(row=0, column=0, sticky="ew")
        input_frame.grid_columnconfigure(1, weight=1)
        
        # Source folder selection
        self.src_path = tk.StringVar()
        ttk.Label(input_frame, text="Source Folder:").grid(row=0, column=0, sticky="w", padx=5)
        self.path_entry = ttk.Entry(input_frame, textvariable=self.src_path)
        self.path_entry.grid(row=0, column=1, sticky="ew", padx=5)
        self.browse_btn = ttk.Button(input_frame, text="Browse", command=self.browse_folder)
        self.browse_btn.grid(row=0, column=2, padx=5)
        
        # Process button
        self.process_btn = ttk.Button(
            self.root, 
            text="Process Folder", 
            command=self.start_processing,
            padding=10
        )
        self.process_btn.grid(row=1, column=0, pady=10, padx=10, sticky="ew")
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(self.root, length=100, mode='determinate')
        self.progress_bar.grid(row=2, column=0, pady=5, padx=10, sticky="ew")
        
        # Progress text
        self.progress_text = tk.Text(self.root, wrap=tk.WORD, height=15)
        self.progress_text.grid(row=3, column=0, pady=5, padx=10, sticky="nsew")
        
        # Scrollbar for progress text
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.progress_text.yview)
        scrollbar.grid(row=3, column=1, sticky="ns")
        self.progress_text.configure(yscrollcommand=scrollbar.set)

    def browse_folder(self):
        folder_path = filedialog.askdirectory(title="Select Source Folder")
        if folder_path:
            self.src_path.set(folder_path)

    def start_processing(self):
        if self.processing:
            return
            
        if not self.src_path.get():
            messagebox.showerror("Error", "Please select a source folder first!")
            return
            
        src_path = Path(self.src_path.get())
        if not src_path.exists():
            messagebox.showerror("Error", "Selected folder does not exist!")
            return
        
        # Clear previous progress
        self.progress_text.delete(1.0, tk.END)
        self.processed_folders = 0
        
        # Get subfolders and count them for progress
        self.subfolders = [f for f in src_path.iterdir() if f.is_dir()]
        self.total_folders = len(self.subfolders)
        
        if self.total_folders == 0:
            messagebox.showwarning("Warning", "No subfolders found in the selected directory!")
            return
            
        self.progress_bar['value'] = 0
        self.processing = True
        self.process_btn.configure(state="disabled")
        self.browse_btn.configure(state="disabled")
        
        # Start processing in a separate thread
        thread = threading.Thread(target=self.collect_coordinates)
        thread.daemon = True
        thread.start()

    def update_progress(self, message):
        self.progress_text.insert(tk.END, message + "\n")
        self.progress_text.see(tk.END)

    def check_queue(self):
        try:
            while True:
                message = self.queue.get_nowait()
                self.update_progress(message)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.check_queue)

    def extract_coordinates(self, coord_string):
        """Extract coordinates from string format 'x=value, y=value'"""
        try:
            # Use regex to extract x and y values
            pattern = r'x=(\d+),\s*y=(\d+)'
            match = re.match(pattern, coord_string)
            if match:
                x = int(match.group(1))
                y = int(match.group(2))
                return x, y
            return None
        except (ValueError, AttributeError):
            return None

    def collect_coordinates(self):
        src_path = Path(self.src_path.get())
        all_configs = {}
        
        try:
            # Process each subfolder
            for subfolder in self.subfolders:
                config_file = subfolder / 'config.yaml'
                
                try:
                    if config_file.exists():
                        with open(config_file, 'r') as f:
                            config_data = yaml.safe_load(f)
                        
                        if 'odor_pos' in config_data:
                            coords = self.extract_coordinates(config_data['odor_pos'])
                            if coords:
                                x, y = coords
                                all_configs[subfolder.name] = {
                                    'x': x,
                                    'y': y
                                }
                                self.queue.put(f"Found odor position in: {subfolder.name}")
                                self.queue.put(f"  x: {x}, y: {y}")
                            else:
                                self.queue.put(f"Invalid coordinate format in: {subfolder.name}")
                        else:
                            self.queue.put(f"No odor position found in: {subfolder.name}")
                    else:
                        self.queue.put(f"No config.yaml found in: {subfolder.name}")
                
                except Exception as e:
                    self.queue.put(f"Error processing {subfolder.name}: {str(e)}")
                
                # Update progress
                self.processed_folders += 1
                self.progress_bar['value'] = (self.processed_folders / self.total_folders) * 100
            
            if all_configs:
                # Save coordinates to odor_pos.config
                output_file = src_path / 'odor_pos.config'
                with open(output_file, 'w') as f:
                    yaml.dump(all_configs, f, default_flow_style=False, sort_keys=False)
                
                self.queue.put(f"\nSuccessfully saved coordinates to {output_file}")
                self.queue.put(f"Processed {len(all_configs)} folders with valid coordinates")
            else:
                self.queue.put("\nNo valid coordinates found in any config files!")
            
        except Exception as e:
            self.queue.put(f"Error: {str(e)}")
        
        finally:
            # Re-enable buttons
            self.root.after(0, lambda: self.process_btn.configure(state="normal"))
            self.root.after(0, lambda: self.browse_btn.configure(state="normal"))
            self.processing = False

def main():
    root = tk.Tk()
    app = CoordinateCollectorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()