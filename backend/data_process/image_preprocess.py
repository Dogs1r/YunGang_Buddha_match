import os
import shutil
from PIL import Image

def preprocess_buddha_image(src_path, dest_dir):
    """
    Preprocess a single image: resize and save to destination directory.
    
    Args:
        src_path: Path to source image
        dest_dir: Directory to save processed image
        
    Returns:
        str: Path to processed image, or None if failed
    """
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
        
    filename = os.path.basename(src_path)
    dest_path = os.path.join(dest_dir, filename)
    
    try:
        # Basic validation: check if it's an image
        with Image.open(src_path) as img:
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize if too large (optional, for performance)
            max_size = (1024, 1024)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            img.save(dest_path, quality=95)
            return dest_path
    except Exception as e:
        print(f"Error processing {src_path}: {e}")
        return None

def batch_preprocess_buddha_images(src_dir, dest_dir):
    """
    Batch preprocess images from source directory to destination directory.
    
    Args:
        src_dir: Source directory containing images
        dest_dir: Destination directory
    """
    if not os.path.exists(src_dir):
        print(f"Source directory {src_dir} does not exist.")
        return

    count = 0
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                src_path = os.path.join(root, file)
                if preprocess_buddha_image(src_path, dest_dir):
                    count += 1
    print(f"Processed {count} images.")
