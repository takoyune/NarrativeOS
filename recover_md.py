import zipfile, os, re

epub_path = r'd:\code iwan\EPUB\Aku_Hanya_Pendeta_Figuran_Vol_1.epub'
out_dir = r'd:\code iwan\EPUB\Aku Hanya Pendeta Figuran Vol 1'

md_files = [
    'Prolog.md', 'Chapter 1.md', 'Chapter 2.md', 'Chapter 3.md',
    'Chapter 4.md', 'Chapter 5.md', 'Chapter 6.md', 'Chapter 7.md',
    'Epilog.md', 'Postscript.md'
]

with zipfile.ZipFile(epub_path, 'r') as z:
    for i, md_file in enumerate(md_files):
        chap_idx = i + 1
        part = 1
        recovered_lines = []
        
        while True:
            xhtml_name = f'OEBPS/xhtml/chapter-{chap_idx:02d}-{part:02d}.xhtml'
            if xhtml_name not in z.namelist():
                break
                
            content = z.read(xhtml_name).decode('utf-8')
            
            # Extract body
            body_match = re.search(r'<body>(.*?)</body>', content, re.DOTALL)
            if body_match:
                body = body_match.group(1)
                
                if part == 1:
                    title = re.search(r'<h2>(.*?)</h2>', body)
                    if title:
                        recovered_lines.append(f'# {title.group(1)}')
                
                # Replace full-page images with markdown image syntax
                body = re.sub(r'<div class="full-page-image">.*?<img src="\.\./images/(.*?)".*?>.*?</div>', r'\n\n(image) [images/\1]\n\n', body, flags=re.DOTALL)
                
                # Extract paragraph content or raw text containing our injected image syntax
                # We will split body by <p> tags
                chunks = re.split(r'(</?p.*?>)', body)
                
                in_p = False
                current_p = ""
                for chunk in chunks:
                    if chunk.startswith('<p'):
                        in_p = True
                        current_p = ""
                    elif chunk.startswith('</p>'):
                        in_p = False
                        
                        p = current_p
                        p = re.sub(r'<strong.*?>(.*?)</strong>', r'**\1**', p, flags=re.DOTALL)
                        p = re.sub(r'<b.*?>(.*?)</b>', r'**\1**', p, flags=re.DOTALL)
                        p = re.sub(r'<em.*?>(.*?)</em>', r'*\1*', p, flags=re.DOTALL)
                        p = re.sub(r'<i.*?>(.*?)</i>', r'*\1*', p, flags=re.DOTALL)
                        p = re.sub(r'<.*?>', '', p) # remove spans etc
                        p = p.replace('&nbsp;', ' ').replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
                        p = p.strip()
                        if p:
                            recovered_lines.append(p)
                    elif in_p:
                        current_p += chunk
                    elif '(image)' in chunk:
                        # Append image chunks that were outside <p> tags
                        for img in re.findall(r'\(image\) \[images/.*?\]', chunk):
                            recovered_lines.append(img)
            part += 1
            
        with open(os.path.join(out_dir, md_file), 'w', encoding='utf-8') as f:
            f.write('\n\n'.join(recovered_lines))
            
print('Recovery completed! Better version.')
