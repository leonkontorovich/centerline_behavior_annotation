import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import yaml
from pathlib import Path
import threading
import queue

class ConfigUpdaterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Config Updater")
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
        ttk.Label(input_frame, text="Source Folder (with odor_pos.config):").grid(row=0, column=0, sticky="w", padx=5)
        self.path_entry = ttk.Entry(input_frame, textvariable=self.src_path)
        self.path_entry.grid(row=0, column=1, sticky="ew", padx=5)
        self.browse_btn = ttk.Button(input_frame, text="Browse", command=self.browse_folder)
        self.browse_btn.grid(row=0, column=2, padx=5)
        
        # Process button
        self.process_btn = ttk.Button(
            self.root, 
            text="Update Config Files", 
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
        folder_path = filedialog.askdirectory(title="Select Source Folder containing odor_pos.config")
        if folder_path:
            self.src_path.set(folder_path)

    def start_processing(self):
        if self.processing:
            return
            
        if not self.src_path.get():
            messagebox.showerror("Error", "Please select a source folder first!")
            return
            
        src_path = Path(self.src_path.get())
        config_file = src_path / 'odor_pos.config'
        
        if not config_file.exists():
            messagebox.showerror("Error", "odor_pos.config not found in selected folder!")
            return
        
        # Clear previous progress
        self.progress_text.delete(1.0, tk.END)
        self.processed_folders = 0
        
        # Load coordinates
        try:
            with open(config_file, 'r') as f:
                self.coordinates = yaml.safe_load(f)
            self.total_folders = len(self.coordinates)
            
            if self.total_folders == 0:
                messagebox.showwarning("Warning", "No coordinates found in odor_pos.config!")
                return
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load odor_pos.config: {str(e)}")
            return
            
        self.progress_bar['value'] = 0
        self.processing = True
        self.process_btn.configure(state="disabled")
        self.browse_btn.configure(state="disabled")
        
        # Start processing in a separate thread
        thread = threading.Thread(target=self.update_configs)
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

    def update_configs(self):
        src_path = Path(self.src_path.get())
        success_count = 0
        
        try:
            for folder_name, coords in self.coordinates.items():
                folder_path = src_path / folder_name
                config_file = folder_path / 'config.yaml'
                
                try:
                    if folder_path.exists() and config_file.exists():
                        # Read the config file as text to preserve format
                        with open(config_file, 'r') as f:
                            config_lines = f.readlines()
                        
                        # Create new coordinate line
                        new_coord_line = f"odor_pos: x={coords['x']}, y={coords['y']}\n"
                        
                        # Find and replace the odor_pos line
                        found = False
                        for i, line in enumerate(config_lines):
                            if line.strip().startswith('odor_pos:'):
                                config_lines[i] = new_coord_line
                                found = True
                                break
                        
                        # If odor_pos line wasn't found, append it
                        if not found:
                            config_lines.append(new_coord_line)
                        
                        # Write back the updated config
                        with open(config_file, 'w') as f:
                            f.writelines(config_lines)
                        
                        success_count += 1
                        self.queue.put(f"Updated config in: {folder_name}")
                        self.queue.put(f"  Set: {new_coord_line.strip()}")
                    else:
                        self.queue.put(f"Folder or config not found: {folder_name}")
                
                except Exception as e:
                    self.queue.put(f"Error updating {folder_name}: {str(e)}")
                
                # Update progress
                self.processed_folders += 1
                self.progress_bar['value'] = (self.processed_folders / self.total_folders) * 100
            
            self.queue.put(f"\nFinished updating configs")
            self.queue.put(f"Successfully updated {success_count} out of {self.total_folders} configs")
            
        except Exception as e:
            self.queue.put(f"Error: {str(e)}")
        
        finally:
            # Re-enable buttons
            self.root.after(0, lambda: self.process_btn.configure(state="normal"))
            self.root.after(0, lambda: self.browse_btn.configure(state="normal"))
            self.processing = False

def main():
    root = tk.Tk()
    app = ConfigUpdaterGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()