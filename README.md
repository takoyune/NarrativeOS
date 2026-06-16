# NarrativeOS

NarrativeOS is a comprehensive, local toolkit specifically engineered for managing, scraping, and compiling Light Novels into high-quality, professional EPUB files. It features a blazing-fast Python/FastAPI backend paired with a sleek, responsive vanilla JavaScript frontend. 

Built originally to circumvent complex anti-scraping measures on translation sites, NarrativeOS provides absolute control over your novel reading and archiving experience.

---

## 🌟 Key Features

### 🌐 Web → Markdown Scraper
- **Automated Scraping**: Just paste a URL, and NarrativeOS will fetch the chapter and convert it perfectly to clean Markdown.
- **Batch Processing**: Give it a list of URLs and it will process an entire volume in seconds.
- **Premium Bypass (HTML Paste)**: Encountered a paywall or a locked chapter? Open the chapter in your browser where you are logged in, copy the HTML source code, and paste it directly into NarrativeOS. It will bypass the lock and parse the content beautifully.
- **Advanced Image Recovery**: Built-in canvas decoding easily breaks through obfuscated images (like base64 canvases) used by modern translation sites to hide illustrations.

### ✏️ Premium Markdown Editor
- **Split-Pane View**: Write or edit in raw Markdown on the left while watching a real-time, styled HTML preview on the right.
- **Custom Syntax Highlighting**: NarrativeOS uses a custom-built highlighter tailored specifically for novel formatting, making it easy to spot character dialogue, thoughts, and UI boxes.
- **Auto-Saving & File Management**: Seamlessly rename, delete, or create new chapters directly within the editor interface.

### 📋 Smart Metadata Management
- **Intelligent Carry-Over**: When creating a new volume for an existing novel, NarrativeOS automatically copies the Author, Artist, Genres, and Translator from your previous volume—leaving only the Volume Number and Table of Contents blank for you to fill.
- **Primary Language Selection**: Set your primary title language (e.g., Japanese, English, Romaji) so your final EPUB looks exactly how you want it.

### 📦 Robust EPUB Compiler
- **Automated Book Assembly**: With the click of a button, NarrativeOS parses your Markdown files and metadata to generate a perfectly structured EPUB.
- **Premium Styling Elements**: The compiler automatically supports Drop Caps, Scene Breaks (`***`), Character Thought Boxes, Game UI/Status Windows, and Full-Page Image Isolation. (See `Styling_and_Tricks_Guide.md` for the full cheatsheet!)
- **Image Optimization**: Automatically compresses massive PNGs and JPEGs into lightweight WebP formats to keep your EPUB file size minimal without losing quality.

### ✅ Tested Websites
NarrativeOS's scraping engine and anti-obfuscation layers have been extensively tested and confirmed to work perfectly out-of-the-box with:
- `remusworld.wordpress.com`
- `kdtnovels.net`

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
To start the backend server and open the interface, run the provided batch script:
```bash
run_web.bat
```
*(Or manually run `python server.py`)*

### 3. Usage
Open your web browser and navigate to:
```
http://localhost:8000
```
- **Create a Novel**: Start by creating a Novel folder and then adding a Volume.
- **Scrape or Write**: Use the **Scraper** panel to fetch chapters from the web, or use the **Editor** panel to write them manually.
- **Add Metadata**: Use the **Metadata** panel to set your cover image and Table of Contents.
- **Build**: Go to the **Builder** panel and click "Build EPUB". Your finished book will appear right inside the volume folder!

---

## 🛠️ Tech Stack
- **Backend**: Python 3, FastAPI, Uvicorn, BeautifulSoup4
- **Frontend**: HTML5, Vanilla JavaScript, CSS3
- **Compiler Architecture**: Modular Python pipeline utilizing `zipfile`, `xml.etree.ElementTree`, and standard libraries.

## 📖 Custom Styling Guide
For a complete list of supported Markdown tricks (like `[UI]` boxes, `(thought)` boxes, and `(image)` splitters), please refer to the `Styling_and_Tricks_Guide.md` file included in this repository.
