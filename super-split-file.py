import os
import argparse
import numpy as np
import trimesh
import pymeshfix

# Enable ANSI escape sequences for Windows CMD
os.system("")

class TerminalColors:
    INFO = '\033[96m'    # Cyan
    SUCCESS = '\033[92m' # Green
    WARNING = '\033[93m' # Yellow
    ERROR = '\033[91m'   # Red
    RESET = '\033[0m'    # Reset

def calculate_splits(model_size, max_size):
    """
    Calculates the required number of divisions to fit a model within a given maximum size.
    """
    if max_size is None or max_size <= 0:
        raise ValueError("Maximum size must be a positive numerical value.")
    return int(np.ceil(model_size / max_size))

def repair_mesh_if_needed(mesh):
    """
    Checks if the mesh is a solid volume (watertight). 
    Attempts to repair the mesh using pymeshfix if it contains holes or structural errors.
    Returns the repaired mesh or the original mesh if no repair was successful.
    """
    if mesh.is_volume:
        print(f"{TerminalColors.SUCCESS}[SUCCESS]{TerminalColors.RESET} Mesh is watertight. No structural repair required.")
        return mesh
        
    print(f"{TerminalColors.WARNING}[WARNING]{TerminalColors.RESET} Mesh is not a solid volume. Initializing automatic repair sequence...")
    try:
        # Cast trimesh TrackedArrays to standard strict numpy arrays required by pymeshfix C++ bindings
        vertices_array = np.asarray(mesh.vertices, dtype=np.float64)
        faces_array = np.asarray(mesh.faces, dtype=np.int32)
        
        v_clean, f_clean = pymeshfix.clean_from_arrays(vertices_array, faces_array)
        repaired_mesh = trimesh.Trimesh(vertices=v_clean, faces=f_clean)
        
        if repaired_mesh.is_volume:
            print(f"{TerminalColors.SUCCESS}[SUCCESS]{TerminalColors.RESET} Repair successful. The mesh has been converted to a solid volume.")
        else:
            print(f"{TerminalColors.WARNING}[WARNING]{TerminalColors.RESET} Repair completed, but the mesh may still contain complex topological issues.")
            
        return repaired_mesh
        
    except Exception as e:
        print(f"{TerminalColors.ERROR}[ERROR]{TerminalColors.RESET} Automatic repair process failed: {e}")
        print(f"{TerminalColors.INFO}[INFO]{TerminalColors.RESET} Proceeding with the original mesh. Intersection processing errors may occur.")
        return mesh

