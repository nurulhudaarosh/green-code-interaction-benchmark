import os
from PIL import Image

def batch_resize(input_dir, output_dir, target_size):
    """
    Resizes every PNG/JPEG image in input_dir to target_size and saves to output_dir.
    
    Args:
        input_dir (str): Path to directory containing input images
        output_dir (str): Path to directory where resized images will be saved
        target_size (tuple): Desired size as (width, height)
    
    Returns:
        int: Number of images successfully processed
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Supported image extensions
    extensions = {'.png', '.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG'}
    
    processed_count = 0
    
    # Iterate through all files in input directory
    for filename in os.listdir(input_dir):
        # Check if file has a supported image extension
        if any(filename.endswith(ext) for ext in extensions):
            input_path = os.path.join(input_dir, filename)
            
            try:
                # Open the image
                with Image.open(input_path) as img:
                    # Convert to RGB if necessary (for PNG with alpha)
                    if img.mode in ('RGBA', 'LA', 'P'):
                        img = img.convert('RGB')
                    
                    # Resize the image using LANCZOS (high quality)
                    resized_img = img.resize(target_size, Image.Resampling.LANCZOS)
                    
                    # Construct output path (preserve original filename)
                    output_path = os.path.join(output_dir, filename)
                    
                    # Save the resized image
                    # Determine format from extension
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in ('.jpg', '.jpeg'):
                        resized_img.save(output_path, 'JPEG', quality=85)
                    else:  # PNG
                        resized_img.save(output_path, 'PNG')
                    
                    processed_count += 1
                    
            except Exception as e:
                print(f"Error processing {filename}: {e}")
                continue
    
    return processed_count