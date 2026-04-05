# STL Grid Splitter & Auto-Repair Tool

<p align="center">
  <strong>Professional CLI tool for preparing large STL models for 3D printing</strong>
</p>

<p align="center">
  Automatically repair broken meshes and split oversized models into clean, printable parts.
</p>

---

## Overview

This tool is designed to streamline the preparation of STL files for 3D printing.

Many models found online present common issues:
- They exceed the physical limits of standard printers
- They contain invalid or non-watertight geometry
- They require manual and time-consuming splitting

This script provides a complete, automated solution.

---

## Core Functionality

The script performs the following operations:

1. Loads and validates the STL file
2. Detects and repairs mesh issues when possible
3. Measures the model dimensions
4. Computes optimal splits based on printer constraints
5. Divides the model into a 3D grid (X, Y, Z)
6. Exports all resulting parts into an organized directory

---

## Features

- Automatic mesh repair (non-manifold, holes, topology issues)
- Dimension-aware splitting based on printer limits
- Full 3-axis grid segmentation
- Clean and structured output folders
- Informative, color-coded terminal logs
- Optional model rotation before processing

---

## Installation

### Requirements
- Python 3.x

### Dependencies

```bash
pip install numpy trimesh pymeshfix pyvista
```

---

## Usage

### Basic command

```bash
python super-split-file.py "path/to/model.stl" --max-x 210 --max-y 210 --max-z 240
```

This command:
- Repairs the mesh if needed
- Splits the model according to the specified dimensions
- Saves all parts in a new folder

---

## Command-Line Options

| Argument     | Shortcut | Description |
|--------------|----------|-------------|
| input_stl    | —        | Path to the STL file (required) |
| --max-x      | -mx      | Max size on X axis (mm) |
| --max-y      | -my      | Max size on Y axis (mm) |
| --max-z      | -mz      | Max size on Z axis (mm) |
| --xsplit     | —        | Manual splits on X |
| --ysplit     | —        | Manual splits on Y |
| --zsplit     | —        | Manual splits on Z |
| --flip       | —        | Rotate model 180° on X axis |

---

## Examples

### Automatic splitting

```bash
python super-split-file.py model.stl --max-x 220 --max-y 220 --max-z 250
```

### Manual splitting

```bash
python super-split-file.py model.stl --xsplit 3 --ysplit 2 --zsplit 2
```

### Mixed configuration

```bash
python super-split-file.py model.stl --xsplit 5 --max-x 200
```

### Apply rotation

```bash
python super-split-file.py model.stl --max-x 200 --flip
```

---

## Output Structure

After execution, a folder is created automatically:

```
/model-name/
├── model-name_splt-01.stl
├── model-name_splt-02.stl
├── model-name_splt-03.stl
...
```

---

## Processing Details

- Mesh loading and manipulation handled by trimesh
- Automatic repair via pymeshfix
- Bounding box analysis for dimension extraction
- Grid generation using numpy
- Boolean intersection for segment extraction

---

## Notes

- Printer size constraints take priority over manual split values
- Some complex meshes may not fully repair, but processing will continue
- Ensure STL files are valid for best results

---

## Troubleshooting

### File fails to load
- Verify file path
- Ensure STL format is correct

### Python issues

```bash
python --version
```

Ensure Python 3 is installed.
