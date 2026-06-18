import os

folder = r'd:\code iwan\EPUB\Aku Hanya Pendeta Figuran Vol 1'

titles = {
    'Prolog.md': '# Prolog: Turunnya Sang Saintess',
    'Chapter 1.md': '# Chapter 1: Aku Menemukan Sang Saintess',
    'Chapter 2.md': '# Chapter 2: Serangkaian Keajaiban Sang Saintess',
    'Chapter 3.md': '# Chapter 3: Aksi Sang Saintess, dan Krisis',
    'Chapter 4.md': '# Chapter 4: Kepergian Sang Saintess',
    'Chapter 5.md': '# Chapter 5: Akademi Tempat Sang Saintess Berada',
    'Chapter 6.md': '# Chapter 6: Urusan Cinta Si Pendeta Figuran',
    'Chapter 7.md': '# Chapter 7: Aku Akan Pulang ke Rumah!',
    'Epilog.md': '# Epilog: Sang Saintess Telah Kembali',
    'Postscript.md': '# Postscript'
}

for filename, title in titles.items():
    filepath = os.path.join(folder, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if not content.lstrip().startswith(title):
            content = title + '\n\n' + content.lstrip()
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Berhasil menambahkan judul ke {filename}")
        else:
            print(f"Judul sudah ada di {filename}")
