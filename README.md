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

<h1 align="center">🎥 Methven Track</h1>

<div align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=fff" alt="Python Badge"/>
  <img src="https://img.shields.io/badge/USD-16B7FB?logo=usd&logoColor=fff" alt="USD Badge"/>
  <br/>
  <a href="https://github.com/cjhosken/methventrack/actions/workflows/build.yml">
    <img src="https://github.com/cjhosken/methventrack/actions/workflows/build.yml/badge.svg?branch=main" alt="App Build Status"/>
  </a>
</div>

---

## 🧭 Overview

**Methven Track** is a Python application that generates **3D camera tracks from video clips**.
It leverages **[COLMAP](https://colmap.github.io/)** for structure-from-motion reconstruction and exports results in **USD (Universal Scene Description)** format.

---

## ⚙️ How It Works

1. **Extract frames** from your video using FFmpeg.
2. **Detect and match features** with COLMAP.
3. **Reconstruct the camera track** in 3D.
4. **Export the camera path and point cloud** to USD.

---

## 🚀 Getting Started

1. **Create a New Project**
   Choose a source video and a folder to store project files.

2. **Adjust Settings**
   Select compute device, camera model, and feature matching type.
   *Default settings usually work great!*

3. **Run Tracking**
   Click the `▶ Run Tracking` button to start reconstruction.

4. **Export to USD**
   Once tracking completes, export your 3D reconstruction to a `.usd` file.

---

## 🧩 Known Issues & Future Ideas

* ⚠️ **Orientation and scale** may occasionally need manual adjustment.
* 🐛 **Logging system** doesn’t print all output — run via terminal for full logs.
* 💡 **GLOMAP support** could be added in future (Python bindings may not exist yet).
* 🙌 **Contributions** are welcome — whether bug reports, code improvements, or algorithmic suggestions!
* 🎬 Some challenging shots might still require professional camera tracking software.

---

## 📦 Download

👉 Get the latest release from the [**Releases Page**](https://github.com/cjhosken/methventrack/releases).

---

## 👤 Author

Created by **Christopher Hosken**
Inspired by **Josh Methven**

* 📧 [hoskenchristopher@gmail.com](mailto:hoskenchristopher@gmail.com)
* 🔗 [LinkedIn: christopher-hosken](https://www.linkedin.com/in/christopher-hosken)

---