# Notebooks

This directory contains Jupyter notebooks for **exploratory analysis and prototyping**.

All production logic has been extracted into modular Python files in `src/`.
The notebook imports from `src/` and is kept lightweight for interactive exploration.

## Usage

```bash
jupyter notebook notebooks/exploration.ipynb
```

> **Note:** The original monolithic notebook has been refactored into the `src/` modules.
> See `src/pipeline.py` for the end-to-end workflow.