def split_stl_into_grid(input_stl, xsplit=None, ysplit=None, zsplit=None, max_x=None, max_y=None, max_z=None, flip=False):
    """
    Loads an STL file, repairs it if necessary, and divides it into smaller segments 
    based on specified axis limits or explicit division counts. Saves outputs in a dedicated folder.
    """
    print(f"{TerminalColors.INFO}[INFO]{TerminalColors.RESET} Loading model: {input_stl}")
    try:
        mesh = trimesh.load(input_stl)
    except Exception as e:
        raise ValueError(f"Failed to load STL file: {e}")

    if not isinstance(mesh, trimesh.Trimesh):
        raise ValueError("The loaded file does not contain a valid 3D mesh structure.")

    # Validate and attempt to fix mesh topology
    mesh = repair_mesh_if_needed(mesh)

    if flip:
        rotation_matrix = trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0])
        mesh.apply_transform(rotation_matrix)
        print(f"{TerminalColors.INFO}[INFO]{TerminalColors.RESET} Applied 180-degree rotation transformation along the X-axis.")

    # Extract bounding box dimensions
    bounds = mesh.bounds
    model_size_x = bounds[1][0] - bounds[0][0]
    model_size_y = bounds[1][1] - bounds[0][1]
    model_size_z = bounds[1][2] - bounds[0][2]

    print(f"{TerminalColors.INFO}[INFO]{TerminalColors.RESET} Main part dimensions (mm) - X: {model_size_x:.2f}, Y: {model_size_y:.2f}, Z: {model_size_z:.2f}")

    # Calculate necessary divisions per axis
    xsplit = calculate_splits(model_size_x, max_x) if max_x else (xsplit or 1)
    ysplit = calculate_splits(model_size_y, max_y) if max_y else (ysplit or 1)
    zsplit = calculate_splits(model_size_z, max_z) if max_z else (zsplit or 1)

    # Ensure at least one segment per axis
    xsplit, ysplit, zsplit = max(1, xsplit), max(1, ysplit), max(1, zsplit)

    segment_size_x = model_size_x / xsplit
    segment_size_y = model_size_y / ysplit
    segment_size_z = model_size_z / zsplit

    print(f"{TerminalColors.INFO}[INFO]{TerminalColors.RESET} Divisions matrix - X: {xsplit}, Y: {ysplit}, Z: {zsplit}")
    print(f"{TerminalColors.INFO}[INFO]{TerminalColors.RESET} Target segment size (mm) - X: {segment_size_x:.2f}, Y: {segment_size_y:.2f}, Z: {segment_size_z:.2f}")

    # Set up output directory
    input_dir = os.path.dirname(os.path.abspath(input_stl))
    base_name = os.path.splitext(os.path.basename(input_stl))[0]
    output_dir = os.path.join(input_dir, base_name)
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"{TerminalColors.INFO}[INFO]{TerminalColors.RESET} Created dedicated output directory: {output_dir}")

    # Generate spatial intervals
    x_extent = np.linspace(bounds[0][0], bounds[1][0], xsplit + 1)
    y_extent = np.linspace(bounds[0][1], bounds[1][1], ysplit + 1)
    z_extent = np.linspace(bounds[0][2], bounds[1][2], zsplit + 1)

    part_number = 1
    for i in range(xsplit):
        for j in range(ysplit):
            for k in range(zsplit):
                x_min, x_max = x_extent[i], x_extent[i + 1]
                y_min, y_max = y_extent[j], y_extent[j + 1]
                z_min, z_max = z_extent[k], z_extent[k + 1]

                # Define the intersection bounding box
                bounds_box = trimesh.creation.box(
                    extents=(x_max - x_min, y_max - y_min, z_max - z_min),
                    transform=trimesh.transformations.translation_matrix(
                        [(x_max + x_min) / 2, (y_max + y_min) / 2, (z_max + z_min) / 2]
                    )
                )

                # Attempt Boolean intersection
                try:
                    section = mesh.intersection(bounds_box)
                except Exception as e:
                    print(f"{TerminalColors.WARNING}[WARNING]{TerminalColors.RESET} Mathematical intersection failed for sector {part_number}: {e}")
                    continue

                # Export if the section contains geometry
                if not section.is_empty:
                    output_filename = os.path.join(output_dir, f"{base_name}_splt-{part_number:02d}.stl")
                    section.export(output_filename)
                    print(f"{TerminalColors.INFO}[INFO]{TerminalColors.RESET} Exported segment: {output_filename}")
                    part_number += 1
                    
    print(f"{TerminalColors.SUCCESS}[SUCCESS]{TerminalColors.RESET} Batch slicing process completed successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process and split an STL file into a 3D grid of smaller segments.")
    parser.add_argument("input_stl", help="Absolute or relative path to the source STL file")
    parser.add_argument("--xsplit", type=int, default=None, help="Explicit number of divisions along the X-axis")
    parser.add_argument("--ysplit", type=int, default=None, help="Explicit number of divisions along the Y-axis")
    parser.add_argument("--zsplit", type=int, default=None, help="Explicit number of divisions along the Z-axis")
    parser.add_argument("--max-x", "-mx", type=float, default=None, help="Maximum physical printer boundary along the X-axis (mm)")
    parser.add_argument("--max-y", "-my", type=float, default=None, help="Maximum physical printer boundary along the Y-axis (mm)")
    parser.add_argument("--max-z", "-mz", type=float, default=None, help="Maximum physical printer boundary along the Z-axis (mm)")
    parser.add_argument("--flip", action="store_true", help="Apply a 180-degree rotation along the X-axis prior to splitting")

    args = parser.parse_args()

    try:
        split_stl_into_grid(
            input_stl=args.input_stl,
            xsplit=args.xsplit,
            ysplit=args.ysplit,
            zsplit=args.zsplit,
            max_x=args.max_x,
            max_y=args.max_y,
            max_z=args.max_z,
            flip=args.flip
        )
    except Exception as e:
        print(f"{TerminalColors.ERROR}[ERROR]{TerminalColors.RESET} Execution terminated due to a critical error: {e}")