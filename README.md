# NarrativeOS

NarrativeOS is a comprehensive, local toolkit for managing, scraping, and compiling Light Novels into high-quality EPUB files. It features a blazing-fast FastAPI backend with a sleek, responsive vanilla JavaScript frontend.

## Features

- **Web → Markdown Scraper**: Automatically scrape chapters from popular translation sites, bypass premium protections (via HTML paste), and clean up formatting.
- **Markdown Editor**: A fully-featured, split-pane markdown editor with syntax highlighting, word wrap, and live preview.
- **Image Manager**: Built-in support for uploading, viewing, and organizing illustrations. Automatically converts images to compressed WebP/JPEG formats to keep EPUB sizes small.
- **EPUB Compiler**: A robust Python builder that converts Markdown files into perfectly formatted EPUBs with table of contents, cover pages, and CSS styling.
- **Smart Metadata**: Automatically carries over novel metadata (Author, Artist, Genres) between volumes.

## Getting Started

1. Install Python dependencies:
   ```bash
   pip install fastapi uvicorn beautifulsoup4 markdownify pillow
   ```
2. Run the local web server:
   ```bash
   run_web.bat
   ```
3. Open your browser to `http://localhost:8000` to access the NarrativeOS interface.

## Tech Stack

- **Backend**: Python 3, FastAPI, Uvicorn, BeautifulSoup4
- **Frontend**: HTML5, Vanilla JavaScript, CSS3
- **Compiler**: Python (Standard Library)
