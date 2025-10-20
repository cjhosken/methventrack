from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
    QFileDialog, QMessageBox, QTextEdit, QComboBox
)
import os
import shutil
import pycolmap

from ui.glviewport import GLViewport

from tracking import (
    generate_frames, extract_features,
    match_features, map_reconstruction, create_usd
)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Methven Track")
        self.resize(1200, 700)

        self.project_dir = None
        self.source_video = None

        # --- Main layout ---
        self.main_layout = QHBoxLayout(self)
        self.sidebar = QVBoxLayout()
        self.main_layout.addLayout(self.sidebar, 0)
        self.viewport = GLViewport(self)
        self.main_layout.addWidget(self.viewport, 1)

        # --- Sidebar UI ---
        self.sidebar.addWidget(QLabel("<b>Project Controls</b>"))
        self.new_btn = QPushButton("🆕 New Project")
        self.new_btn.clicked.connect(self.create_project)
        self.open_btn = QPushButton("📂 Open Project")
        self.open_btn.clicked.connect(self.open_project)
        self.sidebar.addWidget(self.new_btn)
        self.sidebar.addWidget(self.open_btn)
        

        self.sidebar.addWidget(QLabel("<b>Tracking</b>"))
        self.match_type_selector = QComboBox()
        self.match_type_selector.addItems(["exhaustive", "sequential", "spatial"])
        self.sidebar.addWidget(QLabel("Feature Matching Type:"))
        self.sidebar.addWidget(self.match_type_selector)

        self.track_btn = QPushButton("▶ Run Tracking")
        self.track_btn.setEnabled(False)
        self.track_btn.clicked.connect(self.handle_tracking_action)
        self.sidebar.addWidget(self.track_btn)

        # Reconstruction selector
        self.sidebar.addWidget(QLabel("<b>Reconstructions</b>"))
        self.recon_selector = QComboBox()
        self.recon_selector.setEnabled(False)
        self.recon_selector.currentIndexChanged.connect(self.on_recon_selection_changed)
        self.sidebar.addWidget(self.recon_selector)

        self.export_btn = QPushButton("💾 Export USD")
        self.export_btn.setVisible(False)
        self.export_btn.clicked.connect(self.export_usd)
        self.sidebar.addWidget(self.export_btn)

        self.sidebar.addWidget(QLabel("<b>Log Output</b>"))
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setPlaceholderText("Tracking logs will appear here…")
        self.sidebar.addWidget(self.log_box, 1)

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

        project_dir = QFileDialog.getExistingDirectory(
            self, "Select Folder to Create Project In", os.path.expanduser("~")
        )
        if not project_dir:
            return

        project_name = os.path.splitext(os.path.basename(video_path))[0]
        project_path = os.path.join(project_dir, project_name)
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

        self.track_btn.setEnabled(False)
        self.log(f"=== Starting tracking pipeline (recon #{next_index}) ===")
        try:
            self.log("[1/4] Extracting frames with ffmpeg…")
            generate_frames(source=video_path, dest_dir=frames_dir)
            self.log("✅ Frames generated successfully.")

            self.log("[2/4] Extracting features with COLMAP…")
            extract_features(database, frames_dir)
            self.log("✅ Features extracted.")

            self.log("[3/4] Matching features…")
            match_features(database)
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


    def on_recon_selection_changed(self, index):
        """Load the selected reconstruction into the viewport."""
        if not self.project_dir:
            return

        recon_name = self.recon_selector.currentText()
        if not recon_name:
            return

        recon_dir = os.path.join(self.project_dir, "reconstruction", recon_name)
        if os.path.exists(recon_dir):
            try:
                recon = pycolmap.Reconstruction(recon_dir)
                self.viewport.load_reconstruction(recon)
                self.log(f"🖥 Loaded reconstruction #{recon_name} into viewport.")
            except Exception as e:
                self.log(f"❌ Failed to load reconstruction: {e}")

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

        usd_path, _ = QFileDialog.getSaveFileName(
            self, "Export to USD", os.path.join(export_dir, f"camera_track_{selected_recon.replace("/", "_")}.usda"),
            "USD Files (*.usd *.usda)"
        )
        if usd_path:
            try:
                self.log(f"Exporting reconstruction #{selected_recon} to USD…")
                recon = pycolmap.Reconstruction(recon_dir)
                create_usd(recon, usd_path)
                self.log(f"✅ USD file exported to: {usd_path}")
                QMessageBox.information(self, "Export Complete", f"USD file exported to:\n{usd_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", f"Error exporting USD:\n{str(e)}")
