# EPUB Formatting Style & Tricks Guide (Master Cheatsheet)

This file is a master reference guide and test template for all the symbols, text styles, and custom "tricks" supported by our universal EPUB builder system. You can keep this file in the main folder as a general reference when formatting any novel in the future.

---

## 1. Custom Publishing Tricks

These custom tricks are automatically processed by the build system to provide a premium light novel visual experience.

### A. Drop Cap (Classic Chapter Opening Letter)
*   **How it works**: **Automatic!** You don't need to type any special symbols. The script will automatically detect the first letter at the beginning of a chapter and make it large and styled classically.
*   **Example appearance**: The first letter spans multiple lines, creating an elegant opening.

---

### B. Scene Break
*   **Usage**: Used for time skips or point-of-view (POV) shifts.
*   **How to write**: Type `***` or `---` on a new empty line (make sure there is an empty line above and below it).
*   **Markdown**:
    ```markdown
    This is the end of the first scene.
    
    ***
    
    This is the beginning of the next scene after a time skip.
    ```
*   **Result in EPUB**: Automatically converted into an elegant `❖ ❖ ❖` grey symbol centered on the page with neat vertical spacing.

---

### C. Inner Voice / Character Thought Box (Thought Text & Box)
*   **Usage**: Creates a special style for inner murmurs or monologues to make them more *immersive*. There are two modes: **Thought Box** and **Inline Text**.
*   **How to write (Monologue Box)**: Type `(thought)` on a new line, without square brackets (or with square brackets).
    ```markdown
    (thought) Oh no... if I answer him now, he'll definitely get suspicious! I can't let this go.
    ```
*   **How to write (Inline Text)**: Insert `(thought) [thought text]` in the middle of a regular paragraph.
    ```markdown
    The character glared at me sharply. (thought) [Why is he looking at me like that?] I thought to myself.
    ```
*   **Result in EPUB**:
    *   If using the first method, the text will be wrapped in an **elegant transparent grey box with a thick left border** and slightly rounded corners.
    *   If using the second method, it will simply become dark grey italicized text (`italic`) that blends in with the rest of the sentence.

---

### D. UI Box / Game Status / Character Stats (Stats Box)
*   **Usage**: Creates custom status boxes, letters, or game interface message boxes (RPG/Fantasy).
*   **How to write**: Wrap the text with the `[stats]` tag at the beginning and `[/stats]` at the end.
*   **Markdown**:
    ```markdown
    [stats]
    **CHARACTER STATUS**
    *   **Name**: Kanata Allure
    *   **Level**: 99
    *   **Job**: Genius Instructor
    *   **Weakness**: Too much of a jerk
    [/stats]
    ```
*   **Result in EPUB**: Rendered as a premium UI box with a light grey background, an elegant thick black left border, rounded corners, and a modern sans-serif font.

---

### E. Game Notification Box / System Window (Game UI Box)
*   **Usage**: Creates game system notification boxes, status windows, or skill popups with a cool retro/pixel style.
*   **How to write**: Wrap the text with the `[UI]` tag at the beginning and `[UI]` at the end.
*   **Markdown**:
    ```markdown
    [UI]
    Power unlocked.
    Ability:
    【Blessing of Death】
    Total Amount: 3100
    [UI]
    ```
*   **Result in EPUB**: Rendered as a dark mode box with a glowing blue border, **VT323** retro pixel font, bold white text, and a subtle glow effect. Every new line automatically drops down.

---

## 2. Standard Markdown Text Formatting

Our system supports standard Markdown text formatting to adjust writing font styles:

*   **Bold**:
    *   How to write: `**bold text**` or `__bold text__`
    *   Example: **This is bold text for strong emphasis.**
*   **Italic**:
    *   How to write: `*italic text*` or `_italic text_`
    *   Example: *This is italic text for emphasis or foreign languages.*
*   **Bold & Italic**:
    *   How to write: `***bold italic text***`
    *   Example: ***This is both bold and italic text.***
*   **Blockquote**:
    *   How to write: Use the `>` sign at the beginning of the line.
    *   Markdown:
        ```markdown
        > "A great teacher doesn't just teach, but guides his students through the darkness."
        ```

---

## 3. Image Insertion (Illustrations)

*   **Full Isolation Image Page (Inline Image Split)**:
    *   **Usage**: Inserts an illustration in the middle of a chapter which will automatically be separated into its own full page without being mixed with text.
    *   **How to write**: `(image) [images/filename.webp]` or `(image) [Illustrasi/filename.webp]`
    *   **Markdown**:
        ```markdown
        After the fierce battle was over, the girl smiled very brightly at me.
        
        (image) [images/04.webp]
        
        The next day, we prepared to return...
        ```
    *   **Result in EPUB**: The image `04.webp` is guaranteed to stand alone on one full page. The text before the image is on the previous page, and the text after the image is on the next page with the first paragraph automatically formatted without an indent (`no-indent`).

---

## 4. Information Tables

Our system supports standard Markdown table creation which will automatically be transformed into a neat, modern-style table.

*   **Markdown**:
    ```markdown
    | Parameter | Mana Effect | Duration |
    | :--- | :---: | :---: |
    | **Hellflame** | +150 | 5 Minutes |
    | **Serpent Move** | +80 | Active |
    | **Marionette** | +200 | Instant |
    ```

---

*Use this file as a general reference when writing new novels in the future!*
