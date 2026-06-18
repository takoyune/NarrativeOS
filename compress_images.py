import os
from PIL import Image

def compress_image(filepath, max_mb=2.0):
    max_bytes = max_mb * 1024 * 1024
    original_size = os.path.getsize(filepath)
    if original_size <= max_bytes:
        return False
        
    try:
        with Image.open(filepath) as img:
            original_format = img.format
            # Resize if dimensions are excessively large
            if img.width > 2000 or img.height > 2000:
                img.thumbnail((2000, 2000), Image.Resampling.LANCZOS)
                
            if filepath.lower().endswith('.png'):
                # Try saving with optimization first
                temp_path = filepath + ".tmp"
                img.save(temp_path, format="PNG", optimize=True)
                
                # If still too large, use adaptive palette (256 colors) for massive reduction
                if os.path.getsize(temp_path) > max_bytes:
                    img_quantized = img.convert('P', palette=Image.ADAPTIVE, colors=256)
                    img_quantized.save(temp_path, format="PNG", optimize=True)
                    
                os.replace(temp_path, filepath)
            else:
                img.save(filepath, optimize=True, quality=80)
                
        return True
    except Exception as e:
        print(f"Error compressing {filepath}: {e}")
        return False

folder = r'd:\code iwan\EPUB\Aku Hanya Pendeta Figuran Vol 1\images'
print("Scanning for large images...")
for file in os.listdir(folder):
    if file.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
        filepath = os.path.join(folder, file)
        size_mb = os.path.getsize(filepath) / (1024*1024)
        if size_mb > 2.0:
            print(f"Compressing {file} ({size_mb:.2f} MB)...")
            compressed = compress_image(filepath, 2.0)
            if compressed:
                new_size = os.path.getsize(filepath) / (1024*1024)
                print(f" -> Compressed to {new_size:.2f} MB")
