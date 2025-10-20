<h1 align="center">Methven Track</h1>

<div align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=fff" alt="Python"/>
  <img src="https://img.shields.io/badge/USD-16B7FB" alt="USD"/>
  <br/>
  <a href="https://github.com/cjhosken/methventrack/actions/workflows/build.yml">
    <img src="https://github.com/cjhosken/methventrack/actions/workflows/build.yml/badge.svg?branch=main" alt="App Build"/>
  </a>
</div>

---

## Overview

**Methven Track** is a Python application that generates **3D camera tracks from a video clip**.  
It uses **COLMAP** for structure-from-motion under the hood and exports results in **USD (Universal Scene Description)** format.

---

## How It Works

1. Extract frames from your video using FFmpeg.
2. Detect and match features with COLMAP.
3. Reconstruct the camera track in 3D.
4. Export the camera track and point cloud to USD.

---

## Getting Started

1. **Create a new project**: Select a source video and a folder to store project files.  
2. **Adjust settings**: Choose compute device, camera model, feature matching type, etc.  
3. **Run tracking**: Click the `▶ Run Tracking` button.  
4. **Export USD**: Once tracking is complete, export your reconstruction as a USD file.

---

## Known Issues & Future Ideas
- The **orientation and scale** of the track can sometimes be off. Manual adjustment may be required.  
- The **logging system isnt printing everything**, its highly recommended to run this from a terminal for now.
- **GLOMAP support** would be a nice addition, though Python bindings may not exist yet.  
- Contributions, bug reports, and algorithm suggestions are welcome!

---

## 📦 Download

Get the latest version from the [Release Page](https://github.com/cjhosken/methventrack/releases).

---

## 📬 Contact & Information

Created by **Christopher Hosken**, inspired by Josh Methven.  

- 📧 Email: [hoskenchristopher@gmail.com](mailto:hoskenchristopher@gmail.com)  
- 🔗 LinkedIn: [christopher-hosken](https://www.linkedin.com/in/christopher-hosken)
