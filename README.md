<div align="center">
  <h1>📚 NarrativeOS EPUB Toolkit</h1>
  <p><strong>A comprehensive, blazing-fast local toolkit for scraping, managing, and compiling Light Novels into premium EPUBs.</strong></p>
  
  ![Version](https://img.shields.io/badge/version-1.2.061926-blue.svg?style=for-the-badge)
  ![Python](https://img.shields.io/badge/python-3.8+-blue.svg?style=for-the-badge&logo=python&logoColor=white)
  ![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
  ![Vanilla JS](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
</div>

---

## 📖 What is NarrativeOS?
Built originally to circumvent complex anti-scraping measures on translation sites, NarrativeOS gives you **absolute control** over your novel archiving experience. It seamlessly bridges the gap between web content and beautifully formatted eBooks. 

With a robust Python backend and a highly responsive Vanilla JavaScript frontend, it transforms raw web text into professional, structured EPUB files in seconds.

---

## 🚀 What's New in v1.2.061926 (Security Update)
NarrativeOS has been massively overhauled to provide enterprise-grade security, extreme stability, and an upgraded user interface.

### 🛡️ Uncompromised Security
- **Dynamic API Session Tokens**: Implemented a robust `X-API-Key` authentication system to completely lock down local backend endpoints against unauthorized access.
- **SSRF Mitigation**: Added strict IP validation (`is_safe_url`) to block unauthorized internal network requests during automated image downloads.
- **Enhanced Path Traversal Protection**: Hardened backend security to completely block malicious file access requests (`..`, `:` validation).
- **CORS Lockdowns**: Restrictive Cross-Origin Resource Sharing applied to ensure only authorized local interfaces can communicate with the API.
- **ReDoS Prevention**: Mitigated severe Regex Denial of Service vulnerabilities in the Table of Contents extraction logic.

### ✨ UI & Experience Upgrades
- **Modern Typography**: Fully migrated UI typography to the beautiful, highly readable **Inter** font family.
- **Light Theme Support**: Added a brand new `light-clean` aesthetic theme for users who prefer brighter interfaces.
- **Dirty State Protection**: Integrated an unsaved-changes watcher to prevent accidental data loss when editing Markdown or closing the browser tab.
- **Icon Rail & Detail Panel**: Replaced the basic sidebar with a sleek Flexbox icon rail and a collapsible library tree.

### ⚙️ Backend Enhancements
- **Logging Overhaul**: Replaced rudimentary log writing with Python's robust `RotatingFileHandler`, eliminating file-locking race conditions and ensuring system stability.
- **Modular Pipeline Engine**: Massive refactoring of `build_novel.py` into highly testable, modular functions for metadata parsing and manifest generation.
- **Thread Safety**: Implemented `threading.Lock` fixes during simultaneous markdown file saving to prevent data corruption.

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
* **Premium Styling Elements**: Automatically supports Drop Caps, Scene Breaks (`***`), Character Thought Boxes, Game UI/Status Windows, and Full-Page Image Isolation.
* **Image Optimization**: Automatically compresses massive PNGs and JPEGs into lightweight WebP formats to keep file size minimal.

---

## 🛠️ Tech Stack
* **Backend**: Python 3, FastAPI, Uvicorn, BeautifulSoup4
* **Frontend**: HTML5, Vanilla JavaScript, CSS3
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
