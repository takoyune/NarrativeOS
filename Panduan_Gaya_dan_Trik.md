# Panduan Gaya & Trik Pemformatan EPUB (Master Cheatsheet)

File ini adalah panduan master referensi sekaligus template uji coba untuk semua simbol, gaya teks, dan "trik" khusus yang didukung oleh sistem pembuat EPUB universal kita. Anda dapat menyimpan file ini di folder utama `d:\code iwan\EPUB\` sebagai rujukan umum saat menulis novel apa pun di masa mendatang.

---

## 1. Trik Khusus Penerbitan (Custom Tricks)

Trik-trik khusus ini diproses secara otomatis oleh sistem build untuk memberikan tampilan visual layaknya *light novel* premium.

### A. Drop Cap (Huruf Awal Bab Bergaya Klasik)
*   **Cara kerja**: **Otomatis!** Anda tidak perlu mengetik simbol khusus apa pun. Script akan otomatis mendeteksi huruf pertama di awal bab dan menjadikannya besar serta bergaya klasik.
*   **Contoh tampilan**:
    <p><span class="dropcap">H</span>ari itu adalah awal dari petualangan baru...</p>

---

### B. Pembatas Adegan (Scene Break)
*   **Guna**: Digunakan untuk transisi waktu (time skip) atau perpindahan sudut pandang (POV shift).
*   **Cara tulis**: Ketik `***` atau `---` di baris baru yang kosong (pastikan ada baris kosong di atas dan di bawahnya).
*   **Markdown**:
    ```markdown
    Ini adalah akhir adegan pertama.
    
    ***
    
    Ini adalah awal adegan berikutnya setelah time skip.
    ```
*   **Hasil di EPUB**: Otomatis diubah menjadi simbol elegan `❖ ❖ ❖` berwarna abu-abu yang berada pas di tengah halaman dengan jarak vertikal yang rapi.

---

### C. Suara Batin / Kotak Pikiran Karakter (Thought Teks & Box)
*   **Guna**: Membuat gaya khusus untuk gumaman batin atau monolog dalam hati agar lebih *immersive*. Ada dua mode: **Kotak Suara Hati** (Thought Box) dan **Teks Menyatu** (Inline).
*   **Cara tulis (Kotak Monolog)**: Tulis `(thought)` di baris baru, tanpa tanda kurung siku (atau dengan kurung siku).
    ```markdown
    (thought) Gawat... kalau aku menjawabnya sekarang, dia pasti akan curiga! Ini tidak bisa dibiarkan begitu saja.
    ```
*   **Cara tulis (Teks Menyatu)**: Sisipkan `(thought) [teks pikiran]` di tengah paragraf biasa.
    ```markdown
    Karakter itu menatapku tajam. (thought) [Kenapa dia menatapku seperti itu?] pikirku dalam hati.
    ```
*   **Hasil di EPUB**:
    *   Jika memakai cara pertama, teks akan dibungkus **kotak abu-abu transparan bergaris kiri** yang elegan dengan ujung agak membulat.
    *   Jika memakai cara kedua, ia hanya akan menjadi teks miring (`italic`) berwarna abu-abu gelap yang menyatu dengan kalimat lainnya.

---

### D. Kotak UI / Status Game / Statistik Karakter (Stats Box)
*   **Guna**: Membuat kotak status khusus, surat, atau kotak pesan antarmuka game (RPG/Fantasy).
*   **Cara tulis**: Bungkus teks dengan tag `[stats]` di awal dan `[/stats]` di akhir.
*   **Markdown**:
    ```markdown
    [stats]
    **STATUS KARAKTER**
    *   **Nama**: Kanata Allure
    *   **Level**: 99
    *   **Pekerjaan**: Instruktur Jenius
    *   **Kelemahan**: Terlalu berengsek
    [/stats]
    ```
*   **Hasil di EPUB**: Di-render sebagai kotak UI premium dengan latar belakang abu-abu terang, border kiri hitam tebal yang elegan, sudut membulat, dan font sans-serif modern.

---

### E. Kotak Notifikasi Game / System Window (Game UI Box)
*   **Guna**: Membuat kotak notifikasi sistem game, status window, atau popup skill dengan gaya retro/pixel yang keren.
*   **Cara tulis**: Bungkus teks dengan tag `[UI]` di awal dan `[UI]` di akhir.
*   **Markdown**:
    ```markdown
    [UI]
    Kekuatan terbuka.
    Ability:
    【Blessing of Death】
    Jumlah Total: 3100
    [UI]
    ```
*   **Hasil di EPUB**: Di-render sebagai kotak gelap (dark mode) dengan border biru bercahaya, font pixel retro **VT323**, teks tebal putih, dan efek glow halus. Setiap baris baru otomatis turun ke bawah.

---

## 2. Pemformatan Teks Standar Markdown

Sistem kita mendukung pemformatan teks Markdown standar untuk mengatur gaya font tulisan:

*   **Tebal (Bold)**:
    *   Cara tulis: `**teks tebal**` atau `__teks tebal__`
    *   Contoh: **Ini adalah teks tebal untuk penekanan kuat.**
*   **Miring (Italic)**:
    *   Cara tulis: `*teks miring*` atau `_teks miring_`
    *   Contoh: *Ini adalah teks miring untuk penekanan atau bahasa asing.*
*   **Tebal & Miring (Bold Italic)**:
    *   Cara tulis: `***teks tebal miring***`
    *   Contoh: ***Ini adalah teks tebal sekaligus miring.***
*   **Kutipan Blok (Blockquote)**:
    *   Cara tulis: Gunakan tanda `>` di awal baris.
    *   Markdown:
        ```markdown
        > "Seorang guru yang hebat tidak hanya mengajar, tetapi juga membimbing muridnya melewati kegelapan."
        ```
    *   Contoh hasil:
        > "Seorang guru yang hebat tidak hanya mengajar, tetapi juga membimbing muridnya melewati kegelapan."

---

## 3. Penyisipan Gambar (Ilustrasi)

*   **Halaman Gambar Isolasi Penuh (Inline Image Split)**:
    *   **Guna**: Menyisipkan ilustrasi di tengah bab yang otomatis akan dipisahkan menjadi satu halaman penuh tersendiri tanpa tercampur teks.
    *   **Cara tulis**: `(image) [images/nama_file.webp]` atau `(image) [Ilustrasi/nama_file.webp]`
    *   **Markdown**:
        ```markdown
        Setelah pertarungan sengit itu selesai, gadis itu tersenyum dengan sangat cerah ke arahku.
        
        (image) [images/04.webp]
        
        Keesokan harinya, kami bersiap untuk kembali...
        ```
    *   **Hasil di EPUB**: Gambar `04.webp` dijamin berdiri sendiri di satu halaman penuh. Teks sebelum gambar berada di halaman sebelumnya, dan teks sesudah gambar ("Keesokan harinya...") berada di halaman sesudahnya dengan format paragraf pertama otomatis tanpa inden (`no-indent`).

---

## 4. Tabel Informasi (Tables)

Sistem kita mendukung pembuatan tabel Markdown standar yang akan otomatis diubah menjadi tabel bergaya modern dan rapi.

*   **Markdown**:
    ```markdown
    | Parameter | Efek Mana | Durasi |
    | :--- | :---: | :---: |
    | **Hellflame** | +150 | 5 Menit |
    | **Serpent Move** | +80 | Aktif |
    | **Marionette** | +200 | Instan |
    ```
*   **Contoh hasil**:

| Parameter | Efek Mana | Durasi |
| :--- | :---: | :---: |
| **Hellflame** | +150 | 5 Menit |
| **Serpent Move** | +80 | Aktif |
| **Marionette** | +200 | Instan |

---

*Gunakan file ini sebagai rujukan umum saat menulis novel baru di masa depan!*
