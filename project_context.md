# NarrativeOS Project Context

## Purpose
NarrativeOS is a local EPUB authoring toolkit. It allows users to scrape chapters from web sources (via `scraper`), manage and edit Markdown files, handle image conversions, manage EPUB metadata, and finally compile the novel into a fully-packaged EPUB file.

## Architecture
- **Backend (`server.py`)**: A FastAPI web server that handles API endpoints (`/api/novels`, `/api/scrape`, `/api/build`, etc.). It manages file operations securely, ensuring no path traversal beyond `BASE_DIR`.
- **Builder (`build_novel.py`)**: A robust EPUB compiler that processes Markdown into XHTML, parses metadata, manages image compression/conversion (to WebP/JPEG), and calls `epub_builder.py` to assemble the EPUB standard files (`content.opf`, `toc.ncx`).
- **Frontend (`static/`)**: A vanilla HTML/JS/CSS application using a single-page architecture with multiple panels (`overview`, `scraper`, `editor`, `images`, `metadata`, `builder`). State is managed globally via `app.js`, and styling uses CSS variables for theming in `style.css`.
- **Task Runner (`tasks.py`)**: A Python-based CLI tool to start the server, check types, format code, and build EPUBs without using the web UI.

## Security Considerations
- **API Token**: A dynamic session-based token (`X-API-Key`) is required for all API operations, preventing unauthorized access if exposed over localhost.
- **SSRF Prevention**: URL fetching (like image downloads or web scraping) is validated via `is_safe_url()` to block DNS rebinding, loopbacks, and private IPs.
- **Path Validation**: All file operations utilize `safe_path()` which strictly enforces boundaries using Python's `Path.resolve()` and `is_relative_to()`.

## Future Improvements
- Implement a SQLite database to track novel metadata instead of reading the file system directly, for improved performance.
- Add support for converting EPUB to PDF via headless browser printing.
- Migrate the frontend to a component-based framework (React/Vue) if state complexity grows further.
