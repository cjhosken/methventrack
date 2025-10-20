
import subprocess
import pycolmap
import imageio_ffmpeg
from pathlib import Path

import subprocess
from pathlib import Path

def generate_frames(source, dest_dir, dest_name="frame_%06d.jpg", fps=24):
    """Generate frames using packaged ffmpeg binary."""
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

    cmd = [
        ffmpeg_path, "-y", "-i", str(source),
        "-vf", f"fps={fps}",
        "-qscale:v", "2",
        str(dest_dir / dest_name)
    ]
    print(f"[FFmpeg] Using embedded binary: {ffmpeg_path}")
    subprocess.run(cmd, check=True)


def extract_features(db_path, frames_path):
    pycolmap.extract_features(
        database_path=db_path,
        image_path=frames_path
    )

def match_features(db_path, match_type="exhaustive"):
    if match_type == "exhaustive":
        pycolmap.match_exhaustive(
            database_path=db_path,
        )
    elif match_type == "sequential":
        pycolmap.match_sequential(
            database_path=db_path,
        )
    elif match_type == "spatial":
        pycolmap.match_spatial(
            database_path=db_path,
        )

def map_reconstruction(db_path, frames_path, output_path):
    pycolmap.incremental_mapping(
        database_path=db_path,
        image_path=frames_path,
        output_path=output_path
    )

from pxr import Usd, UsdGeom, Gf
import numpy as np

def create_usd(reconstruction: "pycolmap.Reconstruction", export_path: str):
    """
    Export a pycolmap.Reconstruction to USD with point cloud and animated camera.
    """
    stage = Usd.Stage.CreateNew(export_path)
    
    # --- Point Cloud ---
    points = []
    colors = []

    for pt_id, pt in reconstruction.points3D.items():
        # COLMAP 3D coordinates
        points.append(pt.xyz)
        # Optional: RGB colors (0-255) -> (0-1)
        if hasattr(pt, "rgb") and pt.rgb:
            colors.append([c / 255.0 for c in pt.rgb])
        else:
            colors.append([1.0, 1.0, 1.0])  # default white

    points = np.array(points)
    colors = np.array(colors)

    # Create a USD point instancer / points primitive
    pc_prim = UsdGeom.Points.Define(stage, "/PointCloud")
    pc_prim.CreatePointsAttr(points.tolist())
    pc_prim.CreateDisplayColorAttr(colors.tolist())
    pc_prim.CreateWidthsAttr([0.01])  # small point size

    # --- Animated Camera ---
    camera_prim = UsdGeom.Camera.Define(stage, "/Camera")

    # Sort images by frame order
    images = sorted(
        reconstruction.images.items(), key=lambda kv: kv[0]
    )

    for frame_idx, (img_name, img) in enumerate(images):
        pass
    
    # Save USD
    stage.GetRootLayer().Save()
