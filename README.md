<h1 align="center">Methven Track</h1>

<div align="center">
<img src="https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=fff"/>

<img src="https://img.shields.io/badge/USD-16B7FB?style=for-the-badge"/>
    
<br/>

<a href="https://github.com/cjhosken/methventrack/actions/workflows/build.yml">
    <img src="https://github.com/cjhosken/methventrack/actions/workflows/build.yml/badge.svg?branch=main" alt="App Build"/>
</a>

</div>

Methven Track is a python application that creates 3D camera tracks from a video clip.

## How it works

The tool uses COLMAP under the hood, with a conversion in USD (Universal Scene Description) at the end.

## How to use it

1. Create a new project by choose a video clip and specifying a folder directory.
2. Set the settings you want (default should normally word)
3. Hit track!
4. Export as a USD


## Known Issues & Ideas
1. The orientation and scale of the track can be off and will need adjusting. 

2. It would be nice to have GLOMAP supported as well, however I'm not sure if there are any python bindings for it.


If anyone knows any algorithms or can help dont hestitate to reach out.


📦 Get the latest version from the Release Page.

--

## 📬 Contact & Information
Methven Track was created by Christopher Hosken, It's named after Josh Methven, who tasked him with making it.

📧 Email: hoskenchristopher@gmail.com
🔗 LinkedIn: christopher-hosken