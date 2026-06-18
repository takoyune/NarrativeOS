# NarrativeOS — Next-Gen Upgrade Roadmap

A curated list of meaningful upgrades that would take NarrativeOS from a great local tool to an absolutely phenomenal one. Ordered roughly by impact vs. effort.

---

## 🔥 HIGH IMPACT — Core UX Wins

### 1. Live Word Count & Reading Time Estimator
> **Why:** Right now the editor only shows character count. Showing **Word Count**, **Estimated Pages**, and **Reading Time (e.g., "~18 min read")** in the editor footer would make it feel like a professional writing tool (like Scrivener or Notion). It's also extremely useful for Light Novel authors who need to hit chapter length targets.

### 2. Chapter List with Drag-to-Reorder
> **Why:** Currently, files are just a flat dropdown. A proper **visual chapter list in the sidebar** (with drag-and-drop reordering and renaming inline) would be a massive workflow upgrade. Authors could reorder chapters without touching file names. This is the single biggest workflow pain point in any writing tool.

### 3. Full-Text Search Across All Files
> **Why:** With 10+ volumes and 100+ chapters, it's nearly impossible to find a specific scene or character dialogue. A **Ctrl+Shift+F global search** that searches across all `.md` files in the library and shows snippet previews (like VS Code's search sidebar) would be an incredible power-user feature.

### 4. Auto-Save with Restore (Crash Protection)
> **Why:** The unsaved changes modal is great, but a **30-second auto-save to a local draft** (not the real file) would protect against browser crashes and accidental closes. A small "Draft saved X seconds ago" indicator would give writers total peace of mind. This is standard in every professional writing tool.

### 5. EPUB Preview in a Side Pane
> **Why:** Right now you have to fully compile the EPUB, then open it in Calibre or an e-reader to see the final result. An **embedded EPUB-style preview** (applying the actual CSS — drop cap, font size, line height, indents) in a right pane would create an instant feedback loop. "What you see is what you get."

---

## 🚀 HIGH IMPACT — Power Features

### 6. Writing Statistics & Progress Dashboard
> **Why:** The Overview panel shows total counts but no **progress tracking**. A chart showing "words written this week", a progress bar per volume (e.g., "12 of 20 chapters translated"), and a daily writing streak would add a huge motivational layer. This turns the app from a file manager into a proper writing companion.

### 7. Chapter Notes / Sticky Sidebar
> **Why:** Authors constantly need to jot down "continuity notes" (e.g., "Character A has blue eyes in Ch3 but I changed it to green in Ch7"). A **per-chapter sticky note panel** that saves alongside the `.md` file would be incredibly valuable. It keeps all research and editorial notes in the same place as the content.

### 8. Bulk Chapter Scraper with Queue
> **Why:** Right now scraping is one-at-a-time. A **queue-based bulk scraper** where you paste a list of chapter URLs and it scrapes them automatically (with a delay to avoid rate-limiting) would be a massive time saver. Progress shown as a real-time queue with done/failed status per URL.

### 9. Find & Replace with Regex Support
> **Why:** The current Find & Replace is basic. Adding **case sensitivity toggle**, **regex mode** (so you can find patterns like `*text*` and replace with `**text**`), and a **replace-in-all-files** option would make bulk editing entire volumes fast and safe.

### 10. Image Alt-Text & Caption Editor
> **Why:** Currently images are just dropped in. Proper EPUB accessibility and formatting requires **alt text** and optionally **caption text**. A small inline editor in the Images panel to set these per image (saved as metadata) would improve EPUB quality significantly.

---

## 🎨 MEDIUM IMPACT — Polish & UX

### 11. Keyboard Shortcut Cheat Sheet (Modal)
> **Why:** Power users love keyboard shortcuts, but they have to discover them by accident. A `?` button or `Ctrl+/` shortcut that opens a **beautiful shortcuts reference modal** (like GitHub's shortcut modal) would make the app feel incredibly professional and encourage users to get faster.

### 12. Dark/Light Mode Toggle
> **Why:** The app is exclusively dark mode right now. Some users prefer light mode when working in bright environments. Adding a simple **system-aware auto mode + manual toggle** (stored in Settings) would massively broaden accessibility.

### 13. Breadcrumb as a Navigation History
> **Why:** The top breadcrumb currently just shows "Novel / Volume". It could instead be **interactive and show the full navigation trail** — clicking "Novel" would jump you back to the overview filtered by that novel. This creates a much more "IDE-like" mental model.

### 14. Collapsible Sidebar Sections
> **Why:** As the Library grows to 20+ novels, the sidebar tree becomes massive. **Collapsible groups with memory** (it remembers which novels are expanded between sessions) would help manage cognitive load.

### 15. Image Size Warning on Upload
> **Why:** Large images silently slow down EPUB generation. Showing an **inline warning** (e.g., "⚠️ This image is 8MB and may need compression") with a one-click compress button right in the Images panel would proactively prevent build issues.

---

## 🛡️ QUALITY OF LIFE — Stability & Safety

### 16. File Backup / Version History
> **Why:** A writer could accidentally delete an entire chapter with no way to recover it. A simple **"last 5 saves" version history** (stored as `.bak` files) with a restore UI in the editor would provide crucial safety. "Undo" for your whole file.

### 17. Build History Log Panel
> **Why:** After building EPUBs, the log disappears. Keeping a **persistent build history** (timestamp, novel/volume, success/fail, output path) in a dedicated log view would help diagnose recurring issues and track which volumes have been published.

### 18. Connection Status Indicator
> **Why:** If the Python server crashes or loses connection, the app just silently fails. A **small server status dot** in the top bar (green = connected, red = offline) that polls `/api/health` every 5 seconds would make failure states immediately obvious.

---

## 💡 CREATIVE — Unique Differentiators

### 19. AI-Powered Translation Quality Check
> **Why:** Since this is used for translated Light Novels, an optional "quality check" that could flag **untranslated Japanese/Indonesian phrases**, inconsistent character name spellings, or broken dialogue formatting (missing closing quotes) would save enormous time in editing.

### 20. Character & Term Glossary Manager
> **Why:** A dedicated panel where you can maintain a **glossary of characters, locations, and world-building terms** per novel. This could later power the AI quality check to ensure consistency across all chapters (e.g., "Protagonist name is 'Ryou' not 'Ryuu'").
