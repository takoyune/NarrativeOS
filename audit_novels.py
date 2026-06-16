import os
import re
import sys
import argparse

def parse_metadata(content):
    metadata = {}
    fields = [
        ("Title Japan", r"Title Japan\s*:\s*\[(.*?)\]"),
        ("Title Indonesia", r"Title Indonesia\s*:\s*\[(.*?)\]"),
        ("Title Inggris", r"Title Inggris\s*:\s*\[(.*?)\]"),
        ("Title Romanji", r"Title Romanji\s*:\s*\[(.*?)\]"),
        ("Author", r"Author\s*:\s*\[(.*?)\]"),
        ("Artist", r"Artist\s*:\s*\[(.*?)\]"),
        ("Genres", r"Genres\s*:\s*\[(.*?)\]"),
        ("Translator", r"Translator\s*:\s*\[(.*?)\]"),
        ("EPUB Compiler", r"EPUB Compiler\s*:\s*\[(.*?)\]"),
        ("Cover", r"Cover\s*:\s*\[(.*?)\]")
    ]
    for name, pattern in fields:
        match = re.search(pattern, content, flags=re.IGNORECASE)
        metadata[name] = match.group(1).strip() if match else None
    return metadata

def check_file_case_insensitive(directory, filename):
    """Checks if a file exists in the directory case-insensitively.
    Returns (exists, actual_filename)"""
    target_lower = filename.lower()
    try:
        files = os.listdir(directory)
    except FileNotFoundError:
        return False, None
        
    for f in files:
        if f.lower() == target_lower:
            return True, f
    return False, None

def find_image_in_folders(base_dir, img_rel_path):
    """Try to find an image in standard folders: images, Ilustrasi, Ilustarasi.
    Returns (found, actual_path)"""
    img_name = os.path.basename(img_rel_path)
    folders = ["images", "Ilustrasi", "Ilustarasi"]
    
    # First try direct path
    direct_path = os.path.join(base_dir, img_rel_path)
    if os.path.exists(direct_path):
        return True, img_rel_path
        
    # Try case-insensitive direct path
    dir_part = os.path.dirname(img_rel_path)
    exists, actual_name = check_file_case_insensitive(os.path.join(base_dir, dir_part) if dir_part else base_dir, img_name)
    if exists:
        return True, os.path.join(dir_part, actual_name) if dir_part else actual_name
        
    # Try looking in alternative folders
    for folder in folders:
        folder_path = os.path.join(base_dir, folder)
        exists, actual_name = check_file_case_insensitive(folder_path, img_name)
        if exists:
            return True, os.path.join(folder, actual_name)
            
    return False, None

