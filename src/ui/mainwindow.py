from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
    QFileDialog, QMessageBox, QTextEdit, QComboBox, QStackedWidget, QFormLayout, QSpinBox, QDoubleSpinBox, QMenuBar
)
from PySide6.QtGui import QAction
from PySide6.QtCore import QObject, Signal

import os
import shutil
import pycolmap

from tracking import (
    generate_frames, extract_features,
    match_features, map_reconstruction, create_usd
)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Methven Track")
        self.resize(400, 700)

        self.project_dir = None
        self.source_video = None
        
        # --- Menu Bar ---
        self.menu_bar = QMenuBar(self)
        
        new_action = QAction("🆕 New Project", self)
        new_action.triggered.connect(self.create_project)
        self.menu_bar.addAction(new_action)

        open_action = QAction("📂 Open Project", self)
        open_action.triggered.connect(self.open_project)
        self.menu_bar.addAction(open_action)

        # --- Main layout ---
        main_v_layout = QVBoxLayout(self)
        main_v_layout.setContentsMargins(10, 10, 10, 10)
        main_v_layout.addWidget(self.menu_bar)  # top menu bar

        # Horizontal layout for sidebar + viewport
        self.main_layout = QVBoxLayout()
        main_v_layout.addLayout(self.main_layout, 1)

        # --- Sidebar UI ---
        self.main_layout.addWidget(QLabel("<b>Tracking</b>"))
        
        sift_settings_widget = QWidget()
        sift_settings_layout = QFormLayout()
        
        self.device_selector = QComboBox()
        self.device_selector.addItems(["auto", "gpu", "cpu"])
        sift_settings_layout.addRow("Compute Device:", self.device_selector)
        

        
        self.camera_model_selector = QComboBox()
        self.camera_model_selector.addItems(["SIMPLE_RADIAL", "FISHEYE"])
        sift_settings_layout.addRow("Camera Model:", self.camera_model_selector)
        
        self.max_sift_ratio_spin = QDoubleSpinBox()
        self.max_sift_ratio_spin.setValue(0.8)
        self.max_sift_distance_spin = QDoubleSpinBox()
        self.max_sift_distance_spin.setValue(0.7)
        sift_settings_layout.addRow("Max Sift ratio:", self.max_sift_ratio_spin)
        sift_settings_layout.addRow("Max Sift distance:", self.max_sift_distance_spin)
        
        sift_settings_widget.setLayout(sift_settings_layout)
        self.main_layout.addWidget(sift_settings_widget)

        self.match_type_selector = QComboBox()
        self.match_type_selector.addItems(["exhaustive", "sequential", "spatial"])
        self.main_layout.addWidget(QLabel("Feature Matching Type:"))
        self.main_layout.addWidget(self.match_type_selector)
        
        self.match_options_stack = QStackedWidget()
        self.main_layout.addWidget(self.match_options_stack)

        # Exhaustive options
        exhaustive_widget = QWidget()
        exhaustive_layout = QFormLayout()
        self.block_size_spin = QSpinBox()
        self.block_size_spin.setValue(50)
        exhaustive_layout.addRow("Block size:", self.block_size_spin)
        exhaustive_widget.setLayout(exhaustive_layout)

        # Sequential options
        sequential_widget = QWidget()
        sequential_layout = QFormLayout()
        self.overlap_spin = QSpinBox()
        self.overlap_spin.setValue(15)
        sequential_layout.addRow("Overlap:", self.overlap_spin)
        sequential_widget.setLayout(sequential_layout)

        # Spatial options
        spatial_widget = QWidget()
        spatial_layout = QFormLayout()
        self.max_neighbors_spin = QSpinBox()
        self.max_neighbors_spin.setValue(50)
        self.max_distance_spin = QDoubleSpinBox()
        self.max_distance_spin.setValue(100.0)
        spatial_layout.addRow("Max neighbors:", self.max_neighbors_spin)
        spatial_layout.addRow("Max distance:", self.max_distance_spin)
        spatial_widget.setLayout(spatial_layout)

        self.match_options_stack.addWidget(exhaustive_widget)
        self.match_options_stack.addWidget(sequential_widget)
        self.match_options_stack.addWidget(spatial_widget)

        # Switch on match type change
        self.match_type_selector.currentIndexChanged.connect(
            lambda i: self.match_options_stack.setCurrentIndex(i)
        )

        self.track_btn = QPushButton("▶ Run Tracking")
        self.track_btn.setEnabled(False)
        self.track_btn.clicked.connect(self.handle_tracking_action)
        self.main_layout.addWidget(self.track_btn)

        # Reconstruction selector
        self.main_layout.addWidget(QLabel("<b>Reconstructions</b>"))
        self.recon_selector = QComboBox()
        self.recon_selector.setEnabled(False)
        self.main_layout.addWidget(self.recon_selector)

        self.export_btn = QPushButton("💾 Export USD")
        self.export_btn.setVisible(False)
        self.export_btn.clicked.connect(self.export_usd)
        self.main_layout.addWidget(self.export_btn)

        self.main_layout.addWidget(QLabel("<b>Log Output</b>"))
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setPlaceholderText("Tracking logs will appear here…")

        self.main_layout.addWidget(self.log_box, 1)

    # ----------------------------------------------------
    # Utility
    # ----------------------------------------------------
    def log(self, message: str):
        self.log_box.append(message)
        self.log_box.verticalScrollBar().setValue(
            self.log_box.verticalScrollBar().maximum()
        )
        print(message)

    def set_project(self, project_dir: str):
        self.project_dir = project_dir
        self.setWindowTitle(f"Methven Track {project_dir}")
        self.track_btn.setEnabled(True)
        self.log(f"📁 Loaded project: {project_dir}")

        self.update_reconstruction_list()
        if self.recon_selector.count() > 0:
            self.recon_selector.setCurrentIndex(0)
            self.on_recon_selection_changed(0)

    def update_reconstruction_list(self):
        """Refresh the reconstruction dropdown."""
        self.recon_selector.clear()
        recon_dir = os.path.join(self.project_dir, "reconstruction")
        if not os.path.exists(recon_dir):
            os.makedirs(recon_dir, exist_ok=True)

        recon_folders = [
            name for name in os.listdir(recon_dir)
            if os.path.isdir(os.path.join(recon_dir, name))
        ]
        recon_folders.sort()

        if recon_folders:
            self.recon_selector.addItems(recon_folders)
            self.recon_selector.setEnabled(True)
            self.track_btn.setText("🔁 Retrack")
            self.export_btn.setVisible(True)
            self.log(f"🧠 Found {len(recon_folders)} reconstruction(s).")
        else:
            self.recon_selector.setEnabled(False)
            self.track_btn.setText("▶ Run Tracking")
            self.export_btn.setVisible(False)
    # ----------------------------------------------------
    # Project management
    # ----------------------------------------------------
    def create_project(self):
        video_path, _ = QFileDialog.getOpenFileName(
            self, "Select Source Video", "",
            "Videos (*.mp4 *.avi *.mov *.mkv);;All Files (*)"
        )
        if not video_path:
            return

        project_path = QFileDialog.getExistingDirectory(
            self, "Select Folder to Create Project In", os.path.expanduser("~")
        )

        os.makedirs(project_path, exist_ok=True)

        dest_video = os.path.join(project_path, "source.mp4")
        shutil.copy2(video_path, dest_video)
        self.log(f"📀 Copied source video to: {dest_video}")

        os.makedirs(os.path.join(project_path, "frames"), exist_ok=True)
        os.makedirs(os.path.join(project_path, "reconstruction"), exist_ok=True)

        self.set_project(project_path)

    def open_project(self):
        project_dir = QFileDialog.getExistingDirectory(
            self, "Open Project Folder", os.path.expanduser("~")
        )
        if not project_dir:
            return

        video_path = os.path.join(project_dir, "source.mp4")
        if not os.path.exists(video_path):
            QMessageBox.warning(self, "Invalid Project", "This folder doesn't contain a valid project (missing source.mp4).")
            return

        self.source_video = video_path
        self.set_project(project_dir)

    # ----------------------------------------------------
    # Tracking control
    # ----------------------------------------------------
    def handle_tracking_action(self):
        """Handle Track or Retrack button click."""
        if self.track_btn.text().startswith("🔁"):
            confirm = QMessageBox.question(
                self, "Retrack Project",
                "This will clear all existing reconstructions.\nContinue?",
                QMessageBox.Yes | QMessageBox.No
            )
            if confirm == QMessageBox.No:
                return

            # Clear reconstructions
            recon_dir = os.path.join(self.project_dir, "reconstruction")
            for item in os.listdir(recon_dir):
                path = os.path.join(recon_dir, item)
                if os.path.isdir(path):
                    shutil.rmtree(path)
            self.log("🧹 Cleared old reconstructions.")

        self.run_tracking()

    # ----------------------------------------------------
    # Tracking pipeline
    # ----------------------------------------------------
    
    def run_tracking(self):
        if not self.project_dir:
            QMessageBox.warning(self, "No Project", "Please create or open a project first.")
            return

        video_path = os.path.join(self.project_dir, "source.mp4")
        frames_dir = os.path.join(self.project_dir, "frames")
        database = os.path.join(self.project_dir, "database.db")

        # Create new reconstruction subfolder
        recon_root = os.path.join(self.project_dir, "reconstruction")
        next_index = len([
            d for d in os.listdir(recon_root)
            if os.path.isdir(os.path.join(recon_root, d))
        ])
        recon_dir = os.path.join(recon_root, str(next_index))
        os.makedirs(recon_dir, exist_ok=True)
        
        device = {
            "gpu": pycolmap.Device.cuda,
            "cpu": pycolmap.Device.cpu
        }.get(self.device_selector.currentText(), pycolmap.Device.auto)

        self.track_btn.setEnabled(False)
        self.log(f"=== Starting tracking pipeline (recon #{next_index}) ===")
    
        try:
            self.log("[1/4] Extracting frames with ffmpeg…")
            generate_frames(source=video_path, dest_dir=frames_dir)
            self.log("✅ Frames generated successfully.")

            self.log("[2/4] Extracting features with COLMAP…")
            extract_features(database, frames_dir, device, self.camera_model_selector.currentText())
            self.log("✅ Features extracted.")

            self.log("[3/4] Matching features…")
            
            matching_type = self.match_type_selector.currentText()
            
            use_gpu = self.device_selector.currentText() == "gpu"
            
            sift_options = pycolmap.SiftOptions(
                use_gpu=use_gpu,
                max_ratio=self.max_sift_ratio_spin.value(),
                max_distanec=self.max_sift_distance_spin.value()
            )
            
            if matching_type == "exhaustive":
                matching_options = pycolmap.ExhaustiveMatchingOptions(
                    block_size=self.block_size_spin.value()
                )
            elif matching_type == "sequential":
                matching_options = pycolmap.SequentialMatchingOptions(
                    overlap = self.overlap_spin.value()
                )
            elif matching_type == "spatial":
                matching_options = pycolmap.SpatialMatchingOptions(
                    max_num_neighbors=self.max_neighbors_spin.value(),
                    max_distance=self.max_distance_spin.value()
                )
            
            match_features(database, matching_type, sift_options, matching_options, device)
            self.log("✅ Features matched.")

            self.log("[4/4] Running mapping (structure-from-motion)…")
            map_reconstruction(database, frames_dir, recon_dir)
            self.log("✅ Reconstruction complete.")
            self.log("=== Tracking completed successfully ===")

            self.export_btn.setVisible(True)
            self.update_reconstruction_list()

        except Exception as e:
            self.log(f"❌ Error: {e}")
            QMessageBox.critical(self, "Tracking Failed", f"An error occurred:\n{str(e)}")
        finally:
            self.track_btn.setEnabled(True)


    def update_reconstruction_list(self):
        """Refresh the reconstruction dropdown by finding folders containing COLMAP .bin files."""
        self.recon_selector.clear()
        recon_root = os.path.join(self.project_dir, "reconstruction")
        if not os.path.exists(recon_root):
            os.makedirs(recon_root, exist_ok=True)

        valid_recons = []

        # Walk through subfolders recursively
        for root, dirs, files in os.walk(recon_root):
            # Check if folder contains any .bin files
            if any(f.endswith(".bin") for f in files):
                # Make the path relative to recon_root for dropdown display
                rel_path = os.path.relpath(root, recon_root)
                valid_recons.append(rel_path)

        valid_recons.sort()

        if valid_recons:
            self.recon_selector.addItems(valid_recons)
            self.recon_selector.setEnabled(True)
            self.track_btn.setText("🔁 Retrack")
            self.export_btn.setVisible(True)
            self.log(f"🧠 Found {len(valid_recons)} reconstruction(s).")
        else:
            self.recon_selector.setEnabled(False)
            self.track_btn.setText("▶ Run Tracking")
            self.export_btn.setVisible(False)

    # ----------------------------------------------------
    # Export
    # ----------------------------------------------------
    def export_usd(self):
        if not self.project_dir:
            return
        
        export_dir = os.path.join(self.project_dir, "export")
        os.makedirs(export_dir, exist_ok=True)

        selected_recon = self.recon_selector.currentText() or "0"
        recon_dir = os.path.join(self.project_dir, "reconstruction", selected_recon)
        
        recon_clean_name = selected_recon.replace('/', '_').replace('\\', '_')

        usd_path, _ = QFileDialog.getSaveFileName(
            self, "Export to USD", os.path.join(export_dir, f"camera_track_{recon_clean_name}.usda"),
            "USD Files (*.usd *.usda)"
        )
        if usd_path:
            try:
                self.log(f"Exporting reconstruction #{selected_recon} to USD…")
                recon = pycolmap.Reconstruction(recon_dir)
                create_usd(self.project_dir, recon, usd_path)
                self.log(f"✅ USD file exported to: {usd_path}")
                QMessageBox.information(self, "Export Complete", f"USD file exported to:\n{usd_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", f"Error exporting USD:\n{str(e)}")
