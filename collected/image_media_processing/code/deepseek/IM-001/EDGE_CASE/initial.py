import os
from PIL import Image

def batch_resize(input_dir, output_dir, target_size):
    """
    Resizes every PNG/JPEG image in input_dir to target_size and saves results to output_dir.
    
    Args:
        input_dir (str): Path to the directory containing source images
        output_dir (str): Path to the directory where resized images will be saved
        target_size (tuple): Desired output size as (width, height)
    
    Returns:
        int: Number of images successfully processed
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Supported image extensions
    supported_extensions = {'.png', '.jpg', '.jpeg'}
    
    processed_count = 0
    
    # Iterate through all files in the input directory
    for filename in os.listdir(input_dir):
        # Check if file has a supported extension
        file_ext = os.path.splitext(filename)[1].lower()
        
        if file_ext in supported_extensions:
            try:
                # Construct full file paths
                input_path = os.path.join(input_dir, filename)
                output_path = os.path.join(output_dir, filename)
                
                # Open the image
                with Image.open(input_path) as img:
                    # Convert to RGB if necessary (for PNG with alpha channel)
                    if img.mode in ('RGBA', 'LA', 'P'):
                        # Create a white background
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        # Paste the image on the background if it has alpha
                        if img.mode == 'P':
                            img = img.convert('RGBA')
                        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                        img = background
                    elif img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    # Resize the image using LANCZOS (high quality)
                    resized_img = img.resize(target_size, Image.Resampling.LANCZOS)
                    
                    # Save the resized image
                    # Preserve original format
                    if file_ext == '.png':
                        resized_img.save(output_path, 'PNG', optimize=True)
                    else:  # JPEG
                        resized_img.save(output_path, 'JPEG', quality=85, optimize=True)
                    
                    processed_count += 1
                    
            except Exception as e:
                print(f"Error processing {filename}: {e}")
                continue
    
    return processed_count