def audit_folder(base_dir):
    errors = []
    warnings = []
    info = []
    
    main_md_path = os.path.join(base_dir, "main.md")
    if not os.path.exists(main_md_path):
        errors.append("main.md not found in folder.")
        return errors, warnings, info
        
    with open(main_md_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # 1. Metadata check
    metadata = parse_metadata(content)
    required_fields = ["Title Japan", "Title Indonesia", "Author", "Artist", "Genres", "Translator", "EPUB Compiler", "Cover"]
    for field in required_fields:
        if not metadata[field]:
            if field in ["Title Japan", "Title Indonesia", "Author", "Cover"]:
                errors.append(f"Missing critical metadata field: '{field}'")
            else:
                warnings.append(f"Missing recommended metadata field: '{field}'")
                
    # Check Cover Image
    cover_path = metadata.get("Cover")
    if cover_path:
        if cover_path.lower().startswith(('http://', 'https://')):
            info.append(f"Cover is an online image URL: {cover_path}")
        else:
            found, actual_cover = find_image_in_folders(base_dir, cover_path)
            if not found:
                errors.append(f"Cover image file '{cover_path}' not found.")
            elif actual_cover != cover_path:
                warnings.append(f"Cover path case mismatch or location difference: main.md says '{cover_path}', actual file is '{actual_cover}'")
                
    # 2. Table of Contents check
    toc_block_match = re.search(r"Table of Content\s*\[(.*?)\n\s*\]", content, flags=re.DOTALL | re.IGNORECASE)
    if not toc_block_match:
        errors.append("Table of Content block not found in main.md.")
        return errors, warnings, info
        
    toc_block = toc_block_match.group(1)
    raw_toc_items = re.findall(r"\[(.*?)\]", toc_block)
    toc_items = [item.strip() for item in raw_toc_items if item.strip()]
    
    if not toc_items:
        errors.append("Table of Content is empty.")
        
    inline_img_pattern = re.compile(r"\(image\)\s*\[(?:.*?[\/\\])?([^\/\]\\ ]+\.(?:webp|jpg|jpeg|png))\]", re.IGNORECASE)
    online_img_pattern = re.compile(r"!\[(.*?)\]\((https?://[^\)]+)\)", re.IGNORECASE)
    
    for item in toc_items:
        # Cover item
        cover_match = re.match(r"^Cover\s*\((.*?)\)$", item, flags=re.IGNORECASE)
        if cover_match:
            c_path = cover_match.group(1).strip()
            if c_path.lower().startswith(('http://', 'https://')):
                pass
            else:
                found, _ = find_image_in_folders(base_dir, c_path)
                if not found:
                    errors.append(f"TOC Cover image '{c_path}' not found.")
            continue
            
        # Inline images folder / illustration list
        illus_match = re.match(r"^(?:Ilustra(?:s|a)i|images)(?:\(folder\))?\((.*?)\)$", item, flags=re.IGNORECASE)
        if illus_match:
            folder_images = [img.strip() for img in illus_match.group(1).split(',') if img.strip()]
            for img in folder_images:
                found, _ = find_image_in_folders(base_dir, img)
                if not found:
                    errors.append(f"TOC Illustration image '{img}' not found.")
            continue
            
        # Table of Contents & About
        if item.lower() in ['table of contents', 'about']:
            continue
            
        # Chapter / file item
        chapter_match = re.match(r"^(.*?\.md)\s*\(file\)$", item, flags=re.IGNORECASE)
        if chapter_match:
            filename = chapter_match.group(1).strip()
            # Normalize common typo
            filename = filename.replace("Boonus Chapter.md", "Bonus Chapter.md")
            
            exists, actual_filename = check_file_case_insensitive(base_dir, filename)
            if not exists:
                errors.append(f"Chapter file '{filename}' listed in TOC but not found physically.")
            else:
                if actual_filename != filename:
                    warnings.append(f"Chapter file case mismatch: TOC lists '{filename}', actual file is '{actual_filename}'")
                
                # Check contents of the chapter file for images or syntax errors
                ch_path = os.path.join(base_dir, actual_filename)
                try:
                    with open(ch_path, 'r', encoding='utf-8') as cf:
                        ch_text = cf.read()
                        
                    # Check for inline images referenced in markdown
                    img_matches = inline_img_pattern.findall(ch_text)
                    for img in img_matches:
                        found, _ = find_image_in_folders(base_dir, img)
                        if not found:
                            errors.append(f"In {actual_filename}: referenced image '{img}' not found.")
                            
                    # Check for online images that will need downloading
                    online_matches = online_img_pattern.findall(ch_text)
                    if online_matches:
                        info.append(f"In {actual_filename}: found {len(online_matches)} online image(s) to download.")
                        
                except Exception as e:
                    errors.append(f"Could not read chapter file '{actual_filename}': {e}")
            continue
            
        # Unrecognized item
        warnings.append(f"Unrecognized TOC item structure: '{item}'")
        
    return errors, warnings, info

# Reconfigure stdout to use utf-8 to avoid UnicodeEncodeErrors on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    parser = argparse.ArgumentParser(description="Novel EPUB Audit Tool")
    parser.add_argument("folder", nargs="?", default=None, help="Specific novel folder to audit")
    args = parser.parse_args()
    
    workspace_dir = os.path.dirname(os.path.abspath(__file__))
    
    if args.folder:
        target_dir = args.folder
        if not os.path.isabs(target_dir):
            target_dir = os.path.abspath(os.path.join(workspace_dir, target_dir))
            
        if not os.path.exists(target_dir):
            print(f"Error: Directory does not exist: {target_dir}")
            sys.exit(1)
            
        novel_folders = [target_dir]
    else:
        # Scan workspace for folders containing main.md
        novel_folders = []
        for root, dirs, files in os.walk(workspace_dir):
            if "main.md" in files and root != workspace_dir:
                novel_folders.append(root)
                
    if not novel_folders:
        print("No novel folders with main.md found.")
        sys.exit(0)
        
    novel_folders.sort()
    
    print("=" * 80)
    print(f"EPUB NOVEL AUDIT REPORT")
    print(f"Scanning folder(s) in: {workspace_dir}")
    print("=" * 80)
    
    total_errors = 0
    total_warnings = 0
    
    for folder in novel_folders:
        rel_folder = os.path.relpath(folder, workspace_dir)
        print(f"\n[FOLDER] {rel_folder}")
        
        errors, warnings, info = audit_folder(folder)
        
        if not errors and not warnings:
            print("  [PASS] No issues found.")
        else:
            for inf in info:
                print(f"  [INFO] {inf}")
            for warn in warnings:
                print(f"  [WARN] {warn}")
                total_warnings += 1
            for err in errors:
                print(f"  [ERROR] {err}")
                total_errors += 1
                
    print("\n" + "=" * 80)
    print(f"AUDIT SUMMARY: Found {total_errors} error(s) and {total_warnings} warning(s) across {len(novel_folders)} novel folder(s).")
    print("=" * 80)
    
    if total_errors > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
