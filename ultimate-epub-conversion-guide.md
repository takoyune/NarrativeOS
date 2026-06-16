# The Ultimate Guide to Converting Text, Images, and Documents into an EPUB Ebook

---

## Table of Contents

- [What is an EPUB File?](#what-is-an-epub-file)
- [Core EPUB Concepts Every Converter Must Understand](#core-epub-concepts-every-converter-must-understand)
- [Tools You Will Need](#tools-you-will-need)
- [Part 1: Converting Text and Documents to EPUB](#part-1-converting-text-and-documents-to-epub)
  - [1A: Converting Plain Text (.txt) to EPUB](#1a-converting-plain-text-txt-to-epub)
  - [1B: Converting Microsoft Word (.docx) to EPUB](#1b-converting-microsoft-word-docx-to-epub)
  - [1C: Converting Markdown (.md) to EPUB](#1c-converting-markdown-md-to-epub)
- [Part 2: Converting Images and Photos to EPUB](#part-2-converting-images-and-photos-to-epub)
  - [2A: Understanding Reflowable vs Fixed-Layout EPUB](#2a-understanding-reflowable-vs-fixed-layout-epub)
  - [2B: Converting a Set of Images into a Reflowable EPUB](#2b-converting-a-set-of-images-into-a-reflowable-epub)
  - [2C: Converting Scanned Pages or Comic Panels into a Fixed-Layout EPUB](#2c-converting-scanned-pages-or-comic-panels-into-a-fixed-layout-epub)
- [Part 3: Mixed Media — Text and Images Together](#part-3-mixed-media--text-and-images-together)
- [Part 4: Manual EPUB Assembly from Scratch](#part-4-manual-epub-assembly-from-scratch)
- [Part 5: Metadata, Styling, and Polishing](#part-5-metadata-styling-and-polishing)
- [Part 6: Validation and Testing](#part-6-validation-and-testing)
- [Quick Reference — Programmatic Pipeline Summary](#quick-reference--programmatic-pipeline-summary)
- [Troubleshooting Common Errors](#troubleshooting-common-errors)

---

## What is an EPUB File?

An EPUB file is not a single document. It is a **ZIP archive** with the `.epub` file extension. Inside that ZIP archive is a structured collection of files that includes:

- **XHTML files** — the actual text content, formatted as web pages
- **CSS files** — the visual styling rules (fonts, spacing, margins)
- **Image files** — JPG, PNG, GIF, SVG, or WebP assets
- **XML metadata files** — information about the book (title, author, language, cover)
- **A navigation file** — the table of contents
- **A manifest file** — a list of every file inside the EPUB

When a reading device or app (like Kindle, Apple Books, or Kobo) opens an EPUB, it unzips the package, reads the metadata, and renders the XHTML content using the CSS styles — exactly like a web browser renders a website.

> **Key Insight for Automation:** Because EPUB is just a structured ZIP file, any programming language that can write text files and ZIP them can create a valid EPUB from scratch.

---

## Core EPUB Concepts Every Converter Must Understand

### The OPF Package Document

Every EPUB must contain one `.opf` file (Open Packaging Format). This is the heart of the EPUB. It contains three critical sections:

- **`<metadata>`** — Title, author, language, unique identifier, publication date
- **`<manifest>`** — A list of every file in the EPUB, each with a unique `id`, an `href` (file path), and a `media-type`
- **`<spine>`** — The reading order. This tells the reading app which XHTML files to show and in what sequence.

### The NCX / Navigation Document

- **EPUB 2** uses a file called `toc.ncx` for the table of contents.
- **EPUB 3** uses a file called `nav.xhtml` for the table of contents. EPUB 3 is the current standard and is preferred.
- The navigation document lists chapter titles and links them to their corresponding XHTML files.

### The Container File

The file located at `META-INF/container.xml` is always required. It is the very first file a reading app looks at. It simply tells the app where to find the `.opf` file.

### XHTML Content Documents

Every chapter or section of content in an EPUB must be a valid XHTML file. XHTML is stricter than regular HTML — all tags must be properly closed, all attributes must be quoted, and the file must begin with a proper XML declaration and DOCTYPE.

### Media Types Reference

| File Type | Media Type String |
|---|---|
| XHTML content | `application/xhtml+xml` |
| CSS stylesheet | `text/css` |
| JPEG image | `image/jpeg` |
| PNG image | `image/png` |
| GIF image | `image/gif` |
| SVG image | `image/svg+xml` |
| OPF package | `application/oebps-package+xml` |
| NCX (EPUB 2) | `application/x-dtbncx+xml` |

---

## Tools You Will Need

### For Beginners (Graphical Interface)

- **Calibre** — Free, open-source ebook manager and converter. Available at calibre-ebook.com. Handles most conversion tasks automatically. Best for quick conversions.
- **Sigil** — Free, open-source EPUB editor. Available at sigil-ebook.com. Lets you edit the raw XHTML, CSS, and metadata of an EPUB directly. Best for fine-tuning and manual assembly.
- **Pandoc** — Free command-line document converter. Available at pandoc.org. Extremely powerful for converting Markdown, DOCX, HTML, and other formats to EPUB. Best for automation and scripting.

### For Developers and Automation

- **Pandoc** (command-line) — The gold standard for programmatic document conversion.
- **Python with the `ebooklib` library** — `pip install EbookLib`. Allows full programmatic creation and manipulation of EPUB files in Python.
- **Python with `Pillow` library** — `pip install Pillow`. For image processing, resizing, and format conversion before embedding in EPUB.
- **EPUBCheck** — The official EPUB validation tool from the W3C/IDPF. Use it to verify that any EPUB you create is valid and will work on reading devices.

---

## Part 1: Converting Text and Documents to EPUB

---

### 1A: Converting Plain Text (.txt) to EPUB

#### The Challenge

Plain text files have no formatting information. There are no headings, no bold text, no chapter markers — only raw characters and line breaks. The conversion process must make intelligent decisions about structure.

#### Step-by-Step Pipeline

**Step 1 — Input Analysis**
Open the `.txt` file and examine its structure. Look for:
- Blank lines that separate paragraphs
- Lines that appear to be chapter titles (short lines in ALL CAPS, or lines preceded and followed by blank lines)
- Any consistent patterns like `Chapter 1` or `***` section breaks

**Step 2 — Structural Parsing**
Decide on a parsing strategy. The most common approach:
- A line followed by two blank lines is likely a chapter heading.
- A single blank line between text blocks marks a paragraph break.
- Lines with no blank line separation are part of the same paragraph.

**Step 3 — XHTML Generation**
Convert the parsed structure into XHTML. Each paragraph becomes a `<p>` tag. Each detected heading becomes an `<h1>` or `<h2>` tag. Each chapter's content becomes a separate `.xhtml` file.

**Step 4 — CSS Styling**
Create a simple stylesheet that defines paragraph indentation, line height, font size, and margins.

**Step 5 — Package and Metadata**
Create the `.opf` file, the `nav.xhtml`, and the `container.xml`. Set the title, author, and language in the metadata.

**Step 6 — ZIP and Rename**
Compress all files into a ZIP archive. Rename the `.zip` extension to `.epub`. The `mimetype` file must be the very first file in the ZIP and must not be compressed.

**Step 7 — Validate**
Run EPUBCheck on the output file to confirm it is valid.

#### Using Calibre (Beginner Method)

1. Open Calibre.
2. Click **Add Books** and select your `.txt` file.
3. Select the book in the library, then click **Convert Books**.
4. In the conversion dialog, set **Output Format** to `EPUB` in the top-right dropdown.
5. Click the **Look & Feel** section on the left. Set paragraph formatting preferences.
6. Click the **Metadata** section. Enter the title and author name.
7. Click **OK** and wait for conversion to complete.
8. Right-click the book in Calibre and select **Open containing folder** to find the `.epub` file.

#### Using Pandoc (Developer Method)

```
pandoc input.txt -o output.epub --metadata title="My Book" --metadata author="Author Name" --toc
```

> **AI Coding Note:** When automating `.txt` to EPUB conversion, the most important step is the paragraph and heading detection algorithm. A reliable heuristic is: if a line is fewer than 60 characters long and is surrounded by blank lines, classify it as a heading. All other non-empty lines grouped between blank lines form a single paragraph. Process the entire file into a list of `(type, content)` tuples before generating any XHTML.

---

### 1B: Converting Microsoft Word (.docx) to EPUB

#### The Challenge

A `.docx` file is itself a ZIP archive containing XML. The content lives in a file called `word/document.xml`. Word documents use named styles (like `Heading 1`, `Heading 2`, `Normal`) to mark up structure. The conversion process must map these Word styles to the correct HTML elements.

#### Step-by-Step Pipeline

**Step 1 — Input Extraction**
Unzip the `.docx` file and read `word/document.xml`. Parse the XML to extract paragraphs (`<w:p>` elements) and their associated style names (`<w:pStyle w:val="..."/>`).

**Step 2 — Style Mapping**
Create a mapping table:

- Word style `Heading 1` → HTML `<h1>`
- Word style `Heading 2` → HTML `<h2>`
- Word style `Heading 3` → HTML `<h3>`
- Word style `Normal` or `Body Text` → HTML `<p>`
- Word inline style `Bold` (`<w:b/>`) → HTML `<strong>`
- Word inline style `Italic` (`<w:i/>`) → HTML `<em>`

**Step 3 — Image Extraction**
Images in a `.docx` are stored in the `word/media/` folder. The relationship between an image reference in the XML and the actual file is defined in `word/_rels/document.xml.rels`. Extract each image and save it to a folder for use in the EPUB.

**Step 4 — Chapter Splitting**
Use `Heading 1` paragraphs as chapter boundary markers. Every time a `Heading 1` is encountered, close the current XHTML file and start a new one.

**Step 5 — XHTML Generation**
Convert each extracted paragraph into its corresponding XHTML element. Insert image references using `<img>` tags pointing to the extracted image files.

**Step 6 — Package and Output**
Assemble the `.opf`, `nav.xhtml`, and `container.xml`. ZIP into `.epub`.

#### Using Calibre (Beginner Method)

1. Open Calibre and click **Add Books** to import your `.docx` file.
2. Select the book and click **Convert Books**.
3. Set the **Output Format** to `EPUB`.
4. Click **Structure Detection** on the left. In the **Detect chapters at** field, confirm it uses an XPath expression that targets `h1` or `h2` tags. Calibre auto-fills a sensible default.
5. Click **Table of Contents** on the left. Set the level of headings to use for the TOC.
6. Click the **Metadata** section and verify the title and author were imported correctly from the Word document.
7. Click **OK**.

#### Using Pandoc (Developer Method)

```
pandoc input.docx -o output.epub --toc --toc-depth=2 --epub-chapter-level=1
```

The `--epub-chapter-level=1` flag tells Pandoc to split the EPUB into separate files at each `Heading 1`.

> **AI Coding Note:** The `python-docx` library (`pip install python-docx`) can parse `.docx` files programmatically. Use `doc.paragraphs` to iterate over all paragraphs. Each paragraph has a `.style.name` property (e.g., `'Heading 1'`) and a `.runs` list for inline formatting. This is the recommended approach for building a custom `.docx`-to-EPUB pipeline in Python.

---

### 1C: Converting Markdown (.md) to EPUB

#### The Challenge

Markdown is the ideal input format for EPUB conversion because it already has explicit, unambiguous structural markers. A `#` is always an `h1`. A `##` is always an `h2`. Paragraphs are separated by blank lines. The mapping is direct and reliable.

#### Markdown to XHTML Mapping Reference

- `# Title` → `<h1>Title</h1>`
- `## Chapter` → `<h2>Chapter</h2>`
- `### Section` → `<h3>Section</h3>`
- A blank-line-separated block of text → `<p>text</p>`
- `**bold**` → `<strong>bold</strong>`
- `*italic*` → `<em>italic</em>`
- `![alt text](image.png)` → `<img src="image.png" alt="alt text"/>`
- `> blockquote` → `<blockquote><p>blockquote</p></blockquote>`
- `- item` → `<ul><li>item</li></ul>`
- `1. item` → `<ol><li>item</li></ol>`

#### Step-by-Step Pipeline

**Step 1 — Pre-process the Markdown**
Read the `.md` file. Identify all image references and collect the file paths so images can be copied into the EPUB package.

**Step 2 — Parse Markdown**
Use a Markdown parsing library to convert the Markdown AST (Abstract Syntax Tree) into a tree of HTML nodes. Do not output raw HTML at this step — work with the tree.

**Step 3 — Chapter Splitting**
Walk the parsed tree and split at every `h1` (or `h2`, depending on your chosen chapter level) node. Each split becomes a separate XHTML file.

**Step 4 — XHTML Serialization**
Serialize each chunk of the parsed tree into a valid XHTML document. Ensure the XHTML header and DOCTYPE declaration are correct.

**Step 5 — Package**
Assemble the full EPUB package with metadata from a YAML front matter block (if present at the top of the Markdown file) or from command-line arguments.

#### Using Pandoc (Recommended — Beginner and Developer)

For a single Markdown file:
```
pandoc input.md -o output.epub --toc --epub-cover-image=cover.jpg --metadata title="My Book"
```

For a book split across multiple Markdown files (one per chapter):
```
pandoc chapter1.md chapter2.md chapter3.md -o output.epub --toc
```

With a metadata YAML file:
```
pandoc input.md -o output.epub --metadata-file=metadata.yaml
```

A sample `metadata.yaml` file looks like this:
```
title: "My Ebook Title"
author: "Author Name"
language: en
rights: "Copyright 2025 Author Name"
```

#### Using Python with ebooklib (Developer Method)

```python
import markdown
from ebooklib import epub

md_content = open("input.md").read()
html_content = markdown.markdown(md_content)

book = epub.EpubBook()
book.set_title("My Book")
book.set_language("en")
book.add_author("Author Name")

chapter = epub.EpubHtml(title="Content", file_name="content.xhtml", lang="en")
chapter.content = f"<html><body>{html_content}</body></html>"

book.add_item(chapter)
book.add_item(epub.EpubNcx())
book.add_item(epub.EpubNav())
book.spine = ["nav", chapter]
epub.write_epub("output.epub", book)
```

> **AI Coding Note:** Pandoc is the most robust solution for Markdown-to-EPUB conversion and handles edge cases like footnotes, tables, and code blocks correctly. For custom pipelines, use a Markdown parser that exposes an AST (like `mistletoe` or `markdown-it-py` in Python, or `unified` / `remark` in JavaScript) rather than converting to HTML strings first. Operating on the AST gives you precise control over chapter splitting and image extraction.

---

## Part 2: Converting Images and Photos to EPUB

---

### 2A: Understanding Reflowable vs Fixed-Layout EPUB

This is the single most important decision when working with image-heavy content. Choose the wrong layout type and the reading experience will be broken.

#### Reflowable Layout EPUB

**What it is:** The default EPUB format. Content flows and reflows like a web page. Text wraps based on screen size. Font sizes can be changed by the reader. Images are embedded inline within the text and scale to fit the screen.

**When to use it:**
- Novels or text books that contain occasional photographs or illustrations
- Documents where the image is supplementary to the text
- Cases where you want the reader to be able to adjust font size

**How images work in reflowable EPUB:**
Each image is embedded in an XHTML file using a standard `<img>` tag. The CSS controls the maximum width (usually `max-width: 100%`) so the image scales down on small screens without overflowing.

**Example XHTML for an inline image in reflowable EPUB:**
```xml
<p>Below is a diagram of the water cycle.</p>
<img src="../images/water-cycle.png" alt="Diagram of the water cycle" style="max-width: 100%;"/>
<p>As shown above, water evaporates from the ocean.</p>
```

#### Fixed-Layout EPUB (FXL)

**What it is:** A special EPUB mode where every page is a fixed-size canvas, like a PDF. Content does not reflow. The exact position of every element is preserved. Reading apps do not allow font size changes.

**When to use it:**
- Comic books and graphic novels where panel layout is part of the art
- Children's picture books where text and illustration are tightly coupled
- Cookbooks or art books with full-page photographs
- Scanned book pages where the original layout must be preserved exactly
- Any content where the visual design of the page is itself meaningful

**How images work in fixed-layout EPUB:**
Each page is an XHTML file. The page has a declared pixel width and height (e.g., 1200 x 1920 pixels). The image for that page fills the entire viewport. The reading app displays the page at whatever zoom level fits the screen, but never reflows the content.

**Key metadata for fixed-layout EPUB (goes in the `.opf` file):**
```xml
<meta property="rendition:layout">pre-paginated</meta>
<meta property="rendition:orientation">auto</meta>
<meta property="rendition:spread">auto</meta>
```

**Key metadata for each XHTML content page in a fixed-layout EPUB:**
Each XHTML file must declare its viewport size in the `<head>`:
```xml
<meta name="viewport" content="width=1200, height=1920"/>
```

---

### 2B: Converting a Set of Images into a Reflowable EPUB

**Use case:** You have a collection of JPG or PNG images (photos, illustrations, diagrams) that you want to embed into an ebook alongside descriptive text, with a normal readable layout.

#### Step-by-Step Pipeline

**Step 1 — Prepare and Organize Your Images**
Collect all images into a single folder. Name them in the order you want them to appear (e.g., `image-001.jpg`, `image-002.jpg`). Recommended image formats are JPEG for photos and PNG for diagrams with text.

**Step 2 — Resize Images for Screen**
Images from cameras are often very large (4000 x 3000 pixels, several megabytes). Large images make the EPUB file bloated and slow to load. Resize images to a maximum width of 1600 pixels for standard ebooks, or 2560 pixels for high-resolution tablet ebooks. Compress JPEGs to 85% quality to balance size and clarity.

Using Python with Pillow to batch resize:
```python
from PIL import Image
import os

input_folder = "raw_images"
output_folder = "resized_images"
max_width = 1600

os.makedirs(output_folder, exist_ok=True)
for filename in sorted(os.listdir(input_folder)):
    if filename.lower().endswith((".jpg", ".jpeg", ".png")):
        img = Image.open(os.path.join(input_folder, filename))
        if img.width > max_width:
            ratio = max_width / img.width
            new_height = int(img.height * ratio)
            img = img.resize((max_width, new_height), Image.LANCZOS)
        img.save(os.path.join(output_folder, filename), optimize=True, quality=85)
```

**Step 3 — Create an XHTML File for Each Image**
For a simple image-per-page reflowable EPUB, create one XHTML file per image. Each file contains the image tag and an optional caption paragraph.

Template for a single image page:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
  <title>Image Page</title>
  <link rel="stylesheet" type="text/css" href="../css/style.css"/>
</head>
<body>
  <div class="image-page">
    <img src="../images/image-001.jpg" alt="Description of image 001"/>
    <p class="caption">Caption for image 001</p>
  </div>
</body>
</html>
```

**Step 4 — Create a CSS Stylesheet**
```css
body {
  margin: 0;
  padding: 0.5em;
  font-family: Georgia, serif;
  font-size: 1em;
  line-height: 1.6;
}

.image-page {
  text-align: center;
  margin-bottom: 2em;
}

.image-page img {
  max-width: 100%;
  height: auto;
  display: block;
  margin: 0 auto;
}

.caption {
  font-style: italic;
  font-size: 0.85em;
  color: #555;
  margin-top: 0.5em;
}
```

**Step 5 — Assemble the EPUB Package**
Create the folder structure, add all XHTML and image files, write the `.opf` manifest (listing every image file with its correct media type), write the `nav.xhtml`, and zip into `.epub`.

**Step 6 — Validate**

Run EPUBCheck.

---

### 2C: Converting Scanned Pages or Comic Panels into a Fixed-Layout EPUB

**Use case:** You have a set of scanned book pages or comic panels — one image per page — and you need each image to display as a full, unchangeable page in the ebook, exactly as scanned.

#### Step-by-Step Pipeline

**Step 1 — Prepare Images**
Scan at a minimum resolution of 150 DPI for text-heavy pages, or 200–300 DPI for image-heavy pages. Save as JPEG (for photos/color art) or PNG (for black-and-white line art). Clean up scanned images: deskew, crop borders, and adjust brightness/contrast if needed.

Determine the pixel dimensions of your images. All pages should ideally be the same size. A common size for a portrait comic page is 1600 x 2560 pixels.

**Step 2 — Create a Fixed-Layout XHTML Template for Each Page**
Every scanned page becomes one XHTML file. The XHTML declares its viewport to match the image dimensions exactly.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
  <title>Page 1</title>
  <meta name="viewport" content="width=1600, height=2560"/>
  <style type="text/css">
    html, body {
      margin: 0;
      padding: 0;
      width: 1600px;
      height: 2560px;
      overflow: hidden;
    }
    img {
      width: 1600px;
      height: 2560px;
      display: block;
    }
  </style>
</head>
<body>
  <img src="../images/page-001.jpg" alt="Page 1"/>
</body>
</html>
```

**Step 3 — Write the Fixed-Layout OPF File**
The `.opf` file for a fixed-layout EPUB must include the `rendition` metadata properties in its `<metadata>` section. This tells reading apps to use fixed-layout mode.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>My Comic Book</dc:title>
    <dc:creator>Author Name</dc:creator>
    <dc:language>en</dc:language>
    <dc:identifier id="bookid">urn:uuid:UNIQUE-UUID-HERE</dc:identifier>
    <meta property="rendition:layout">pre-paginated</meta>
    <meta property="rendition:orientation">auto</meta>
    <meta property="rendition:spread">auto</meta>
  </metadata>
  <manifest>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
    <item id="page001" href="xhtml/page-001.xhtml" media-type="application/xhtml+xml" properties="rendition:layout-pre-paginated"/>
    <item id="img001" href="images/page-001.jpg" media-type="image/jpeg"/>
  </manifest>
  <spine>
    <itemref idref="page001"/>
  </spine>
</package>
```

**Step 4 — Handle Cover Image**
The cover image is listed in the OPF manifest with the `properties="cover-image"` attribute:
```xml
<item id="cover-img" href="images/cover.jpg" media-type="image/jpeg" properties="cover-image"/>
```

**Step 5 — Create Navigation File**
Even fixed-layout EPUBs need a `nav.xhtml`. It can be minimal but must exist.

**Step 6 — Compile and Validate**
Zip all files following the correct EPUB folder structure and rename to `.epub`. Run EPUBCheck.

> **AI Coding Note:** When automating fixed-layout EPUB creation from a folder of images, the key operations are: (1) sort image files by filename to determine reading order, (2) detect image dimensions using an image processing library like Pillow, (3) use those dimensions as the viewport value in each generated XHTML file, (4) generate sequential OPF `<item>` and `<itemref>` entries for each page, (5) generate NCX/nav entries with page numbers as labels.

---

## Part 3: Mixed Media — Text and Images Together

**Use case:** You have a document where chapters contain both body text and embedded images — like a travel memoir with photos, a technical manual with diagrams, or a recipe book with step-by-step pictures.

### Recommended Approach

Use **reflowable layout** for mixed media content. Fixed-layout is only necessary when pixel-perfect page design is essential.

### Step-by-Step Workflow

**Step 1 — Organize Source Files**
Create a project folder with subfolders:
```
my-ebook/
  text/
    chapter-01.md
    chapter-02.md
  images/
    photo-01.jpg
    diagram-01.png
  metadata.yaml
```

**Step 2 — Reference Images in Text Files**
In your Markdown or DOCX source files, reference images using relative paths or filenames. Pandoc and most converters will find and package them automatically.

In Markdown:
```markdown
## Chapter 1: The Journey Begins

We arrived at dawn. The harbor was quiet.

![The harbor at dawn](../images/photo-01.jpg)

The boat was smaller than I had imagined.
```

**Step 3 — Define Image Styling**
In your CSS, set images to be responsive by default:
```css
img {
  max-width: 100%;
  height: auto;
  display: block;
  margin: 1em auto;
}

figure {
  margin: 1.5em 0;
  text-align: center;
}

figcaption {
  font-style: italic;
  font-size: 0.85em;
  margin-top: 0.4em;
  color: #666;
}
```

**Step 4 — Convert Using Pandoc**
Pandoc handles mixed content natively. Run:
```
pandoc chapter-01.md chapter-02.md -o output.epub --toc --metadata-file=metadata.yaml --css=style.css --epub-chapter-level=1
```

Pandoc will automatically:
- Find all referenced images and embed them in the EPUB
- Convert Markdown image references to XHTML `<img>` tags
- Create a separate XHTML file for each chapter

**Step 5 — Fine-Tune in Sigil**
Open the output `.epub` in Sigil to:
- Inspect and adjust the generated XHTML
- Add or modify CSS rules
- Check that images are rendering correctly at different simulated screen sizes

### Handling Images That Are Part of the Flow vs. Full-Page Images

- **Inline image** (between paragraphs): Use a standard `<img>` tag inside a `<p>` or `<figure>` element.
- **Full-page image** (a photograph that deserves its own page): Wrap the image in a `<div>` with `page-break-before` and `page-break-after` CSS properties:
```css
.full-page-image {
  page-break-before: always;
  page-break-after: always;
  text-align: center;
}
```

> **AI Coding Note:** The key challenge in mixed media conversion is resolving image paths. When processing source files, build a manifest of all referenced images (parsing `<img>` src attributes in HTML, `![...](path)` patterns in Markdown, or `<w:drawing>` elements in DOCX XML). Copy all referenced images to a normalized `images/` folder within the EPUB package and update all references to use the new relative paths before generating the final XHTML.

---

## Part 4: Manual EPUB Assembly from Scratch

This section describes the exact folder structure and file contents needed to build a valid EPUB 3 from scratch without any conversion tools.

### Required Folder Structure

```
my-epub/
  mimetype
  META-INF/
    container.xml
  OEBPS/
    content.opf
    nav.xhtml
    css/
      style.css
    xhtml/
      chapter-01.xhtml
      chapter-02.xhtml
    images/
      cover.jpg
      image-01.png
```

### File 1: `mimetype`

This file must be the very first file added to the ZIP. It must not be compressed. It has no file extension and contains exactly this text (no newline at the end):
```
application/epub+zip
```

### File 2: `META-INF/container.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
```

### File 3: `OEBPS/content.opf`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">

  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>My Ebook Title</dc:title>
    <dc:creator>Author Name</dc:creator>
    <dc:language>en</dc:language>
    <dc:identifier id="bookid">urn:uuid:12345678-1234-1234-1234-123456789012</dc:identifier>
    <meta property="dcterms:modified">2025-01-01T00:00:00Z</meta>
  </metadata>

  <manifest>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
    <item id="css" href="css/style.css" media-type="text/css"/>
    <item id="cover-img" href="images/cover.jpg" media-type="image/jpeg" properties="cover-image"/>
    <item id="ch01" href="xhtml/chapter-01.xhtml" media-type="application/xhtml+xml"/>
    <item id="ch02" href="xhtml/chapter-02.xhtml" media-type="application/xhtml+xml"/>
    <item id="img01" href="images/image-01.png" media-type="image/png"/>
  </manifest>

  <spine>
    <itemref idref="ch01"/>
    <itemref idref="ch02"/>
  </spine>

</package>
```

### File 4: `OEBPS/nav.xhtml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="en">
<head>
  <title>Table of Contents</title>
</head>
<body>
  <nav epub:type="toc" id="toc">
    <h1>Table of Contents</h1>
    <ol>
      <li><a href="xhtml/chapter-01.xhtml">Chapter 1: The Beginning</a></li>
      <li><a href="xhtml/chapter-02.xhtml">Chapter 2: The Middle</a></li>
    </ol>
  </nav>
</body>
</html>
```

### File 5: A Sample Chapter XHTML File

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
  <title>Chapter 1</title>
  <link rel="stylesheet" type="text/css" href="../css/style.css"/>
</head>
<body>
  <h1>Chapter 1: The Beginning</h1>
  <p>This is the first paragraph of chapter one.</p>
  <p>This is the second paragraph.</p>
  <figure>
    <img src="../images/image-01.png" alt="Description of the image"/>
    <figcaption>Caption for the image.</figcaption>
  </figure>
</body>
</html>
```

### Creating the ZIP / EPUB Archive

**Using Python to create a valid EPUB ZIP:**
```python
import zipfile
import os

def create_epub(source_folder, output_path):
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # mimetype MUST be first and MUST be uncompressed (ZIP_STORED)
        zf.write(
            os.path.join(source_folder, "mimetype"),
            "mimetype",
            compress_type=zipfile.ZIP_STORED
        )
        # Add all other files
        for root, dirs, files in os.walk(source_folder):
            for file in files:
                if file == "mimetype":
                    continue
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, source_folder)
                zf.write(file_path, arcname)

create_epub("my-epub", "output.epub")
```

> **AI Coding Note:** The `mimetype` file rule is absolute. EPUBCheck will fail any EPUB where `mimetype` is not the first entry in the ZIP with `ZIP_STORED` compression. All other files may use `ZIP_DEFLATED`. This is the most common mistake made by programmatic EPUB generators.

---

## Part 5: Metadata, Styling, and Polishing

### Essential Metadata Fields

All of these belong inside the `<metadata>` section of the `.opf` file.

- **`<dc:title>`** — The full title of the ebook. Required.
- **`<dc:creator>`** — The author's name. Use `opf:role="aut"` to specify the role.
- **`<dc:language>`** — The language code. Use ISO 639-1 codes: `en` for English, `fr` for French, `de` for German.
- **`<dc:identifier>`** — A unique ID for this book. Can be a UUID, ISBN, or any unique string.
- **`<dc:publisher>`** — The publisher name. Optional but recommended.
- **`<dc:description>`** — A blurb or summary. Optional but useful for ebook stores.
- **`<dc:rights>`** — Copyright statement. Optional.
- **`<meta property="dcterms:modified">`** — The last modification date in ISO 8601 format. Required for EPUB 3.

### Professional CSS Styling Template

Save this as `css/style.css`:
```css
/* Base page settings */
body {
  font-family: Georgia, "Times New Roman", serif;
  font-size: 1em;
  line-height: 1.7;
  margin: 0;
  padding: 0 1em;
  color: #1a1a1a;
  background-color: transparent;
}

/* Headings */
h1 {
  font-size: 1.8em;
  font-weight: bold;
  text-align: center;
  margin-top: 2em;
  margin-bottom: 1em;
  page-break-before: always;
}

h2 {
  font-size: 1.4em;
  font-weight: bold;
  margin-top: 1.5em;
  margin-bottom: 0.5em;
}

h3 {
  font-size: 1.15em;
  font-weight: bold;
  margin-top: 1.2em;
  margin-bottom: 0.3em;
}

/* Body paragraphs */
p {
  margin: 0;
  padding: 0;
  text-indent: 1.5em;
}

/* First paragraph after a heading — no indent */
h1 + p, h2 + p, h3 + p {
  text-indent: 0;
}

/* Block quote */
blockquote {
  margin: 1em 2em;
  font-style: italic;
  border-left: 3px solid #ccc;
  padding-left: 1em;
}

/* Images */
img {
  max-width: 100%;
  height: auto;
  display: block;
  margin: 1em auto;
}

figure {
  margin: 1.5em 0;
  text-align: center;
}

figcaption {
  font-style: italic;
  font-size: 0.85em;
  color: #666;
  margin-top: 0.4em;
}

/* Cover page */
.cover-page {
  text-align: center;
  page-break-after: always;
}

.cover-page img {
  max-width: 100%;
  max-height: 90vh;
}
```

### Adding a Cover Image

The cover image is handled in two places:

**In the OPF manifest**, mark the cover image file with the `cover-image` property:
```xml
<item id="cover-img" href="images/cover.jpg" media-type="image/jpeg" properties="cover-image"/>
```

**Optionally**, create a dedicated cover XHTML page as the first item in the spine:
```xml
<body>
  <div class="cover-page">
    <img src="../images/cover.jpg" alt="Book Cover"/>
  </div>
</body>
```

---

## Part 6: Validation and Testing

### Running EPUBCheck

EPUBCheck is a Java application. Download the `.jar` file from the official GitHub repository at github.com/w3c/epubcheck.

Run it from the command line:
```
java -jar epubcheck.jar output.epub
```

A valid EPUB will output:
```
No errors or warnings detected.
```

Any errors must be fixed before distributing the EPUB. Common error types are listed in the troubleshooting section below.

### Testing on Reading Devices and Apps

Always test your EPUB in at least two different reading environments:

- **Calibre's built-in viewer** (free, desktop, cross-platform) — Good for quick previews.
- **Apple Books** (macOS/iOS) — A strict EPUB renderer. If it works here, it works everywhere.
- **Kobo** desktop or device — Tests reflowable layout rendering.
- **Adobe Digital Editions** (free) — Good for testing EPUB 2 compatibility.
- **Firefox or Chrome browser** with the EPUBReader extension — Useful for debugging.

### Checklist Before Distribution

- The EPUB passes EPUBCheck with zero errors and zero warnings.
- The cover image displays correctly.
- The table of contents is complete and all links work.
- Images load and display at appropriate sizes.
- Chapter headings are correct and hierarchical.
- Text is readable at default font sizes.
- No missing fonts or broken character encoding.
- Metadata includes title, author, language, and unique identifier.

---

## Quick Reference — Programmatic Pipeline Summary

### Pipeline A: Plain Text (.txt) → EPUB

```
Input .txt file
  → Read file as string
  → Detect paragraphs (split on double newlines)
  → Detect headings (short lines surrounded by blank lines)
  → Split into chapters at each heading
  → Generate one XHTML file per chapter
  → Generate CSS stylesheet
  → Generate OPF with manifest listing all XHTML files
  → Generate nav.xhtml with TOC entries
  → Generate container.xml
  → Write mimetype file
  → ZIP all files (mimetype first, uncompressed)
  → Rename .zip to .epub
  → Run EPUBCheck
```

### Pipeline B: Word Document (.docx) → EPUB

```
Input .docx file
  → Unzip .docx archive
  → Parse word/document.xml
  → Extract paragraphs with style names (Heading 1, Normal, etc.)
  → Map Word styles to HTML elements (h1, h2, p, strong, em)
  → Extract images from word/media/ folder
  → Resolve image relationships via word/_rels/document.xml.rels
  → Split content into chapters at each Heading 1
  → Generate one XHTML file per chapter with embedded image references
  → Copy images to EPUB images/ folder
  → Generate OPF with all files in manifest (including each image)
  → Generate nav.xhtml
  → Generate container.xml
  → ZIP and rename to .epub
  → Run EPUBCheck
```

### Pipeline C: Markdown (.md) → EPUB

```
Input .md file(s)
  → Parse YAML front matter for metadata (title, author, language)
  → Parse Markdown into AST
  → Walk AST, extract image references, collect image file paths
  → Split AST at h1 nodes to define chapter boundaries
  → Serialize each chapter sub-AST into a valid XHTML document
  → Copy referenced images to EPUB images/ folder
  → Update all image src paths to relative EPUB paths
  → Generate OPF with manifest
  → Generate nav.xhtml from h1 headings list
  → Generate container.xml
  → ZIP and rename to .epub
  → Run EPUBCheck
```

### Pipeline D: Images Only → Fixed-Layout EPUB

```
Input folder of images (JPG/PNG)
  → Sort images by filename to determine reading order
  → Detect pixel dimensions of each image (width, height)
  → Resize images if necessary (max 2560px on long edge)
  → For each image:
      → Generate XHTML page file with viewport matching image dimensions
      → Add image as full-page <img> tag
  → Generate fixed-layout OPF with rendition metadata
  → Generate nav.xhtml with page number labels
  → Generate container.xml
  → ZIP and rename to .epub
  → Run EPUBCheck
```

### Pipeline E: Mixed Media (Text + Images) → EPUB

```
Input: text files (.md or .docx) + image files folder
  → Parse text files, extract all image references
  → Resolve image file paths (relative to source file locations)
  → Resize and optimize images for screen
  → Convert text to XHTML chapters (see Pipeline B or C)
  → Inline image references in XHTML as <img> or <figure> tags
  → Copy all images to EPUB images/ folder
  → Update all image paths in XHTML to relative EPUB paths
  → Generate OPF manifest listing all XHTML and image files
  → Generate nav.xhtml
  → Generate container.xml
  → ZIP and rename to .epub
  → Run EPUBCheck
```

---

## Troubleshooting Common Errors

### EPUBCheck Error: `mimetype entry is missing or not the first in archive`

**Cause:** The `mimetype` file was either not added first, or was added with compression.

**Fix:** Recreate the ZIP archive. Add `mimetype` as the first entry using `ZIP_STORED` (no compression). All other files may use `ZIP_DEFLATED`.

---

### EPUBCheck Error: `element "img" missing required attribute "alt"`

**Cause:** One or more `<img>` tags in your XHTML files do not have an `alt` attribute.

**Fix:** Add an `alt` attribute to every `<img>` tag. For decorative images with no informational value, use `alt=""`.

---

### EPUBCheck Error: `referenced resource ... could not be found in the EPUB`

**Cause:** The OPF manifest references a file (image, CSS, or XHTML) that does not exist at the specified path inside the EPUB ZIP.

**Fix:** Check all file paths in the manifest for typos. Check that the file was actually included when creating the ZIP. File paths in EPUB are case-sensitive.

---

### EPUBCheck Error: `item … not listed in the manifest`

**Cause:** A file exists inside the EPUB ZIP but is not listed in the OPF manifest.

**Fix:** Add an `<item>` entry for the file in the OPF `<manifest>` section, with the correct `id`, `href`, and `media-type`.

---

### EPUBCheck Error: `'href' attribute of item … is not a valid URI`

**Cause:** A file path in the manifest contains spaces or special characters that are not valid in URIs.

**Fix:** Rename all files to use only lowercase letters, numbers, hyphens, and underscores. Replace spaces with hyphens. Update all references.

---

### Images Not Displaying on Kindle

**Cause:** Amazon's Kindle format (MOBI/AZW3) has stricter image requirements than standard EPUB. Also, Kindle uses its own format derived from EPUB.

**Fix:** Ensure images are JPEG or PNG format. Ensure JPEG images use the standard RGB color space (not CMYK). Keep individual image file sizes under 5MB. Total EPUB image payload should stay under 50MB for Kindle Direct Publishing.

---

### Text Appears Without Indentation or Spacing

**Cause:** The CSS stylesheet is not being applied. Either the CSS file is missing, the path in the `<link>` tag is wrong, or the CSS file is not listed in the OPF manifest.

**Fix:** Verify the CSS file exists in the EPUB ZIP. Verify the `href` path in the OPF manifest `<item>` entry. Verify the `<link rel="stylesheet">` tag in each XHTML file uses the correct relative path to the CSS file.

---

### Table of Contents Does Not Appear

**Cause:** The `nav.xhtml` file is missing the `properties="nav"` attribute on its `<item>` entry in the OPF manifest, or the `<nav epub:type="toc">` element is missing or malformed.

**Fix:** Ensure the nav item in the manifest is:
```xml
<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
```

Ensure the `nav.xhtml` body contains a `<nav epub:type="toc">` element with a nested `<ol>` list of links.

---

*End of Guide*
