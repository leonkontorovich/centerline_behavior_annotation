import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

def delete_output_folders(root, src_folder_path, dry_run, progress_var):
    folders_to_delete = []
    
    # Walk the directory only up to three levels deep
    for root_dir, dirs, files in os.walk(src_folder_path):
        # Calculate depth by counting folder separators
        relative_depth = os.path.relpath(root_dir, src_folder_path).count(os.sep)
        if relative_depth > 2:
            continue  # Skip if depth exceeds 2

        for dir_name in dirs:
            if dir_name == "output":
                folder_path = os.path.join(root_dir, dir_name)
                folders_to_delete.append(folder_path)
                print(f"Found 'output' folder at: {folder_path}")

    total_folders = len(folders_to_delete)
    deleted_folders = []

    # Process each folder with a progress update
    for idx, folder_path in enumerate(folders_to_delete, 1):
        print(f"{'Dry run:' if dry_run else 'Deleting:'} {folder_path}")
        deleted_folders.append(folder_path)
        
        if not dry_run:
            shutil.rmtree(folder_path)
            print(f"Deleted: {folder_path}")
        
        # Update progress bar
        progress_var.set(int((idx / total_folders) * 100))  
        root.update_idletasks()  # Refresh GUI

    print("Operation completed.")
    return deleted_folders

def browse_folder():
    folder_selected = filedialog.askdirectory()
    src_folder_var.set(folder_selected)

def perform_deletion():
    src_folder_path = src_folder_var.get()
    dry_run = dry_run_var.get()

    if not os.path.isdir(src_folder_path):
        messagebox.showerror("Error", "Invalid source folder path.")
        return

    print(f"Starting deletion in: {src_folder_path}")
    print(f"Dry run mode: {'Enabled' if dry_run else 'Disabled'}")

    # Reset progress bar and delete folders
    progress_var.set(0)
    deleted_folders = delete_output_folders(root, src_folder_path, dry_run, progress_var)
    
    # Show results only in the console for dry run
    if dry_run:
        print("\nDry Run - Folders that would be deleted:")
        for folder in deleted_folders:
            print(folder)
    else:
        if deleted_folders:
            message = "Deleted the following folders:\n\n" + "\n".join(deleted_folders)
        else:
            message = "No folders named 'output' found."
        messagebox.showinfo("Results", message)

# Set up GUI
root = tk.Tk()
root.title("Delete 'output' Folders")

# Folder path input
src_folder_var = tk.StringVar()
tk.Label(root, text="Source Folder Path:").pack(padx=10, pady=5)
tk.Entry(root, textvariable=src_folder_var, width=50).pack(padx=10, pady=5)
tk.Button(root, text="Browse", command=browse_folder).pack(pady=5)

# Dry Run option
dry_run_var = tk.BooleanVar(value=True)
tk.Checkbutton(root, text="Dry Run (Preview only)", variable=dry_run_var).pack(pady=5)

# Progress bar
progress_var = tk.IntVar()
progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100, length=300)
progress_bar.pack(pady=10)

# Delete button
tk.Button(root, text="Delete 'output' Folders", command=perform_deletion).pack(pady=10)

root.mainloop()
