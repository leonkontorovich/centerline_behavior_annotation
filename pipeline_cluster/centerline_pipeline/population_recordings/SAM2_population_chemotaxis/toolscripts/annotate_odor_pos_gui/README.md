# Annotate Odor Position (quick setup)

A tiny desktop helper to click reference points on image stacks and save them to a `dataset_coordinates.yaml` file per dataset.

> **What it does:** You select a root folder, the app scans subfolders for images/stacks (`.tif/.tiff`, GIFs, and common formats), lets you mark `top_left` and `odor_pos` by clicking, and writes those coordinates to YAML.

---

## Quick start — copy/paste

```bash
# 1) Create a fresh conda environment (small + reproducible)
conda create -n chemotaxis_env -y -c conda-forge python=3.11 pillow imageio tifffile matplotlib pyyaml tk

# 2) Activate it
conda activate chemotaxis_env

# 3) Run the app
python annotate_odor_pos_gui.py
```

---

## What those steps mean (super short)

- **Conda environment** = a self‑contained folder with its own Python + libraries. Keeps this tool isolated so versions don’t clash.
- **Create → Activate** = make it once, then switch into it when you want to use the app.
- **Packages**: `pillow`/`imageio`/`tifffile` read images; `matplotlib` shows images + records clicks; `pyyaml` writes YAML; `tk` provides the simple desktop window.

---

## Using the app

1. Start it: `python annotate_odor_pos_gui.py`
2. Pick a **root folder** (the app scans its subfolders for images).
3. Click **Search**.
4. Choose **point type** (`top_left` or `odor_pos`) and click on the image.
5. Navigate **Next/Previous Image** as needed. Coordinates save on image change or when closing the figure.
6. A **`dataset_coordinates.yaml`** file is written inside each dataset folder.

### Example YAML
```yaml
some_dataset_folder:
  top_left_x: 123
  top_left_y: 45
  odor_x: 400
  odor_y: 320
```

---

## Done with it?

```bash
# Leave the environment
conda deactivate
```

> Keep `chemotaxis_env` installed so you can run the tool again later.
