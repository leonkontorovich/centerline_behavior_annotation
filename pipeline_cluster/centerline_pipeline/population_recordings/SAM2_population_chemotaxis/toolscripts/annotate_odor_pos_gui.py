import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, UnidentifiedImageError
import imageio.v3 as iio
import tifffile
import matplotlib.pyplot as plt
from matplotlib.backend_bases import MouseButton
import yaml

class ImagePointDetector:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Point Detector")
        self.folder_path = ""
        self.image_paths = []
        self.current_image_index = 0
        self.points = {}
        
        # Selected point type (top_left or odor_pos)
        self.selected_point_type = tk.StringVar(value="top_left")
        
        # GUI Elements
        self.create_widgets()
        
    def create_widgets(self):
        tk.Label(self.root, text="Source Folder:").grid(row=0, column=0, sticky="w")
        self.path_entry = tk.Entry(self.root, width=40)
        self.path_entry.grid(row=0, column=1)
        tk.Button(self.root, text="Browse", command=self.select_folder).grid(row=0, column=2)
        
        tk.Button(self.root, text="Search", command=self.search_images).grid(row=1, column=0, columnspan=3)
        
        self.detect_button = tk.Button(self.root, text="Detect Points", command=self.confirm_detect_points)
        self.detect_button.grid(row=2, column=0, columnspan=3)
        
        tk.Label(self.root, text="Select Point Type:").grid(row=3, column=0, sticky="w")
        self.point_menu = tk.OptionMenu(self.root, self.selected_point_type, "top_left", "odor_pos")
        self.point_menu.grid(row=3, column=1)
        
        self.result_label = tk.Label(self.root, text="")
        self.result_label.grid(row=4, column=0, columnspan=3)
        self.prev_image_button = tk.Button(self.root, text="Previous Image", command=self.previous_image, state="disabled")
        self.prev_image_button.grid(row=5, column=0)
        self.next_image_button = tk.Button(self.root, text="Next Image", command=self.next_image, state="disabled")
        self.next_image_button.grid(row=5, column=2)

    def select_folder(self):
        self.folder_path = filedialog.askdirectory()
        self.path_entry.delete(0, tk.END)
        self.path_entry.insert(0, self.folder_path)
    
    def search_images(self):
        self.image_paths = []
        print(f"Starting search in folder: {self.folder_path}")
        
        try:
            for subfolder in os.listdir(self.folder_path):
                subfolder_path = os.path.join(self.folder_path, subfolder)
                if not os.path.isdir(subfolder_path):
                    continue
                    
                # Get subsubfolders
                for subsubfolder in os.listdir(subfolder_path):
                    subsubfolder_path = os.path.join(subfolder_path, subsubfolder)
                    if not os.path.isdir(subsubfolder_path):
                        continue
                        
                    # Look for avg_background.tif only in this level
                    target_file = os.path.join(subsubfolder_path, "avg_background.tif")
                    if os.path.isfile(target_file):
                        self.image_paths.append(target_file)
                        print(f"Found image in {subfolder}: {target_file}")
                        
        except Exception as e:
            print(f"Error during search: {e}")
            messagebox.showerror("Error", f"Error during search: {e}")
            return
        
        print(f"Search finished. Total occurrences found: {len(self.image_paths)}")
        self.result_label.config(text=f"Found {len(self.image_paths)} occurrences.")
    
    def confirm_detect_points(self):
        if not self.detect_button["state"] == "disabled":
            confirm = messagebox.askyesno("Confirm Restart", "You have already started point detection. Restarting will lose all current progress. Do you want to continue?")
            if not confirm:
                return

        self.detect_button.config(state="disabled")
        self.detect_points()

    def detect_points(self):
        if not self.image_paths:
            messagebox.showerror("Error", "No images found. Please search again.")
            return

        self.current_image_index = 0
        self.points = {}
        self.show_image()
    
    def load_image_stack(self, image_path):
        try:
            pil_image = Image.open(image_path)
            frames = []
            while True:
                frames.append(pil_image.convert("L"))
                pil_image.seek(pil_image.tell() + 1)
        except (EOFError, UnidentifiedImageError):
            frames = []  # Reset frames if PIL failed

        if frames:
            print(f"Loaded {len(frames)} frames with PIL.")
            return frames

        try:
            frames = iio.imread(image_path)
            if len(frames.shape) > 2:  # If we have a stack
                return [frames[i] for i in range(frames.shape[0])]
            else:  # If we have a single image
                return [frames]
        except Exception as e:
            print(f"imageio failed: {e}")

        try:
            with tifffile.TiffFile(image_path) as tif:
                frames = [page.asarray() for page in tif.pages]
                print(f"Loaded {len(frames)} frames with tifffile.")
                return frames
        except Exception as e:
            print(f"tifffile failed: {e}")

        print(f"Failed to load {image_path} with all methods.")
        return None

    def get_subfolder_info(self, image_path):
        """Extract source folder and subfolder names from image path."""
        parts = image_path.split(os.sep)
        try:
            # Find the index where the source folder is
            src_index = parts.index(os.path.basename(self.folder_path))
            if src_index + 1 < len(parts):
                subfolder = parts[src_index + 1]
                return subfolder
        except ValueError:
            pass
        return "Unknown"

    def load_yaml_config(self, folder_path):
        """Load coordinates from config.yaml file at the correct folder level."""
        yaml_folder = os.path.dirname(folder_path)
        config_path = os.path.join(yaml_folder, "config.yaml")

        if not os.path.exists(config_path):
            yaml_folder = os.path.dirname(yaml_folder)
            config_path = os.path.join(yaml_folder, "config.yaml")

        subfolder = os.path.basename(yaml_folder)

        print(f"\nLoading coordinates for subfolder: {subfolder}")
        print(f"YAML path: {config_path}")

        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as file:
                    config = yaml.safe_load(file)

                coordinates = {}
                if 'top_left' in config:
                    top_left_str = config['top_left'].replace('"', '')
                    x = int(top_left_str.split('x=')[1].split(',')[0].strip())
                    y = int(top_left_str.split('y=')[1].strip())
                    coordinates['top_left'] = (x, y)
                    print(f"Loaded top_left coordinate: ({x}, {y})")

                if 'odor_pos' in config:
                    odor_pos_str = config['odor_pos'].replace('"', '')
                    x = int(odor_pos_str.split('x=')[1].split(',')[0].strip())
                    y = int(odor_pos_str.split('y=')[1].strip())
                    coordinates['odor_pos'] = (x, y)
                    print(f"Loaded odor_pos coordinate: ({x}, {y})")

                return config, coordinates
            except Exception as e:
                print(f"Error loading config: {e}")
                return None, {}

        print(f"No config file found at: {config_path}")
        return None, {}

    def save_to_yaml(self, folder_path, coords):
        """Save coordinates to config.yaml, checking folder levels."""
        yaml_folder = os.path.dirname(folder_path)
        config_path = os.path.join(yaml_folder, "config.yaml")

        if not os.path.exists(config_path):
            yaml_folder = os.path.dirname(yaml_folder)
            config_path = os.path.join(yaml_folder, "config.yaml")

        print(f"\nSaving coordinates for subfolder: {os.path.basename(yaml_folder)}")
        print(f"YAML path: {config_path}")

        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as file:
                    config = yaml.safe_load(file) or {}
            else:
                config = {'# Arena details in px': '-> get from background tif'}

            if 'top_left' in coords:
                x, y = coords['top_left']
                config['top_left'] = f"x={x}, y={y}"
                print(f"Saving top_left coordinate: ({x}, {y})")

            if 'odor_pos' in coords:
                x, y = coords['odor_pos']
                config['odor_pos'] = f"x={x}, y={y}"
                print(f"Saving odor_pos coordinate: ({x}, {y})")

            with open(config_path, 'w') as file:
                yaml.dump(config, file, default_flow_style=False, sort_keys=False, allow_unicode=True)

            print(f"Coordinates saved successfully in config.yaml")
        except Exception as e:
            print(f"Error saving config: {e}")

    def show_image(self):
        image_path = self.image_paths[self.current_image_index]
        frames = self.load_image_stack(image_path)
        
        if frames is None:
            print(f"Error: Cannot identify image file {image_path}. Skipping.")
            return

        subfolder = self.get_subfolder_info(image_path)
        folder = os.path.dirname(image_path)
        config, coordinates = self.load_yaml_config(folder)
        if coordinates:
            self.points[image_path] = coordinates
        
        self.image = frames[0]
        self.fig, self.ax = plt.subplots()
        self.ax.imshow(self.image, cmap='gray')
        self.cid = self.fig.canvas.mpl_connect('button_press_event', self.onclick)

        if image_path in self.points:
            if "top_left" in self.points[image_path]:
                x, y = self.points[image_path]["top_left"]
                self.ax.plot(x, y, 'ro', label="top_left")
            if "odor_pos" in self.points[image_path]:
                x, y = self.points[image_path]["odor_pos"]
                self.ax.plot(x, y, 'bo', label="odor_pos")

        plt.title(f"Subfolder: {subfolder}\nImage {self.current_image_index + 1} / {len(self.image_paths)}")
        plt.show()

        self.prev_image_button.config(state="normal" if self.current_image_index > 0 else "disabled")
        self.next_image_button.config(state="normal" if self.current_image_index < len(self.image_paths) - 1 else "disabled")

    def onclick(self, event):
        if event.button == MouseButton.LEFT and event.xdata is not None and event.ydata is not None:
            x, y = int(event.xdata), int(event.ydata)
            point_type = self.selected_point_type.get()
            
            color = 'ro' if point_type == "top_left" else 'bo'
            self.ax.plot(x, y, color)
            plt.draw()

            image_path = self.image_paths[self.current_image_index]
            if image_path not in self.points:
                self.points[image_path] = {}
            self.points[image_path][point_type] = (x, y)
    
    def next_image(self):
        image_path = self.image_paths[self.current_image_index]
        if image_path in self.points:
            folder = os.path.dirname(image_path)
            self.save_to_yaml(folder, self.points[image_path])

        self.fig.canvas.mpl_disconnect(self.cid)
        plt.close(self.fig)
        self.current_image_index += 1
        self.show_image()

    def previous_image(self):
        image_path = self.image_paths[self.current_image_index]
        if image_path in self.points:
            folder = os.path.dirname(image_path)
            self.save_to_yaml(folder, self.points[image_path])
            
        self.fig.canvas.mpl_disconnect(self.cid)
        plt.close(self.fig)
        self.current_image_index -= 1
        self.show_image()

if __name__ == "__main__":
    root = tk.Tk()
    app = ImagePointDetector(root)
    root.mainloop()
