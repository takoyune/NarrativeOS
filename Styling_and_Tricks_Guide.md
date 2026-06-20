# NarrativeOS Formatting & Tricks Guide (Master Reference)

Welcome to the definitive guide for styling and formatting novels in the NarrativeOS EPUB Compiler. This document outlines all standard markdown formatting, custom publishing tricks, and advanced workflow enhancements supported by the newest version of the toolkit.

Keep this reference handy whenever you're authoring or formatting a novel to ensure a premium, publisher-grade final EPUB.

---

## 1. Automated EPUB Enhancements

These features happen completely automatically during the EPUB compilation process. You do not need to do anything special to trigger them.

### A. Classic Drop Cap (First Letter styling)
* **How it works:** The compiler automatically detects the first letter of the first paragraph in every chapter and transforms it into an elegant, oversized drop cap. 
* **Note:** This only applies to the very first text segment of a chapter (it will intelligently skip over starting illustrations).

### B. Smart Indentation Removal
* **How it works:** In professional publishing, the first paragraph of a chapter or immediately following a scene break/image does not have a paragraph indent. NarrativeOS automatically applies a `no-indent` class to these paragraphs for a clean, professional look.

---

## 2. Advanced Workflow & Image Support

The newest version of NarrativeOS includes powerful automation tools for managing illustrations seamlessly.

### A. Intelligent Image Autocomplete
* **Usage:** Inserting illustrations from your local `images/` folder has never been easier.
* **How to use:** While in the Markdown Editor, simply type `![image](` or `![](`.
* **What happens:** An elegant, floating glass gallery will appear at the bottom of the editor showing thumbnails of all images in your current volume. Clicking a thumbnail instantly inserts the correct filename and closes the bracket for you.

### B. Auto-Download & WebP Compression
* **Usage:** You don't need to manually download images from the internet anymore.
* **How to use:** Paste any direct image URL into your standard markdown image tag.
  ```markdown
  ![Illustration](https://example.com/character_art.jpg)
  ```
* **What happens:** When you click "Compile EPUB", the builder will:
  1. Securely download the image from the URL.
  2. Automatically convert it to a highly-optimized `.webp` file.
  3. Automatically compress it to hit the target file size (e.g., under 1.5MB).
  4. **Rewrite your original `.md` file** to safely replace the URL with the new local file: `![Illustration](character_art.webp)`.

### C. Full-Page Image Isolation
* **Usage:** Illustrations placed between paragraphs are automatically split into their own dedicated, full-page XHTML files in the EPUB.
* **How to write:** Use the standard Markdown image tag. *(Note: The legacy `(image) [images/...]` syntax is still supported for older volumes).*
  ```markdown
  The monster roared, shattering the glass.

  ![Monster Illustration](monster.webp)

  I drew my sword and braced for impact.
  ```
* **Result:** The text before the image ends the previous page. The image gets a dedicated full page. The text after the image begins on a new page, automatically styled with a `no-indent` first paragraph.

---

## 3. Custom Publishing Tags (Light Novel Elements)

We have built custom syntax specifically tailored for Light Novels, LitRPGs, and Web Novels.

### A. Scene Breaks (Time/POV Skips)
* **Usage:** Creates a visual break for time skips or changing character perspectives.
* **How to write:** Type `***` or `---` on an empty line. Alternatively, you can use specialized symbols like `❖ ❖ ❖`.
  ```markdown
  And with that, the day came to an end.

  ***

  The morning sun pierced through the curtains...
  ```
* **Result:** The symbols are converted into an elegant, centered, and widely-spaced grey symbol `❖ ❖ ❖` with proper margins.

### B. Character Thought Box (Monologues)
* **Usage:** Distinguishes internal thoughts from spoken dialogue.
* **How to write (Block Box):** Start a new line with `(thought)`.
  ```markdown
  (thought) If I answer him now, he'll definitely get suspicious...
  ```
  *Result:* The text is wrapped in a transparent grey box with a thick left border and rounded corners.
* **How to write (Inline):** Place `(thought) [text]` inside a paragraph.
  ```markdown
  The character glared at me. (thought) [Why is he looking at me like that?] I wondered.
  ```
  *Result:* The bracketed text becomes dark grey, italicized text blending smoothly into the paragraph.

### C. Character Stats Box
* **Usage:** Perfect for LitRPG status screens, displaying character sheets, or fantasy letters.
* **How to write:** Wrap your text with `[stats]` and `[/stats]`. Markdown inside the box is fully supported.
  ```markdown
  [stats]
  **CHARACTER STATUS**
  * **Name**: Kanata
  * **Level**: 99
  * **Class**: Sage
  [/stats]
  ```
* **Result:** Renders as a premium UI card with a light background, elegant thick left border, rounded corners, and a modern sans-serif font.

### D. Game UI Notification Window
* **Usage:** Simulates floating system notifications or retro game popups.
* **How to write:** Wrap the text with `[UI]` and `[/UI]`. *(Note: Ensure you use the closing slash `/UI` at the end!)*
  ```markdown
  [UI]
  ▶ NEW SKILL UNLOCKED
  Skill: [Blessing of Death]
  Mana Cost: 0
  [/UI]
  ```
* **Result:** Renders as a striking dark mode box with a glowing neon border, using the retro **VT323** pixel font, bold white text, and a cyberpunk aesthetic. Line breaks are preserved automatically.

---

## 4. Standard Markdown Text Formatting

NarrativeOS fully supports all standard Markdown formatting for writing.

* **Bold**: `**bold text**` ➔ **bold text**
* **Italic**: `*italic text*` ➔ *italic text*
* **Bold & Italic**: `***bold & italic***` ➔ ***bold & italic***
* **Blockquote**: Use `>` at the start of a line.
  ```markdown
  > "A great teacher guides his students through the dark."
  ```
* **Tables**:
  ```markdown
  | Skill | Mana Cost | Duration |
  | :--- | :---: | :---: |
  | Hellflame | +150 | 5 Minutes |
  | Marionette| +200 | Instant |
  ```

---

*Tip: Use this guide as a template to test styles by clicking the "Preview" toggle in the editor!*
