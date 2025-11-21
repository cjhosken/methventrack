
import subprocess
import pycolmap
import imageio_ffmpeg
from pathlib import Path
import subprocess
import os

from PySide6.QtCore import QObject, QThread, Signal

class TrackingWorker(QObject):
    finished = Signal()
    log_message = Signal(str)
    error = Signal(str)

    def __init__(self, project_dir, camera_model, match_type, sift_ratio, sift_distance, pair_options):
        super().__init__()
        self.project_dir = project_dir
        self.camera_model = camera_model
        self.match_type = match_type
        self.sift_ratio = sift_ratio
        self.sift_distance = sift_distance
        self.pair_options = pair_options

    def run(self):
        try:
            import os, pycolmap
            
            video_path = os.path.join(self.project_dir, "source.mp4")
            frames_dir = os.path.join(self.project_dir, "frames")
            database = os.path.join(self.project_dir, "database.db")

            recon_root = os.path.join(self.project_dir, "reconstruction")
            next_index = len([d for d in os.listdir(recon_root) if os.path.isdir(os.path.join(recon_root, d))])
            recon_dir = os.path.join(recon_root, str(next_index))
            os.makedirs(recon_dir, exist_ok=True)

            self.log_message.emit("[1/4] Extracting frames…")
            generate_frames(video_path, frames_dir)
            self.log_message.emit("✅ Frames generated.")

            self.log_message.emit("[2/4] Extracting features…")
            extract_features(database, frames_dir, self.camera_model)
            self.log_message.emit("✅ Features extracted.")
            
            self.log_message.emit("[3/4] Matching features…")
            sift_options = pycolmap.SiftMatchingOptions(
                max_ratio=self.sift_ratio,
                max_distance=self.sift_distance
            )

            matching_options = pycolmap.FeatureMatchingOptions(
                sift=sift_options
            )
            

            match_features(database, self.match_type, matching_options, self.pair_options)
            self.log_message.emit("✅ Features matched.")

            self.log_message.emit("[4/4] Running mapping…")
            map_reconstruction(database, frames_dir, recon_dir)
            self.log_message.emit("✅ Reconstruction complete.")
            self.log_message.emit("=== Tracking completed successfully ===")

        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()


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


def extract_features(db_path, frames_path, camera_model):    
    # set image reader to single camera
    pycolmap.extract_features(
        database_path=db_path,
        image_path=frames_path,
        camera_mode=pycolmap.CameraMode.SINGLE,
        camera_model=camera_model
    )

def match_features(db_path, match_type, matching_options, pairing_options):
    if match_type == "exhaustive":
        pycolmap.match_exhaustive(
            database_path=db_path,
            matching_options=matching_options,
            pairing_options=pairing_options
        )
    elif match_type == "sequential":
        pycolmap.match_sequential(
            database_path=db_path,
            matching_options=matching_options,
            pairing_options=pairing_options
        )
    elif match_type == "spatial":
        pycolmap.match_spatial(
            database_path=db_path,
            matching_options=matching_options,
            pairing_options=pairing_options
        )

def map_reconstruction(db_path, frames_path, output_path):
    pycolmap.incremental_mapping(
        database_path=db_path,
        image_path=frames_path,
        output_path=output_path
    )

from pxr import Usd, UsdGeom, Gf, Sdf
import numpy as np

def create_usd(project_dir, reconstruction: "pycolmap.Reconstruction", export_path: str, horizontal_aperature=20.0):
    """
    Export a pycolmap.Reconstruction to USD with point cloud and animated camera.
    """
    stage = Usd.Stage.CreateNew(export_path)
    track_xform = UsdGeom.Xform.Define(stage, "/track")
    track_xform.AddRotateXOp().Set(180.0)
    
    # --- Point Cloud ---
    points = []
    colors = []

    for pt_id, pt in reconstruction.points3D.items():
        # COLMAP 3D coordinates
        points.append(pt.xyz)
        # Optional: RGB colors (0-255) -> (0-1)
        if hasattr(pt, 'rgb') and pt.rgb:
            colors.append([c / 255.0 for c in pt.rgb])
        else:
            colors.append([1.0, 1.0, 1.0])  # default white

    points = np.array(points)
    colors = np.array(colors)

    # Create a USD point instancer / points primitive
    pc_prim = UsdGeom.Points.Define(stage, "/track/PointCloud")
    pc_prim.CreatePointsAttr(points.tolist())
    pc_prim.CreateDisplayColorAttr(colors.tolist())
    pc_prim.CreateWidthsAttr([0.01])  # small point size

    # --- Animated Camera ---
    camera_prim = UsdGeom.Camera.Define(stage, "/track/Camera")
    transform_op = camera_prim.AddTransformOp()
    
    first_camera_id = next(iter(reconstruction.cameras.keys()))
    first_camera = reconstruction.cameras[first_camera_id]
    camera_prim.GetProjectionAttr().Set("perspective")
    
    vertical_aperature = horizontal_aperature * first_camera.height / first_camera.width
    camera_prim.GetHorizontalApertureAttr().Set(horizontal_aperature)
    camera_prim.GetVerticalApertureAttr().Set(vertical_aperature)
    
    # --- Camera background for Houdini ---
    bg_attr = camera_prim.GetPrim().CreateAttribute(
        "houdini:backgroundimage", Sdf.ValueTypeNames.String
    )

    # --- Lens distortion attribute (create once) ---
    k_attr = camera_prim.GetPrim().CreateAttribute(
        "lens:distortion_k", Sdf.ValueTypeNames.FloatArray
    )

    for img_name, image in reconstruction.images.items():
        try:
            frame = int(image.name.replace("frame_", "").replace(".jpg", ""))
        except:
            continue
        
        T_cw = image.cam_from_world().inverse()
        q = T_cw.rotation.quat
        q = q/ np.linalg.norm(q)
        t = T_cw.translation
        
        q_usd = Gf.Quatd(q[3], Gf.Vec3d(q[0], q[1], q[2]))
        R_cw = Gf.Matrix3d(q_usd)
        t_cw = Gf.Vec3d(t[0], t[1], t[2])
        
        R_local_x = Gf.Matrix3d().SetRotate(Gf.Rotation(Gf.Vec3d(1,0,0), 0))
        R_local_y = Gf.Matrix3d().SetRotate(Gf.Rotation(Gf.Vec3d(0, 1, 0), 180))
        R_local_z = Gf.Matrix3d().SetRotate(Gf.Rotation(Gf.Vec3d(0, 0, 1), 180))
        
        R_l = R_local_x * R_local_y * R_local_z
        
        R_combined = R_l * R_cw
        M = Gf.Matrix4d(1.0)
        M.SetRotate(R_combined)
        M.SetTranslateOnly(t_cw)
        
        transform_op.Set(M, float(frame))
        
        cam = reconstruction.cameras[image.camera_id]
        f, cx, cy, k = cam.params  # only focal length
        focal_length = f * (horizontal_aperature / first_camera.width)
        camera_prim.GetFocalLengthAttr().Set(focal_length, time=frame)

        # --- Lens distortion keyed ---
        k_attr.Set([float(cam.params[3])], time=float(frame))

        # --- Background image keyed per frame ---
        # You can use absolute or relative path
        img_path = os.path.join(project_dir, "frames", "frame_$F6.jpg").replace("\\", "/")  # image.path gives the original file path
        bg_attr.Set(img_path, time=float(frame))
                
    # Save USD
    stage.GetRootLayer().Save()
