<div align="center">
  <h1>📚 NarrativeOS EPUB Toolkit</h1>
  <p><strong>A comprehensive, blazing-fast local toolkit for scraping, managing, and compiling Light Novels into premium EPUBs.</strong></p>
  
  ![Version](https://img.shields.io/badge/version-1.3.260620-blue.svg?style=for-the-badge)
  ![Python](https://img.shields.io/badge/python-3.8+-blue.svg?style=for-the-badge&logo=python&logoColor=white)
  ![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
  ![Vanilla JS](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
</div>

---

## 📖 What is NarrativeOS?
Built originally to circumvent complex anti-scraping measures on translation sites, NarrativeOS gives you **absolute control** over your novel archiving experience. It seamlessly bridges the gap between web content and beautifully formatted eBooks. 

With a robust Python backend and a highly responsive Vanilla JavaScript frontend, it transforms raw web text into professional, structured EPUB files in seconds.

---

## 🚀 What's New in v1.3.260620 (Architecture & UI Refinement)
The latest update brings a monumental leap in maintainability, UI responsiveness, and stealth-scraping capabilities.

### 🧩 Frontend Modularization
- **ES6 Module Architecture**: Completely dismantled the monolithic `app.js` into highly focused, specialized modules (`editor.js`, `scraper.js`, `metadata.js`, `library.js`, etc.). This ensures blazing-fast load times and unparalleled code maintainability.
- **Dynamic Language Support**: The Metadata panel now supports dynamically adding and managing custom title languages. Break free from rigid "English/Romanji" defaults!

### 🖼️ Smart Media Engine
- **Auto-Download & WebP Compression**: Paste any direct image URL into your Markdown (`![img](https...)`). On compile, NarrativeOS securely downloads it, converts it to highly-optimized WebP, compresses it to save space, and automatically rewrites the path in your chapter to be local.
- **Full-Page Image Isolation**: Standard markdown tags `![...](...)` now act as isolated, full-page illustrations automatically in the compiled EPUB.

### ✨ Elevated UI & Visuals
- **Premium Themes**: Introducing hyper-refined aesthetic palettes, including *Indigo Dark*, *Cinema Rose*, *Financial Navy*, and *Clean SaaS*.
- **Image Autocomplete Gallery**: Type `![` to open a real-time, visual image autocomplete glass gallery directly inside the Markdown editor.
- **Fluid Micro-Interactions**: Built-in SVG `Gooey` filters and micro-animations to make the interface feel incredibly alive.

### 🛡️ Core Security & Stealth
- **Advanced Cloudflare Bypass**: Integrated `StealthyFetcher` engine to seamlessly bypass aggressive anti-bot protections like Cloudflare on modern translation sites.
- **Hardened Middleware**: Deployed stringent HTTP Headers including `Content-Security-Policy (CSP)`, `X-Frame-Options`, and `Referrer-Policy`. 
- **Strict Path Resolution**: Upgraded path-traversal blocking with stricter boundary checking and recursive resolution blocks.

---

## 🔒 Previous Major Updates

<details>
<summary><strong>v1.2.061926 (Security Update)</strong></summary>

- **Dynamic API Session Tokens**: Implemented a robust `X-API-Key` authentication system to completely lock down local backend endpoints against unauthorized access.
- **SSRF Mitigation**: Added strict IP validation (`is_safe_url`) to block unauthorized internal network requests during automated image downloads.
- **Enhanced Path Traversal Protection**: Hardened backend security to completely block malicious file access requests (`..`, `:` validation).
- **CORS Lockdowns**: Restrictive Cross-Origin Resource Sharing applied to ensure only authorized local interfaces can communicate with the API.
- **ReDoS Prevention**: Mitigated severe Regex Denial of Service vulnerabilities in the Table of Contents extraction logic.
- **Logging Overhaul**: Replaced rudimentary log writing with Python's robust `RotatingFileHandler`.
- **Thread Safety**: Implemented `threading.Lock` fixes during simultaneous markdown file saving to prevent data corruption.
</details>

---

## 🌟 Core Features

### 🌐 Web → Markdown Scraper
* **Automated Scraping**: Paste a URL and NarrativeOS will fetch the chapter and convert it perfectly to clean Markdown.
* **Batch Processing**: Feed it a list of URLs and process an entire volume in seconds.
* **Premium Bypass (HTML Paste)**: Got a locked chapter? Copy the HTML source code from your browser and paste it directly. NarrativeOS easily bypasses the lock.
* **Advanced Image Recovery**: Built-in canvas decoding easily breaks through obfuscated base64 canvases used by modern translation sites.

### ✏️ Premium Markdown Editor
* **Split-Pane View**: Write or edit in raw Markdown on the left while watching a real-time, styled HTML preview on the right.
* **Custom Syntax Highlighting**: Uses a custom-built highlighter tailored specifically for novel formatting, making dialogue and thoughts pop.
* **Auto-Saving & File Management**: Rename, delete, or create chapters seamlessly within the interface.

### 📋 Smart Metadata Management
* **Intelligent Carry-Over**: Creating a new volume automatically copies the Author, Artist, Genres, and Translator from the previous volume.
* **Language Targeting**: Set your primary title language (Japanese, English, Romaji) so your final EPUB looks exactly how you want it.

### 📦 Robust EPUB Compiler
* **Automated Book Assembly**: With one click, NarrativeOS parses your Markdown and metadata to generate a perfectly structured EPUB.
* **Premium Styling Elements**: Automatically supports Drop Caps, elegant Scene Breaks (`***` to `❖ ❖ ❖`), Character Thought Boxes `(thought)`, Character Stats Box `[stats]`, retro Game UI Notifications `[UI]`, and Full-Page Image Isolation.
* **Smart Image Engine**: Automatically downloads remote images, converts massive PNGs/JPEGs into lightweight WebP formats, compresses them, and safely localizes URLs.

---

## 🛠️ Tech Stack
* **Backend**: Python 3, FastAPI, Uvicorn, BeautifulSoup4, Scrapling
* **Frontend**: HTML5, Vanilla JavaScript (ES6 Modules), CSS3
* **Compiler Architecture**: Modular Python pipeline utilizing `zipfile`, `xml.etree.ElementTree`, and standard libraries.

---

## 🚀 Getting Started

### Prerequisites
You need **Python 3.8+** installed on your system.

### 1. Installation
Clone the repository and install the required dependencies:
```bash
git clone https://github.com/takoyune/NarrativeOS.git
cd NarrativeOS
pip install -r requirements.txt
```

### 2. Running the Server
To start the backend server and open the interface, simply run:
```bash
run_web.bat
```
*(Or manually run `python server.py`)*

### 3. Usage
Open your web browser and navigate to: **`http://localhost:8765`** (or the port defined in your console).
1. **Create a Novel**: Add a Novel folder and then a Volume.
2. **Scrape or Write**: Use the **Scraper** panel or **Editor** to add chapters.
3. **Add Metadata**: Set your cover image and Table of Contents in the **Metadata** panel.
4. **Build**: Click "Compile EPUB" in the **Builder** panel. Your finished book is ready!

---

## 📖 Custom Styling Guide
For a complete list of supported Markdown tricks (like `[UI]` boxes, `(thought)` boxes, and `(image)` splitters), refer to the [`Styling_and_Tricks_Guide.md`](Styling_and_Tricks_Guide.md) file included in this repository.
